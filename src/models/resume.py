from datetime import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass
class Resume:
    """
    Data model for resume records
    Matches the DynamoDB schema used in the Node.js version
    """
    user_id: str
    resume_version: str  # "v1", "v2", etc.
    resume_url: str      # S3 URL
    resume_name: str     # Original filename
    created_at: str      # ISO timestamp
    
    def __post_init__(self):
        """Validate the resume data after initialization"""
        if not self.user_id:
            raise ValueError("user_id is required")
        if not self.resume_version:
            raise ValueError("resume_version is required")
        if not self.resume_url:
            raise ValueError("resume_url is required")
        if not self.resume_name:
            raise ValueError("resume_name is required")
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Resume':
        """Create a Resume object from a dictionary (e.g., DynamoDB response)"""
        return cls(
            user_id=data.get('user_id', ''),
            resume_version=data.get('resume_version', ''),
            resume_url=data.get('resume_url', ''),
            resume_name=data.get('resume_name', ''),
            created_at=data.get('created_at', '')
        )
    
    def to_dict(self) -> dict:
        """Convert Resume object to dictionary for storage"""
        return {
            'user_id': self.user_id,
            'resume_version': self.resume_version,
            'resume_url': self.resume_url,
            'resume_name': self.resume_name,
            'created_at': self.created_at
        }
    
    def to_dynamo_item(self) -> dict:
        """Convert Resume object to DynamoDB item format"""
        return {
            'user_id': {'S': self.user_id},
            'resume_version': {'S': self.resume_version},
            'resume_url': {'S': self.resume_url},
            'resume_name': {'S': self.resume_name},
            'created_at': {'S': self.created_at}
        }
    
    @classmethod
    def from_dynamo_item(cls, item: dict) -> 'Resume':
        """Create Resume object from DynamoDB item format"""
        return cls(
            user_id=item.get('user_id', {}).get('S', ''),
            resume_version=item.get('resume_version', {}).get('S', ''),
            resume_url=item.get('resume_url', {}).get('S', ''),
            resume_name=item.get('resume_name', {}).get('S', ''),
            created_at=item.get('created_at', {}).get('S', '')
        )
    
    def get_version_number(self) -> int:
        """Extract the numeric version from resume_version (e.g., "v1" -> 1)"""
        try:
            return int(self.resume_version[1:])  # Remove 'v' prefix
        except (ValueError, IndexError):
            return 0
    
    def get_hypothes_is_url(self) -> str:
        """Generate the Hypothes.is annotation URL"""
        return f"https://via.hypothes.is/{self.resume_url}"
    
    def is_valid(self) -> bool:
        """Check if the resume data is valid"""
        try:
            self.__post_init__()
            return True
        except ValueError:
            return False


@dataclass 
class DiscordAttachment:
    """
    Data model for Discord attachment information
    Extracted from Discord interaction payload
    """
    id: str
    filename: str
    content_type: str
    size: int
    url: str
    proxy_url: str
    ephemeral: bool = True
    
    @classmethod
    def from_discord_data(cls, attachment_data: dict) -> 'DiscordAttachment':
        """Create DiscordAttachment from Discord API response"""
        return cls(
            id=attachment_data.get('id', ''),
            filename=attachment_data.get('filename', ''),
            content_type=attachment_data.get('content_type', ''),
            size=attachment_data.get('size', 0),
            url=attachment_data.get('url', ''),
            proxy_url=attachment_data.get('proxy_url', ''),
            ephemeral=attachment_data.get('ephemeral', True)
        )
    
    def is_pdf(self) -> bool:
        """Check if the attachment is a PDF"""
        return self.content_type == 'application/pdf'
    
    def size_mb(self) -> float:
        """Get file size in megabytes"""
        return self.size / (1024 * 1024)
    
    def is_valid_size(self, max_mb: int = 10) -> bool:
        """Check if file size is within limits"""
        return self.size_mb() <= max_mb
    
    def to_dict(self) -> dict:
        """Convert to dictionary for validation functions"""
        return {
            'id': self.id,
            'filename': self.filename,
            'content_type': self.content_type,
            'size': self.size,
            'url': self.url,
            'proxy_url': self.proxy_url,
            'ephemeral': self.ephemeral
        }