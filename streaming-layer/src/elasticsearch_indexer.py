"""
Elasticsearch Indexer for LoL Match Data
Handles connection, index creation, and bulk indexing
"""

from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import ConnectionError, RequestError
import json
import logging
from typing import List, Dict, Any
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ElasticsearchIndexer:
    """
    Elasticsearch indexer for LoL match streaming data
    """
    
    def __init__(self, 
                 hosts: List[str] = None,
                 index_name: str = "lol_matches_stream",
                 mapping_file: str = None):
        """
        Initialize ES client
        
        Args:
            hosts: List of ES hosts (default: ["http://localhost:9200"])
            index_name: Name of the index
            mapping_file: Path to mapping JSON file
        """
        self.hosts = hosts or ["http://localhost:9200"]
        self.index_name = index_name
        self.mapping_file = mapping_file
        
        # Initialize ES client
        self.es = None
        self.connect()
        
        # Create index if not exists
        if self.es and not self.index_exists():
            self.create_index()
    
    def connect(self) -> bool:
        """
        Connect to Elasticsearch
        
        Returns:
            bool: True if connection successful
        """
        try:
            self.es = Elasticsearch(
                hosts=self.hosts,
                verify_certs=False,
                request_timeout=30,
                meta_header=False
            )
            
            # Test connection
            if self.es.ping():
                logger.info(f"✓ Connected to Elasticsearch: {self.hosts}")
                return True
            else:
                logger.error("✗ Failed to ping Elasticsearch")
                return False
                
        except ConnectionError as e:
            logger.error(f"✗ Connection error: {e}")
            self.es = None
            return False
    
    def index_exists(self) -> bool:
        """
        Check if index exists
        
        Returns:
            bool: True if index exists
        """
        try:
            return self.es.indices.exists(index=self.index_name)
        except Exception as e:
            logger.error(f"Error checking index existence: {e}")
            return False
    
    def create_index(self) -> bool:
        """
        Create index with mapping
        
        Returns:
            bool: True if creation successful
        """
        try:
            # Load mapping from file
            mapping = None
            if self.mapping_file:
                with open(self.mapping_file, 'r') as f:
                    mapping = json.load(f)
            
            # Create index
            if mapping:
                self.es.indices.create(
                    index=self.index_name,
                    body=mapping
                )
            else:
                self.es.indices.create(index=self.index_name)
            
            logger.info(f"✓ Created index: {self.index_name}")
            return True
            
        except RequestError as e:
            if e.error == 'resource_already_exists_exception':
                logger.warning(f"Index {self.index_name} already exists")
                return True
            else:
                logger.error(f"✗ Error creating index: {e}")
                return False
        except Exception as e:
            logger.error(f"✗ Unexpected error creating index: {e}")
            return False
    
    def index_document(self, document: Dict[str, Any]) -> bool:
        """
        Index single document
        
        Args:
            document: Document to index
            
        Returns:
            bool: True if indexing successful
        """
        try:
            # Add @timestamp for Kibana
            document['@timestamp'] = document.get('timestamp', 
                                                  int(datetime.now().timestamp() * 1000))
            
            response = self.es.index(
                index=self.index_name,
                document=document
            )
            
            return response['result'] in ['created', 'updated']
            
        except Exception as e:
            logger.error(f"✗ Error indexing document: {e}")
            return False
    
    def bulk_index(self, documents: List[Dict[str, Any]]) -> tuple:
        """
        Bulk index documents
        
        Args:
            documents: List of documents to index
            
        Returns:
            tuple: (success_count, failed_count)
        """
        try:
            if not documents:
                return (0, 0)
            
            # Prepare actions for bulk API
            actions = []
            for doc in documents:
                # Add @timestamp
                doc['@timestamp'] = doc.get('timestamp', 
                                           int(datetime.now().timestamp() * 1000))
                
                actions.append({
                    '_index': self.index_name,
                    '_source': doc
                })
            
            # Execute bulk
            success, failed = helpers.bulk(
                self.es,
                actions,
                raise_on_error=False,
                stats_only=True
            )
            
            logger.info(f"✓ Bulk indexed: {success} docs, {failed} failed")
            return (success, failed)
            
        except Exception as e:
            logger.error(f"✗ Error in bulk indexing: {e}")
            return (0, len(documents))
    
    def delete_index(self) -> bool:
        """
        Delete index
        
        Returns:
            bool: True if deletion successful
        """
        try:
            if self.index_exists():
                self.es.indices.delete(index=self.index_name)
                logger.info(f"✓ Deleted index: {self.index_name}")
                return True
            else:
                logger.warning(f"Index {self.index_name} does not exist")
                return False
        except Exception as e:
            logger.error(f"✗ Error deleting index: {e}")
            return False
    
    def refresh_index(self) -> bool:
        """
        Refresh index to make documents searchable
        
        Returns:
            bool: True if refresh successful
        """
        try:
            self.es.indices.refresh(index=self.index_name)
            return True
        except Exception as e:
            logger.error(f"✗ Error refreshing index: {e}")
            return False
    
    def count_documents(self) -> int:
        """
        Count documents in index
        
        Returns:
            int: Document count
        """
        try:
            count = self.es.count(index=self.index_name)
            return count['count']
        except Exception as e:
            logger.error(f"✗ Error counting documents: {e}")
            return 0
    
    def close(self):
        """Close ES connection"""
        if self.es:
            self.es.close()
            logger.info("✓ Closed Elasticsearch connection")


# Example usage
if __name__ == "__main__":
    # Initialize indexer
    indexer = ElasticsearchIndexer(
        hosts=["http://localhost:9200"],
        index_name="lol_matches_stream",
        mapping_file="streaming-layer/config/es_mapping.json"
    )
    
    # Test document
    test_doc = {
        "match_id": "TEST_123",
        "timestamp": int(datetime.now().timestamp() * 1000),
        "game_duration": 1800,
        "participant_id": "P1",
        "summoner_name": "TestPlayer",
        "champion_name": "Ahri",
        "team_id": 100,
        "position": "MIDDLE",
        "win": True,
        "kills": 10,
        "deaths": 2,
        "assists": 15,
        "kda": 12.5,
        "total_damage_dealt": 50000,
        "gold_earned": 15000,
        "cs": 200,
        "vision_score": 30,
        "gold_per_minute": 500.0,
        "damage_per_minute": 1666.67,
        "cs_per_minute": 6.67
    }
    
    # Index test document
    success = indexer.index_document(test_doc)
    print(f"Indexing: {'Success' if success else 'Failed'}")
    
    # Count documents
    count = indexer.count_documents()
    print(f"Total documents: {count}")
    
    # Close connection
    indexer.close()
