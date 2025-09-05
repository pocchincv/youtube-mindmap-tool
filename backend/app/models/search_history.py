"""
Search history model for storing user search queries and results
"""

from sqlalchemy import String, ForeignKey, Text, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any, List

from .base import Base, UUIDMixin, TimestampMixin


class SearchHistory(Base, UUIDMixin, TimestampMixin):
    """User search history with natural language queries and results"""
    
    __tablename__ = "search_history"
    
    # Foreign key to user
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    
    # Search query information
    query: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    
    # Query language and type
    query_language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="zh-TW"
    )
    
    query_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="natural_language"
    )  # natural_language, keyword, advanced
    
    # Search results
    results_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )
    
    # Detailed search results with video segments
    search_results: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON,
        nullable=True
    )
    
    # Search metadata and context
    query_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        default=dict
    )
    
    # Performance metrics
    search_duration: Mapped[Optional[int]] = mapped_column(
        nullable=True  # Search time in milliseconds
    )
    
    # User interaction with results
    clicked_results: Mapped[Optional[List[str]]] = mapped_column(
        JSON,  # List of video IDs that user clicked
        nullable=True,
        default=list
    )
    
    # Search context (which playlist, filters applied)
    search_context: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="search_history"
    )
    
    # Indexes for efficient queries
    __table_args__ = (
        Index("idx_search_user_created", "user_id", "created_at"),
        Index("idx_search_query_lang", "query_language"),
        Index("idx_search_type", "query_type"),
        Index("idx_search_results_count", "results_count"),
        Index("idx_search_user_query", "user_id", "query"),  # For query text search
    )
    
    def __repr__(self) -> str:
        return f"<SearchHistory(user_id='{self.user_id}', query='{self.query[:50]}...', results={self.results_count})>"
    
    @property
    def has_results(self) -> bool:
        """Check if search returned any results"""
        return self.results_count > 0
    
    @property
    def was_successful(self) -> bool:
        """Check if search was successful (has results and completed)"""
        return self.has_results and self.search_results is not None
    
    def add_clicked_result(self, video_id: str) -> None:
        """Add a video ID to clicked results"""
        if self.clicked_results is None:
            self.clicked_results = []
        if video_id not in self.clicked_results:
            self.clicked_results.append(video_id)
    
    def get_top_results(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top search results limited by count"""
        if not self.search_results:
            return []
        return self.search_results[:limit]