"""
Video model for YouTube video metadata and processing status
"""

from datetime import datetime
from sqlalchemy import String, Integer, Text, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any, List

from .base import Base, UUIDMixin, TimestampMixin


class Video(Base, UUIDMixin, TimestampMixin):
    """Video model with YouTube metadata and processing information"""
    
    __tablename__ = "videos"
    
    # YouTube metadata
    youtube_id: Mapped[str] = mapped_column(
        String(20),  # YouTube video IDs are 11 characters, but allowing extra space
        unique=True,
        nullable=False,
        index=True
    )
    
    title: Mapped[str] = mapped_column(
        String(500),  # YouTube titles can be long
        nullable=False
    )
    
    channel_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    
    duration: Mapped[Optional[int]] = mapped_column(
        Integer,  # Duration in seconds
        nullable=True
    )
    
    view_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    
    thumbnail_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Processing fields
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True
    )
    
    processing_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        index=True
    )  # pending, processing, completed, failed
    
    # Transcript and content data
    transcript_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    
    # Additional metadata from processing  
    video_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        default=dict
    )
    
    # Relationships
    playlist_videos: Mapped[List["PlaylistVideo"]] = relationship(
        "PlaylistVideo",
        back_populates="video",
        cascade="all, delete-orphan"
    )
    
    mindmap_nodes: Mapped[List["MindMapNode"]] = relationship(
        "MindMapNode", 
        back_populates="video",
        cascade="all, delete-orphan"
    )
    
    processing_cache_entries: Mapped[List["ProcessingCache"]] = relationship(
        "ProcessingCache",
        back_populates="video",
        cascade="all, delete-orphan"
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_video_status_created", "processing_status", "created_at"),
        Index("idx_video_title_search", "title"),
        Index("idx_video_channel_name", "channel_name"),
    )
    
    def __repr__(self) -> str:
        return f"<Video(id='{self.id}', youtube_id='{self.youtube_id}', title='{self.title[:50]}...')>"
    
    @property
    def is_processed(self) -> bool:
        """Check if video processing is completed"""
        return self.processing_status == "completed"
    
    @property
    def has_transcript(self) -> bool:
        """Check if video has transcript data"""
        return self.transcript_data is not None and len(self.transcript_data) > 0