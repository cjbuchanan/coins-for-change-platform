"""
Base database model with audit fields and common functionality.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class BaseModel(Base):
    """
    Base model with audit fields and common functionality.
    
    All models should inherit from this class to get:
    - UUID primary key
    - Created/updated timestamps
    - Created/updated by user tracking
    """
    __abstract__ = True
    
    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    
    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Audit user tracking
    created_by: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    updated_by: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"