"""
User model for authentication and preferences
"""

from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any, List

from .base import Base, UUIDMixin, TimestampMixin


class User(Base, UUIDMixin, TimestampMixin):
    """User model with Google OAuth integration"""
    
    __tablename__ = "users"
    
    # Authentication fields
    google_oauth_id: Mapped[Optional[str]] = mapped_column(
        String(255), 
        unique=True, 
        nullable=True,
        index=True
    )
    
    email: Mapped[Optional[str]] = mapped_column(
        String(255), 
        unique=True, 
        nullable=True,
        index=True
    )
    
    display_name: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True
    )
    
    # User preferences stored as JSON
    preferences: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        default=dict
    )
    
    # Relationships
    playlists: Mapped[List["Playlist"]] = relationship(
        "Playlist",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    search_history: Mapped[List["SearchHistory"]] = relationship(
        "SearchHistory",
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    
    api_configurations: Mapped[List["APIConfiguration"]] = relationship(
        "APIConfiguration",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(id='{self.id}', email='{self.email}', display_name='{self.display_name}')>"