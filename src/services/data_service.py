"""Data persistence service."""

import json
import os
import logging
from typing import Dict, Optional
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from config.config import DATA_FILE
except ImportError:
    DATA_FILE = "data/bot_data.json"

logger = logging.getLogger(__name__)


class DataService:
    """Service for managing data persistence."""
    
    def __init__(self, data_file: Optional[str] = None):
        """
        Initialize data service.
        
        Args:
            data_file: Path to the data file (uses config default if not provided)
        """
        self.data_file = Path(data_file or DATA_FILE)
        self._ensure_data_directory()
    
    def _ensure_data_directory(self):
        """Ensure data directory exists."""
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
    
    def load_data(self) -> Dict:
        """
        Load data from file.
        
        Returns:
            Dictionary containing bots and channels
        """
        if not self.data_file.exists():
            logger.info(f"Data file {self.data_file} does not exist, returning empty data")
            return {'bots': {}, 'channels': {}}
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Successfully loaded data from {self.data_file}")
                return {
                    'bots': data.get('bots', {}),
                    'channels': data.get('channels', {})
                }
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {self.data_file}: {e}")
            return {'bots': {}, 'channels': {}}
        except Exception as e:
            logger.error(f"Error loading data from {self.data_file}: {e}")
            return {'bots': {}, 'channels': {}}
    
    def save_data(self, bots: Dict, channels: Dict) -> bool:
        """
        Save data to file.
        
        Args:
            bots: Dictionary of bots
            channels: Dictionary of channels
            
        Returns:
            True if successful, False otherwise
        """
        try:
            data = {
                'bots': bots,
                'channels': channels,
                'last_updated': str(os.path.getmtime(self.data_file) if self.data_file.exists() else None)
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully saved data to {self.data_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving data to {self.data_file}: {e}")
            return False
    
    def backup_data(self, backup_file: Optional[str] = None) -> bool:
        """
        Create a backup of the data file.
        
        Args:
            backup_file: Optional backup file path
            
        Returns:
            True if successful, False otherwise
        """
        if not self.data_file.exists():
            logger.warning("No data file to backup")
            return False
        
        if backup_file is None:
            backup_file = str(self.data_file) + '.backup'
        
        try:
            import shutil
            shutil.copy2(self.data_file, backup_file)
            logger.info(f"Created backup at {backup_file}")
            return True
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False

