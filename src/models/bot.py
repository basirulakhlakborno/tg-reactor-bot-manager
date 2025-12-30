"""Bot and Channel data models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Bot:
    """Bot data model."""
    id: str
    token: str
    name: str
    is_running: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self, mask_token: bool = True) -> dict:
        """Convert bot to dictionary.
        
        Args:
            mask_token: If True, mask the token for API responses. If False, return full token.
        """
        # Mask token for security in API responses only
        if mask_token:
            masked_token = self.token[:10] + '...' + self.token[-4:] if len(self.token) > 14 else '***'
        else:
            masked_token = self.token
        
        return {
            'id': self.id,
            'token': masked_token,
            'name': self.name,
            'is_running': self.is_running,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Bot':
        """Create bot from dictionary."""
        return cls(
            id=data.get('id', ''),
            token=data.get('token', ''),
            name=data.get('name', ''),
            is_running=data.get('is_running', False),
            created_at=data.get('created_at', datetime.now().isoformat())
        )


@dataclass
class Channel:
    """Channel data model."""
    id: str
    channel_id: str
    name: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        """Convert channel to dictionary."""
        return {
            'id': self.id,
            'channel_id': self.channel_id,
            'name': self.name,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Channel':
        """Create channel from dictionary."""
        return cls(
            id=data.get('id', ''),
            channel_id=data.get('channel_id', ''),
            name=data.get('name', ''),
            created_at=data.get('created_at', datetime.now().isoformat())
        )

