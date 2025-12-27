"""
Database connection management with async support, connection pooling, and health checks.
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from urllib.parse import urlparse

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
# Remove pool import - let SQLAlchemy choose the appropriate pool for async

from ..config import get_settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Database connection manager with connection pooling, health checks, and retry logic.
    """
    
    def __init__(self):
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self._settings = get_settings()
        
    def _create_engine(self) -> AsyncEngine:
        """
        Create async SQLAlchemy engine with proper configuration.
        """
        # Parse database URL to validate format
        parsed_url = urlparse(self._settings.database_url)
        if not parsed_url.scheme.startswith('postgresql'):
            raise ValueError("Only PostgreSQL databases are supported")
        
        # Engine configuration with async-compatible pooling
        engine_config = {
            "echo": self._settings.debug,  # Log SQL queries in debug mode
            "pool_size": self._settings.database_pool_size,
            "max_overflow": self._settings.database_max_overflow,
            "pool_timeout": self._settings.database_pool_timeout,
            "pool_recycle": 3600,  # Recycle connections every hour
            "pool_pre_ping": True,  # Validate connections before use
        }
        
        # Create async engine
        engine = create_async_engine(
            self._settings.database_url,
            **engine_config
        )
        
        # Add connection event listeners for monitoring
        self._setup_connection_events(engine)
        
        return engine
    
    def _setup_connection_events(self, engine: AsyncEngine) -> None:
        """
        Set up SQLAlchemy event listeners for connection monitoring.
        """
        @event.listens_for(engine.sync_engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            logger.debug("Database connection established")
            
        @event.listens_for(engine.sync_engine, "checkout")
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            logger.debug("Database connection checked out from pool")
            
        @event.listens_for(engine.sync_engine, "checkin")
        def on_checkin(dbapi_connection, connection_record):
            logger.debug("Database connection returned to pool")
            
        @event.listens_for(engine.sync_engine, "invalidate")
        def on_invalidate(dbapi_connection, connection_record, exception):
            logger.warning(f"Database connection invalidated: {exception}")
    
    @property
    def engine(self) -> AsyncEngine:
        """Get or create the database engine."""
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine
    
    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get or create the session factory."""
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False,
            )
        return self._session_factory
    
    async def health_check(self) -> dict:
        """
        Perform database health check with connection testing and performance monitoring.
        
        Returns:
            dict: Health check results with status and metrics
        """
        import time
        
        health_status = {
            "status": "healthy",
            "database": "postgresql",
            "connection_pool": {},
            "query_performance": {},
            "errors": []
        }
        
        try:
            # Test basic connectivity
            start_time = time.time()
            async with self.get_session() as session:
                result = await session.execute(text("SELECT 1 as health_check"))
                row = result.fetchone()
                if row[0] != 1:
                    raise Exception("Health check query returned unexpected result")
            
            query_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            health_status["query_performance"]["simple_query_ms"] = round(query_time, 2)
            
            # Get basic connection pool information
            health_status["connection_pool"] = {
                "type": str(type(self.engine.pool).__name__),
                "status": "active"
            }
            
            # Test more complex query for performance monitoring
            start_time = time.time()
            async with self.get_session() as session:
                await session.execute(text("""
                    SELECT 
                        current_database() as database_name,
                        current_user as current_user,
                        version() as version
                """))
            
            complex_query_time = (time.time() - start_time) * 1000
            health_status["query_performance"]["complex_query_ms"] = round(complex_query_time, 2)
            
            # Performance thresholds
            if query_time > 100:  # 100ms threshold
                health_status["errors"].append("Simple query performance degraded")
            if complex_query_time > 500:  # 500ms threshold
                health_status["errors"].append("Complex query performance degraded")
                
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["errors"].append(f"Database connection failed: {str(e)}")
            logger.error(f"Database health check failed: {e}")
        
        return health_status
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get database session with proper transaction management and error handling.
        
        Yields:
            AsyncSession: Database session with automatic cleanup
        """
        session = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()
    
    async def retry_connection(self, max_retries: int = 3, base_delay: float = 1.0) -> bool:
        """
        Implement database connection retry logic with exponential backoff.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        for attempt in range(max_retries):
            try:
                async with self.get_session() as session:
                    await session.execute(text("SELECT 1"))
                logger.info(f"Database connection successful on attempt {attempt + 1}")
                return True
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Database connection failed after {max_retries} attempts: {e}")
                    return False
                
                # Exponential backoff with jitter
                delay = base_delay * (2 ** attempt)
                jitter = delay * 0.1  # 10% jitter
                total_delay = delay + jitter
                
                logger.warning(f"Database connection attempt {attempt + 1} failed: {e}. Retrying in {total_delay:.2f}s")
                await asyncio.sleep(total_delay)
        
        return False
    
    async def close(self) -> None:
        """Close database engine and cleanup resources."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database engine closed")


# Global database manager instance
_db_manager = DatabaseManager()


def get_async_engine() -> AsyncEngine:
    """Get the async database engine."""
    return _db_manager.engine


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for getting database session.
    
    Yields:
        AsyncSession: Database session for request handling
    """
    async with _db_manager.get_session() as session:
        yield session


async def get_database_health() -> dict:
    """Get database health check results."""
    return await _db_manager.health_check()


async def close_database() -> None:
    """Close database connections (for application shutdown)."""
    await _db_manager.close()