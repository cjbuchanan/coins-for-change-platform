"""
Circuit breaker pattern implementation for external service resilience.
"""
import asyncio
import logging
import time
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

logger = logging.getLogger(__name__)

F = TypeVar('F', bound=Callable[..., Any])


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """
    Circuit breaker implementation with configurable failure thresholds and recovery.
    """
    
    def __init__(
        self,
        name: str,
        fail_max: int = 5,
        reset_timeout: int = 60,
        success_threshold: int = 1,
        excluded_exceptions: Optional[List[type]] = None
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Circuit breaker name for identification
            fail_max: Maximum consecutive failures before opening
            reset_timeout: Seconds to wait before attempting reset
            success_threshold: Consecutive successes needed to close from half-open
            excluded_exceptions: Exception types that don't count as failures
        """
        self.name = name
        self.fail_max = fail_max
        self.reset_timeout = reset_timeout
        self.success_threshold = success_threshold
        self.excluded_exceptions = excluded_exceptions or []
        
        # State tracking
        self._state = CircuitBreakerState.CLOSED
        self._fail_counter = 0
        self._success_counter = 0
        self._last_failure_time: Optional[float] = None
        self._lock = asyncio.Lock()
        
        # Metrics
        self._total_requests = 0
        self._total_failures = 0
        self._total_successes = 0
        self._state_changes = 0
        
        logger.info(f"Circuit breaker '{name}' initialized")
    
    @property
    def state(self) -> CircuitBreakerState:
        """Get current circuit breaker state."""
        return self._state
    
    @property
    def fail_counter(self) -> int:
        """Get current failure counter."""
        return self._fail_counter
    
    @property
    def success_counter(self) -> int:
        """Get current success counter."""
        return self._success_counter
    
    @property
    def metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics."""
        return {
            "name": self.name,
            "state": self._state.value,
            "fail_counter": self._fail_counter,
            "success_counter": self._success_counter,
            "total_requests": self._total_requests,
            "total_failures": self._total_failures,
            "total_successes": self._total_successes,
            "state_changes": self._state_changes,
            "failure_rate": self._total_failures / max(self._total_requests, 1),
            "last_failure_time": self._last_failure_time
        }
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        if self._state != CircuitBreakerState.OPEN:
            return False
        
        if self._last_failure_time is None:
            return False
        
        return time.time() - self._last_failure_time >= self.reset_timeout
    
    def _is_excluded_exception(self, exception: Exception) -> bool:
        """Check if exception should be excluded from failure counting."""
        return any(isinstance(exception, exc_type) for exc_type in self.excluded_exceptions)
    
    async def _change_state(self, new_state: CircuitBreakerState) -> None:
        """Change circuit breaker state and log the transition."""
        old_state = self._state
        self._state = new_state
        self._state_changes += 1
        
        if old_state != new_state:
            logger.info(f"Circuit breaker '{self.name}' state changed: {old_state.value} -> {new_state.value}")
            
            # Reset counters on state change
            if new_state == CircuitBreakerState.CLOSED:
                self._fail_counter = 0
                self._success_counter = 0
            elif new_state == CircuitBreakerState.HALF_OPEN:
                self._success_counter = 0
    
    async def _on_success(self) -> None:
        """Handle successful operation."""
        async with self._lock:
            self._total_requests += 1
            self._total_successes += 1
            
            if self._state == CircuitBreakerState.HALF_OPEN:
                self._success_counter += 1
                if self._success_counter >= self.success_threshold:
                    await self._change_state(CircuitBreakerState.CLOSED)
            elif self._state == CircuitBreakerState.CLOSED:
                self._fail_counter = 0  # Reset failure counter on success
    
    async def _on_failure(self, exception: Exception) -> None:
        """Handle failed operation."""
        if self._is_excluded_exception(exception):
            logger.debug(f"Circuit breaker '{self.name}' excluding exception: {type(exception).__name__}")
            return
        
        async with self._lock:
            self._total_requests += 1
            self._total_failures += 1
            self._last_failure_time = time.time()
            
            if self._state == CircuitBreakerState.CLOSED:
                self._fail_counter += 1
                if self._fail_counter >= self.fail_max:
                    await self._change_state(CircuitBreakerState.OPEN)
            elif self._state == CircuitBreakerState.HALF_OPEN:
                await self._change_state(CircuitBreakerState.OPEN)
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: If circuit is open
        """
        async with self._lock:
            # Check if we should attempt reset
            if self._should_attempt_reset():
                await self._change_state(CircuitBreakerState.HALF_OPEN)
            
            # Reject if circuit is open
            if self._state == CircuitBreakerState.OPEN:
                raise CircuitBreakerError(f"Circuit breaker '{self.name}' is open")
        
        # Execute function
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            await self._on_success()
            return result
            
        except Exception as e:
            await self._on_failure(e)
            raise
    
    def close(self) -> None:
        """Manually close the circuit breaker."""
        asyncio.create_task(self._change_state(CircuitBreakerState.CLOSED))
    
    def open(self) -> None:
        """Manually open the circuit breaker."""
        asyncio.create_task(self._change_state(CircuitBreakerState.OPEN))
    
    def half_open(self) -> None:
        """Manually set circuit breaker to half-open state."""
        asyncio.create_task(self._change_state(CircuitBreakerState.HALF_OPEN))


class CircuitBreakerManager:
    """
    Manager for multiple circuit breakers with centralized configuration.
    """
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._default_config = {
            "fail_max": 5,
            "reset_timeout": 60,
            "success_threshold": 1,
            "excluded_exceptions": []
        }
    
    def get_breaker(
        self,
        name: str,
        fail_max: Optional[int] = None,
        reset_timeout: Optional[int] = None,
        success_threshold: Optional[int] = None,
        excluded_exceptions: Optional[List[type]] = None
    ) -> CircuitBreaker:
        """
        Get or create a circuit breaker with the given name.
        
        Args:
            name: Circuit breaker name
            fail_max: Maximum failures before opening (uses default if None)
            reset_timeout: Reset timeout in seconds (uses default if None)
            success_threshold: Success threshold for closing (uses default if None)
            excluded_exceptions: Exceptions to exclude (uses default if None)
            
        Returns:
            CircuitBreaker instance
        """
        if name not in self._breakers:
            config = self._default_config.copy()
            if fail_max is not None:
                config["fail_max"] = fail_max
            if reset_timeout is not None:
                config["reset_timeout"] = reset_timeout
            if success_threshold is not None:
                config["success_threshold"] = success_threshold
            if excluded_exceptions is not None:
                config["excluded_exceptions"] = excluded_exceptions
            
            self._breakers[name] = CircuitBreaker(name=name, **config)
        
        return self._breakers[name]
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all circuit breakers."""
        return {name: breaker.metrics for name, breaker in self._breakers.items()}
    
    def reset_all(self) -> None:
        """Reset all circuit breakers to closed state."""
        for breaker in self._breakers.values():
            breaker.close()


# Global circuit breaker manager
_circuit_breaker_manager = CircuitBreakerManager()


def circuit_breaker(
    name: str,
    fail_max: int = 5,
    reset_timeout: int = 60,
    success_threshold: int = 1,
    excluded_exceptions: Optional[List[type]] = None
) -> Callable[[F], F]:
    """
    Decorator to apply circuit breaker pattern to functions.
    
    Args:
        name: Circuit breaker name
        fail_max: Maximum failures before opening
        reset_timeout: Reset timeout in seconds
        success_threshold: Success threshold for closing
        excluded_exceptions: Exception types to exclude from failures
        
    Returns:
        Decorated function with circuit breaker protection
    """
    def decorator(func: F) -> F:
        breaker = _circuit_breaker_manager.get_breaker(
            name=name,
            fail_max=fail_max,
            reset_timeout=reset_timeout,
            success_threshold=success_threshold,
            excluded_exceptions=excluded_exceptions
        )
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return asyncio.run(breaker.call(func, *args, **kwargs))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def get_circuit_breaker_metrics() -> Dict[str, Dict[str, Any]]:
    """Get metrics for all circuit breakers."""
    return _circuit_breaker_manager.get_all_metrics()