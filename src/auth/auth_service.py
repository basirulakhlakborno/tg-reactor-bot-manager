"""Authentication service."""

import hashlib
import json
import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Service for managing authentication."""
    
    def __init__(self, config_file: str = "data/config.json"):
        """
        Initialize auth service.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load configuration from file."""
        if not self.config_file.exists():
            return {
                'setup_complete': False,
                'admin_username': None,
                'admin_password_hash': None
            }
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {
                'setup_complete': False,
                'admin_username': None,
                'admin_password_hash': None
            }
    
    def _save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def is_setup_complete(self) -> bool:
        """Check if setup is complete."""
        return self.config.get('setup_complete', False)
    
    def complete_setup(self, username: str, password: str):
        """
        Complete the setup process.
        
        Args:
            username: Admin username
            password: Admin password
        """
        password_hash = self._hash_password(password)
        self.config['setup_complete'] = True
        self.config['admin_username'] = username
        self.config['admin_password_hash'] = password_hash
        self._save_config()
        logger.info("Setup completed successfully")
    
    def _hash_password(self, password: str) -> str:
        """Hash a password."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str) -> bool:
        """Verify a password."""
        if not self.config.get('admin_password_hash'):
            return False
        password_hash = self._hash_password(password)
        return password_hash == self.config['admin_password_hash']
    
    def verify_login(self, username: str, password: str) -> bool:
        """
        Verify login credentials.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            True if credentials are valid
        """
        if not self.is_setup_complete():
            return False
        
        stored_username = self.config.get('admin_username')
        if username != stored_username:
            return False
        
        return self.verify_password(password)
    
    def get_username(self) -> Optional[str]:
        """Get the admin username."""
        return self.config.get('admin_username')

