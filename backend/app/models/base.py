"""
Database base model with common fields
"""

from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String


Base = declarative_base()


class TimestampMixin:
    """Mixin for adding timestamp fields"""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class UUIDMixin:
    """Mixin for adding UUID primary key"""
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )