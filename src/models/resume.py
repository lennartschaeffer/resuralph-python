from dataclasses import dataclass


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