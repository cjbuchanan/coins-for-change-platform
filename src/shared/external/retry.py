"""
Retry logic with exponential backoff and jitter for external service calls.
"""
import asyncio
import logging
import random
import time
from functools import wraps
from typing import Any, Callable, List, Optional, Type, TypeVar, Union

logger = logging.getLogger(__name__)

F = TypeVar('F', bound=Callable[..., Any])


class RetryError(Exception):
    """Exception raised when all retry attempts are exhausted."""
    
    def __init__(self, message: str, last_exception: Exception, attempts: int):
        super().__init__(message)
        self.last_exception = last_exception
        self.attempts = attempts


class RetryManager:
    """
    Retry manager with exponential backoff and jitter.
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Optional[List[Type[Exception]]] = None
    ):
        """
        Initialize retry manager.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff calculation
            jitter: Whether to add random jitter to delays
            retryable_exceptions: Exception types that should trigger retries
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or [Exception]
    
    def _calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for the given attempt with exponential backoff and jitter.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        # Exponential backoff
        delay = self.base_delay * (self.exponential_base ** attempt)
        
        # Cap at max delay
        delay = min(delay, self.max_delay)
        
        # Add jitter (±10% of delay)
        if self.jitter:
            jitter_amount = delay * 0.1
            delay += random.uniform(-jitter_amount, jitter_amount)
        
        return max(0, delay)
    
    def _should_retry(self, exception: Exception) -> bool:
        """
        Check if the exception should trigger a retry.
        
        Args:
            exception: Exception that occurred
            
        Returns:
            True if should retry, False otherwise
        """
        return any(isinstance(exception, exc_type) for exc_type in self.retryable_exceptions)
    
    async def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            RetryError: If all retry attempts are exhausted
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):  # +1 for initial attempt
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
                    
            except Exception as e:
                last_exception = e
                
                # Don't retry if this is the last attempt
                if attempt == self.max_retries:
                    break
                
                # Don't retry if exception is not retryable
                if not self._should_retry(e):
                    logger.warning(f"Non-retryable exception occurred: {type(e).__name__}: {e}")
                    break
                
                # Calculate delay and wait
                delay = self._calculate_delay(attempt)
                logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retries + 1} failed: {type(e).__name__}: {e}. "
                    f"Retrying in {delay:.2f}s"
                )
                
                await asyncio.sleep(delay)
        
        # All attempts exhausted
        raise RetryError(
            f"All {self.max_retries + 1} attempts failed",
            last_exception,
            self.max_retries + 1
        )

def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Optional[List[Type[Exception]]] = None
) -> Callable[[F], F]:
    """
    Decorator to add retry logic to functions.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff calculation
        jitter: Whether to add random jitter to delays
        retryable_exceptions: Exception types that should trigger retries
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: F) -> F:
        retry_manager = RetryManager(
            max_retries=max_retries,
            base_delay=base_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retryable_exceptions=retryable_exceptions
        )
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await retry_manager.execute_with_retry(func, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return asyncio.run(retry_manager.execute_with_retry(func, *args, **kwargs))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Common retry configurations
class RetryConfigs:
    """Predefined retry configurations for common scenarios."""
    
    # Quick operations (API calls, cache operations)
    QUICK = {
        "max_retries": 3,
        "base_delay": 0.5,
        "max_delay": 10.0,
        "exponential_base": 2.0,
        "jitter": True
    }
    
    # Standard operations (database queries, search operations)
    STANDARD = {
        "max_retries": 3,
        "base_delay": 1.0,
        "max_delay": 30.0,
        "exponential_base": 2.0,
        "jitter": True
    }
    
    # Long operations (file uploads, batch processing)
    LONG = {
        "max_retries": 5,
        "base_delay": 2.0,
        "max_delay": 120.0,
        "exponential_base": 2.0,
        "jitter": True
    }
    
    # Network operations (external API calls)
    NETWORK = {
        "max_retries": 4,
        "base_delay": 1.0,
        "max_delay": 60.0,
        "exponential_base": 2.0,
        "jitter": True,
        "retryable_exceptions": [
            ConnectionError,
            TimeoutError,
            OSError,  # Network-related OS errors
        ]
    }


def quick_retry(func: F) -> F:
    """Quick retry decorator for fast operations."""
    return with_retry(**RetryConfigs.QUICK)(func)


def standard_retry(func: F) -> F:
    """Standard retry decorator for normal operations."""
    return with_retry(**RetryConfigs.STANDARD)(func)


def long_retry(func: F) -> F:
    """Long retry decorator for slow operations."""
    return with_retry(**RetryConfigs.LONG)(func)


def network_retry(func: F) -> F:
    """Network retry decorator for external API calls."""
    return with_retry(**RetryConfigs.NETWORK)(func)