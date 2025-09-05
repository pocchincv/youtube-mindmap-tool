"""
API Configuration model for storing encrypted user API keys
"""

from datetime import datetime
from sqlalchemy import String, ForeignKey, Text, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from .base import Base, UUIDMixin, TimestampMixin


class APIConfiguration(Base, UUIDMixin, TimestampMixin):
    """User API configuration with encrypted storage for API keys"""
    
    __tablename__ = "api_configurations"
    
    # Foreign key to user
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    
    # API service information
    service_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )  # openai, google, youtube, whisper
    
    service_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )  # stt, llm, api, oauth
    
    # Configuration data (encrypted)
    api_key_encrypted: Mapped[Optional[str]] = mapped_column(
        Text,  # Encrypted API key
        nullable=True
    )
    
    # Additional configuration (encrypted if sensitive)
    config_data_encrypted: Mapped[Optional[str]] = mapped_column(
        Text,  # Other encrypted configuration
        nullable=True
    )
    
    # Non-sensitive configuration
    public_config: Mapped[Optional[str]] = mapped_column(
        Text,  # JSON string for non-sensitive config
        nullable=True
    )
    
    # Configuration status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    
    # Usage tracking
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True
    )
    
    usage_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )
    
    # Rate limiting and quotas
    daily_quota: Mapped[Optional[int]] = mapped_column(
        nullable=True
    )
    
    daily_usage: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )
    
    quota_reset_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True
    )
    
    # Error tracking
    last_error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    error_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="api_configurations"
    )
    
    # Indexes for efficient queries
    __table_args__ = (
        Index("idx_api_config_user_service", "user_id", "service_name"),
        Index("idx_api_config_user_type", "user_id", "service_type"),
        Index("idx_api_config_active", "is_active"),
        Index("idx_api_config_verified", "is_verified"),
        Index("idx_api_config_last_used", "last_used_at"),
    )
    
    def __repr__(self) -> str:
        return f"<APIConfiguration(user_id='{self.user_id}', service='{self.service_name}', type='{self.service_type}')>"
    
    @property
    def is_usable(self) -> bool:
        """Check if API configuration is ready to use"""
        return self.is_active and self.is_verified and self.api_key_encrypted is not None
    
    @property
    def is_quota_exceeded(self) -> bool:
        """Check if daily quota is exceeded"""
        if self.daily_quota is None:
            return False
        return self.daily_usage >= self.daily_quota
    
    @property
    def quota_remaining(self) -> Optional[int]:
        """Get remaining daily quota"""
        if self.daily_quota is None:
            return None
        return max(0, self.daily_quota - self.daily_usage)
    
    def increment_usage(self) -> None:
        """Increment usage counters"""
        self.usage_count += 1
        self.daily_usage += 1
        self.last_used_at = datetime.utcnow()
    
    def record_error(self, error_message: str) -> None:
        """Record an API error"""
        self.last_error = error_message
        self.error_count += 1
    
    def reset_daily_quota(self) -> None:
        """Reset daily usage counter"""
        self.daily_usage = 0
        self.quota_reset_at = datetime.utcnow()