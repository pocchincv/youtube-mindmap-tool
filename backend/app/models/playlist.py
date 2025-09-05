"""
Playlist model for organizing videos into collections
"""

from sqlalchemy import String, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

from .base import Base, UUIDMixin, TimestampMixin


class Playlist(Base, UUIDMixin, TimestampMixin):
    """Playlist model for video organization"""
    
    __tablename__ = "playlists"
    
    # Foreign key to user
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    
    # Playlist information
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    description: Mapped[str] = mapped_column(
        String(1000),
        nullable=True
    )
    
    # System playlists like "Uncategorized" and "Smart Search Result"
    is_system_playlist: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    
    # Display order for UI
    display_order: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="playlists"
    )
    
    playlist_videos: Mapped[List["PlaylistVideo"]] = relationship(
        "PlaylistVideo",
        back_populates="playlist",
        cascade="all, delete-orphan"
    )
    
    # Indexes for efficient queries
    __table_args__ = (
        Index("idx_playlist_user_name", "user_id", "name"),
        Index("idx_playlist_system", "is_system_playlist"),
        Index("idx_playlist_user_order", "user_id", "display_order"),
    )
    
    def __repr__(self) -> str:
        return f"<Playlist(id='{self.id}', name='{self.name}', user_id='{self.user_id}')>"
    
    @property
    def video_count(self) -> int:
        """Get the number of videos in this playlist"""
        return len(self.playlist_videos)
    
    def is_default_playlist(self, name: str) -> bool:
        """Check if this is a default system playlist"""
        default_names = ["Uncategorized", "Smart Search Result"]
        return self.is_system_playlist and self.name in default_names