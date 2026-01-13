"""
Unit Tests for LoL Match Generator
"""
import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.generator import MatchGenerator


class TestMatchGenerator:
    """Test suite for MatchGenerator class"""
    
    @patch('src.generator.KafkaProducer')
    def test_generator_initialization(self, mock_producer):
        """Test generator initializes correctly"""
        generator = MatchGenerator()
        
        assert generator is not None
        assert generator.config is not None
        assert len(generator.champions) > 0
        assert len(generator.positions) == 5
    
    @patch('src.generator.KafkaProducer')
    def test_generate_match_format(self, mock_producer):
        """Test generated match has correct format"""
        generator = MatchGenerator()
        match_data = generator.generate_match()
        
        # Check top-level structure
        assert 'metadata' in match_data
        assert 'info' in match_data
        
        # Check metadata
        assert 'matchId' in match_data['metadata']
        assert 'participants' in match_data['metadata']
        assert len(match_data['metadata']['participants']) == 10
        
        # Check info
        assert 'gameId' in match_data['info']
        assert 'participants' in match_data['info']
        assert len(match_data['info']['participants']) == 10
        assert 'teams' in match_data['info']
        assert len(match_data['info']['teams']) == 2
    
    @patch('src.generator.KafkaProducer')
    def test_participant_structure(self, mock_producer):
        """Test participant data structure"""
        generator = MatchGenerator()
        match_data = generator.generate_match()
        
        participant = match_data['info']['participants'][0]
        
        # Required fields
        required_fields = [
            'puuid', 'summonerId', 'summonerName', 'championName',
            'teamPosition', 'teamId', 'win', 'kills', 'deaths', 'assists',
            'goldEarned', 'totalDamageDealtToChampions', 'totalMinionsKilled',
            'visionScore', 'champLevel'
        ]
        
        for field in required_fields:
            assert field in participant, f"Missing field: {field}"
    
    @patch('src.generator.KafkaProducer')
    def test_team_distribution(self, mock_producer):
        """Test participants are distributed correctly across teams"""
        generator = MatchGenerator()
        match_data = generator.generate_match()
        
        team_100 = [p for p in match_data['info']['participants'] if p['teamId'] == 100]
        team_200 = [p for p in match_data['info']['participants'] if p['teamId'] == 200]
        
        assert len(team_100) == 5, "Team 100 should have 5 participants"
        assert len(team_200) == 5, "Team 200 should have 5 participants"
    
    @patch('src.generator.KafkaProducer')
    def test_winner_consistency(self, mock_producer):
        """Test winner is consistent across teams and participants"""
        generator = MatchGenerator()
        match_data = generator.generate_match()
        
        teams = match_data['info']['teams']
        winning_team_id = next(t['teamId'] for t in teams if t['win'])
        
        # Check participants match team win status
        for p in match_data['info']['participants']:
            expected_win = (p['teamId'] == winning_team_id)
            assert p['win'] == expected_win, "Participant win status doesn't match team"
    
    @patch('src.generator.KafkaProducer')
    def test_unique_champions(self, mock_producer):
        """Test each match uses unique champions"""
        generator = MatchGenerator()
        match_data = generator.generate_match()
        
        champions = [p['championName'] for p in match_data['info']['participants']]
        
        assert len(champions) == 10
        assert len(set(champions)) == 10, "Champions should be unique in a match"
    
    @patch('src.generator.KafkaProducer')
    def test_position_coverage(self, mock_producer):
        """Test all 5 positions are covered in each team"""
        generator = MatchGenerator()
        match_data = generator.generate_match()
        
        team_100_positions = [p['teamPosition'] for p in match_data['info']['participants'] if p['teamId'] == 100]
        team_200_positions = [p['teamPosition'] for p in match_data['info']['participants'] if p['teamId'] == 200]
        
        expected_positions = {"TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"}
        
        assert set(team_100_positions) == expected_positions, "Team 100 missing positions"
        assert set(team_200_positions) == expected_positions, "Team 200 missing positions"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
