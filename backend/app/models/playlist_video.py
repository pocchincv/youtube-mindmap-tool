"""
Junction table for many-to-many relationship between playlists and videos
"""

from datetime import datetime
from sqlalchemy import String, ForeignKey, Integer, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin, TimestampMixin


class PlaylistVideo(Base, UUIDMixin, TimestampMixin):
    """Many-to-many relationship table between playlists and videos"""
    
    __tablename__ = "playlist_videos"
    
    # Foreign keys
    playlist_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("playlists.id"),
        nullable=False,
        index=True
    )
    
    video_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("videos.id"),
        nullable=False,
        index=True
    )
    
    # Order of video in playlist
    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )
    
    # When the video was added to playlist
    added_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow
    )
    
    # Relationships
    playlist: Mapped["Playlist"] = relationship(
        "Playlist",
        back_populates="playlist_videos"
    )
    
    video: Mapped["Video"] = relationship(
        "Video",
        back_populates="playlist_videos"
    )
    
    # Constraints and indexes
    __table_args__ = (
        # Ensure unique video per playlist
        UniqueConstraint("playlist_id", "video_id", name="uq_playlist_video"),
        # Ensure unique position per playlist
        UniqueConstraint("playlist_id", "position", name="uq_playlist_position"),
        # Index for efficient queries
        Index("idx_playlist_video_playlist", "playlist_id"),
        Index("idx_playlist_video_video", "video_id"),
        Index("idx_playlist_video_position", "playlist_id", "position"),
        Index("idx_playlist_video_added", "playlist_id", "added_at"),
    )
    
    def __repr__(self) -> str:
        return f"<PlaylistVideo(playlist_id='{self.playlist_id}', video_id='{self.video_id}', position={self.position})>"