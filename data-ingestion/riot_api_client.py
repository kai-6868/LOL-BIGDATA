"""
Riot Games API Client
Official API wrapper with rate limiting and error handling
"""

import requests
import time
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, requests_per_second: int = 20, requests_per_2min: int = 100):
        self.rps = requests_per_second
        self.rpm2 = requests_per_2min
        self.last_request_time = 0
        self.request_count_2min = 0
        self.window_start = time.time()
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        current_time = time.time()
        
        # Check 2-minute window
        if current_time - self.window_start >= 120:
            self.request_count_2min = 0
            self.window_start = current_time
        
        if self.request_count_2min >= self.rpm2:
            sleep_time = 120 - (current_time - self.window_start)
            if sleep_time > 0:
                logger.warning(f"Rate limit reached. Sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)
                self.request_count_2min = 0
                self.window_start = time.time()
        
        # Check per-second limit
        time_since_last = current_time - self.last_request_time
        if time_since_last < 1.0 / self.rps:
            time.sleep(1.0 / self.rps - time_since_last)
        
        self.last_request_time = time.time()
        self.request_count_2min += 1


class RiotAPIClient:
    """Riot Games API Client with rate limiting"""
    
    # Regional routing
    REGIONS = {
        'na1': 'americas', 'br1': 'americas', 'la1': 'americas', 'la2': 'americas',
        'euw1': 'europe', 'eun1': 'europe', 'tr1': 'europe', 'ru': 'europe',
        'kr': 'asia', 'jp1': 'asia', 'oc1': 'asia', 'ph2': 'asia',
        'sg2': 'asia', 'th2': 'asia', 'tw2': 'asia', 'vn2': 'asia',
    }
    
    def __init__(self, api_key: str, region: str = 'na1'):
        self.api_key = api_key
        self.region = region.lower()
        self.rate_limiter = RateLimiter()
        
        # URLs
        self.platform_url = f'https://{self.region}.api.riotgames.com'
        regional_routing = self.REGIONS.get(self.region, 'americas')
        self.regional_url = f'https://{regional_routing}.api.riotgames.com'
        
        logger.info(f"Riot API Client initialized for region: {region}")
    
    def _make_request(self, url: str, retries: int = 3) -> Optional[Dict]:
        """Make rate-limited API request with retries"""
        for attempt in range(retries):
            try:
                self.rate_limiter.wait_if_needed()
                
                headers = {'X-Riot-Token': self.api_key}
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited. Retry after {retry_after}s")
                    time.sleep(retry_after)
                elif response.status_code == 404:
                    return None
                elif response.status_code == 403:
                    logger.error("Invalid API key or forbidden")
                    raise Exception("API key invalid")
                else:
                    logger.error(f"API error {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
        
        return None
    
    def get_challenger_players(self, region: str = None) -> List[Dict]:
        """Get Challenger league players"""
        if region:
            platform_url = f'https://{region}.api.riotgames.com'
        else:
            platform_url = self.platform_url
            
        url = f"{platform_url}/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5"
        data = self._make_request(url)
        return data.get('entries', []) if data else []
    
    def get_match_ids(self, puuid: str, count: int = 20, region: str = None) -> List[str]:
        """Get match IDs for a player"""
        if region:
            regional_routing = self.REGIONS.get(region, 'americas')
            regional_url = f'https://{regional_routing}.api.riotgames.com'
        else:
            regional_url = self.regional_url
            
        url = f"{regional_url}/lol/match/v5/matches/by-puuid/{puuid}/ids?count={count}"
        return self._make_request(url) or []
    
    def get_match_details(self, match_id: str, region: str = None) -> Optional[Dict]:
        """Get detailed match data"""
        if region:
            regional_routing = self.REGIONS.get(region, 'americas')
            regional_url = f'https://{regional_routing}.api.riotgames.com'
        else:
            regional_url = self.regional_url
            
        url = f"{regional_url}/lol/match/v5/matches/{match_id}"
        return self._make_request(url)
