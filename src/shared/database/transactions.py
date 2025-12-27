"""
Database transaction management utilities with proper rollback and error handling.
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Type, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from .connection import get_db_session

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=Exception)


class TransactionError(Exception):
    """Custom exception for transaction-related errors."""
    pass


@asynccontextmanager
async def database_transaction(
    session: Optional[AsyncSession] = None,
    rollback_on_exception: bool = True,
    reraise_exceptions: bool = True
) -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database transactions with automatic rollback on errors.
    
    Args:
        session: Optional existing session to use
        rollback_on_exception: Whether to rollback on exceptions
        reraise_exceptions: Whether to reraise caught exceptions
        
    Yields:
        AsyncSession: Database session within transaction context
        
    Raises:
        TransactionError: If transaction fails and reraise_exceptions is True
    """
    if session is not None:
        # Use existing session (nested transaction)
        async with session.begin_nested() as savepoint:
            try:
                yield session
                await savepoint.commit()
            except Exception as e:
                if rollback_on_exception:
                    await savepoint.rollback()
                    logger.error(f"Nested transaction rolled back due to error: {e}")
                
                if reraise_exceptions:
                    raise TransactionError(f"Nested transaction failed: {e}") from e
    else:
        # Create new session and transaction
        async with get_db_session() as session:
            try:
                async with session.begin():
                    yield session
                    # Commit happens automatically if no exception
            except Exception as e:
                # Rollback happens automatically on exception
                logger.error(f"Transaction rolled back due to error: {e}")
                
                if reraise_exceptions:
                    raise TransactionError(f"Transaction failed: {e}") from e


@asynccontextmanager
async def atomic_operation(
    session: Optional[AsyncSession] = None,
    isolation_level: Optional[str] = None
) -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for atomic database operations with optional isolation level.
    
    Args:
        session: Optional existing session to use
        isolation_level: Optional SQL isolation level
        
    Yields:
        AsyncSession: Database session for atomic operations
    """
    async with database_transaction(session=session) as tx_session:
        if isolation_level:
            await tx_session.execute(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}")
        
        yield tx_session


class TransactionManager:
    """
    Advanced transaction manager with retry logic and error handling.
    """
    
    def __init__(self, max_retries: int = 3, retry_exceptions: tuple = (SQLAlchemyError,)):
        self.max_retries = max_retries
        self.retry_exceptions = retry_exceptions
    
    async def execute_with_retry(
        self,
        operation,
        *args,
        session: Optional[AsyncSession] = None,
        **kwargs
    ):
        """
        Execute database operation with retry logic.
        
        Args:
            operation: Async function to execute
            *args: Arguments for the operation
            session: Optional database session
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Result of the operation
            
        Raises:
            TransactionError: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                async with database_transaction(session=session) as tx_session:
                    if session is None:
                        # Pass the transaction session to the operation
                        result = await operation(*args, session=tx_session, **kwargs)
                    else:
                        result = await operation(*args, **kwargs)
                    
                    return result
                    
            except self.retry_exceptions as e:
                last_exception = e
                logger.warning(
                    f"Transaction attempt {attempt + 1} failed: {e}. "
                    f"{'Retrying...' if attempt < self.max_retries - 1 else 'No more retries.'}"
                )
                
                if attempt == self.max_retries - 1:
                    break
                    
                # Simple backoff - could be made more sophisticated
                import asyncio
                await asyncio.sleep(0.1 * (2 ** attempt))
            
            except Exception as e:
                # Non-retryable exception
                logger.error(f"Non-retryable transaction error: {e}")
                raise TransactionError(f"Transaction failed with non-retryable error: {e}") from e
        
        # All retries exhausted
        raise TransactionError(
            f"Transaction failed after {self.max_retries} attempts. Last error: {last_exception}"
        ) from last_exception
    
    @asynccontextmanager
    async def managed_transaction(
        self,
        session: Optional[AsyncSession] = None,
        isolation_level: Optional[str] = None
    ) -> AsyncGenerator[AsyncSession, None]:
        """
        Context manager for managed transactions with automatic retry.
        
        Args:
            session: Optional existing session
            isolation_level: Optional SQL isolation level
            
        Yields:
            AsyncSession: Managed database session
        """
        async with atomic_operation(session=session, isolation_level=isolation_level) as tx_session:
            yield tx_session


# Global transaction manager instance
transaction_manager = TransactionManager()


# Convenience functions
async def execute_in_transaction(operation, *args, **kwargs):
    """
    Execute operation within a database transaction.
    
    Args:
        operation: Async function to execute
        *args: Arguments for the operation
        **kwargs: Keyword arguments for the operation
        
    Returns:
        Result of the operation
    """
    return await transaction_manager.execute_with_retry(operation, *args, **kwargs)


@asynccontextmanager
async def managed_transaction(
    session: Optional[AsyncSession] = None,
    isolation_level: Optional[str] = None
) -> AsyncGenerator[AsyncSession, None]:
    """
    Convenience context manager for managed transactions.
    
    Args:
        session: Optional existing session
        isolation_level: Optional SQL isolation level
        
    Yields:
        AsyncSession: Managed database session
    """
    async with transaction_manager.managed_transaction(
        session=session,
        isolation_level=isolation_level
    ) as tx_session:
        yield tx_session