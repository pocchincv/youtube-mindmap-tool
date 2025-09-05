"""
Processing cache model for central database optimization
"""

from datetime import datetime, timedelta
from sqlalchemy import String, ForeignKey, Text, JSON, Index, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any

from .base import Base, UUIDMixin, TimestampMixin


class ProcessingCache(Base, UUIDMixin, TimestampMixin):
    """Cache for processed video data to optimize central database usage"""
    
    __tablename__ = "processing_cache"
    
    # Foreign key to video
    video_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("videos.id"),
        nullable=False,
        index=True
    )
    
    # Cache key for identifying the type of cached data
    cache_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )  # e.g., "transcript", "mindmap", "analysis", "thumbnail"
    
    # Cache data type
    data_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="json"
    )  # json, text, binary, url
    
    # Cached data content
    data_content: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    
    # Text content for large text data
    text_content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # URL or file path for binary/media content
    file_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    
    # Cache metadata
    cache_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="1.0"
    )
    
    # Expiration settings
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True
    )
    
    is_permanent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    
    # Cache statistics
    hit_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )
    
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True
    )
    
    # Processing information
    processing_time: Mapped[Optional[int]] = mapped_column(
        nullable=True  # Processing time in milliseconds
    )
    
    # Relationships
    video: Mapped["Video"] = relationship(
        "Video",
        back_populates="processing_cache_entries"
    )
    
    # Indexes for efficient cache lookups
    __table_args__ = (
        Index("idx_cache_video_key", "video_id", "cache_key"),
        Index("idx_cache_key_version", "cache_key", "cache_version"),
        Index("idx_cache_expires", "expires_at"),
        Index("idx_cache_accessed", "last_accessed_at"),
        Index("idx_cache_type", "data_type"),
    )
    
    def __repr__(self) -> str:
        return f"<ProcessingCache(video_id='{self.video_id}', cache_key='{self.cache_key}', version='{self.cache_version}')>"
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        if self.is_permanent:
            return False
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if cache entry is valid and not expired"""
        return not self.is_expired
    
    def extend_expiry(self, hours: int = 24) -> None:
        """Extend cache expiry by specified hours"""
        if not self.is_permanent:
            self.expires_at = datetime.utcnow() + timedelta(hours=hours)
    
    def mark_accessed(self) -> None:
        """Mark cache as accessed and increment hit count"""
        self.last_accessed_at = datetime.utcnow()
        self.hit_count += 1
    
    def get_content(self) -> Any:
        """Get the appropriate content based on data type"""
        if self.data_type == "json":
            return self.data_content
        elif self.data_type == "text":
            return self.text_content
        elif self.data_type in ["binary", "url"]:
            return self.file_path
        return None