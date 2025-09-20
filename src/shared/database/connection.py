"""Database connection management with SQLAlchemy async support."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.shared.config import get_settings

# Global variables for engine and session maker
_engine = None
_async_session_maker = None


def get_engine():
    """Get or create the async database engine."""
    global _engine
    
    if _engine is None:
        settings = get_settings()
        
        # Create async engine with connection pooling
        _engine = create_async_engine(
            settings.database_url,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=settings.database_pool_timeout,
            pool_pre_ping=True,  # Validate connections before use
            echo=settings.debug,  # Log SQL queries in debug mode
            # Use NullPool for testing to avoid connection issues
            poolclass=NullPool if settings.environment == "testing" else None,
        )
    
    return _engine


def get_session_maker():
    """Get or create the async session maker."""
    global _async_session_maker
    
    if _async_session_maker is None:
        engine = get_engine()
        _async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    
    return _async_session_maker


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session with automatic cleanup."""
    session_maker = get_session_maker()
    
    async with session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_session_dependency() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions."""
    async with get_db_session() as session:
        yield session


async def close_db_connections():
    """Close all database connections."""
    global _engine, _async_session_maker
    
    if _engine:
        await _engine.dispose()
        _engine = None
        _async_session_maker = None