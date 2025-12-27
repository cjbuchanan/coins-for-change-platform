"""Unit tests for external service resilience components."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Import the modules directly to avoid dependency issues in tests
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.shared.external.circuit_breaker import CircuitBreaker, CircuitBreakerError, CircuitBreakerState
from src.shared.external.retry import RetryManager, RetryError
from src.shared.external.monitoring import ServiceMonitor, AlertSeverity


class TestCircuitBreaker:
    """Test circuit breaker functionality."""
    
    @pytest.mark.asyncio
    async def test_successful_calls(self):
        """Test that successful calls work normally."""
        cb = CircuitBreaker("test", fail_max=3)
        
        async def success_func():
            return "success"
        
        result = await cb.call(success_func)
        assert result == "success"
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.fail_counter == 0
        assert cb.success_counter == 0  # Only incremented in half-open state
    
    @pytest.mark.asyncio
    async def test_circuit_opens_after_failures(self):
        """Test that circuit opens after max failures."""
        cb = CircuitBreaker("test", fail_max=2)
        
        async def fail_func():
            raise Exception("Test failure")
        
        # First failure
        with pytest.raises(Exception, match="Test failure"):
            await cb.call(fail_func)
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.fail_counter == 1
        
        # Second failure - should open circuit
        with pytest.raises(Exception, match="Test failure"):
            await cb.call(fail_func)
        assert cb.state == CircuitBreakerState.OPEN
        assert cb.fail_counter == 2
        
        # Third call should be blocked
        with pytest.raises(CircuitBreakerError):
            await cb.call(fail_func)
    
    @pytest.mark.asyncio
    async def test_circuit_reset_after_timeout(self):
        """Test that circuit resets after timeout."""
        cb = CircuitBreaker("test", fail_max=1, reset_timeout=0.1)
        
        async def fail_func():
            raise Exception("Test failure")
        
        async def success_func():
            return "success"
        
        # Trigger failure to open circuit
        with pytest.raises(Exception):
            await cb.call(fail_func)
        assert cb.state == CircuitBreakerState.OPEN
        
        # Wait for reset timeout
        await asyncio.sleep(0.15)
        
        # Should transition to half-open and allow call
        result = await cb.call(success_func)
        assert result == "success"
        assert cb.state == CircuitBreakerState.CLOSED
    
    @pytest.mark.asyncio
    async def test_half_open_success_threshold(self):
        """Test success threshold in half-open state."""
        cb = CircuitBreaker("test", fail_max=1, reset_timeout=0.1, success_threshold=2)
        
        async def fail_func():
            raise Exception("Test failure")
        
        async def success_func():
            return "success"
        
        # Open circuit
        with pytest.raises(Exception):
            await cb.call(fail_func)
        
        # Wait for reset
        await asyncio.sleep(0.15)
        
        # First success in half-open
        await cb.call(success_func)
        assert cb.state == CircuitBreakerState.HALF_OPEN
        assert cb.success_counter == 1
        
        # Second success should close circuit
        await cb.call(success_func)
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.success_counter == 0  # Reset on state change
    
    @pytest.mark.asyncio
    async def test_excluded_exceptions(self):
        """Test that excluded exceptions don't count as failures."""
        class BusinessError(Exception):
            pass
        
        cb = CircuitBreaker("test", fail_max=1, excluded_exceptions=[BusinessError])
        
        async def business_error_func():
            raise BusinessError("Business logic error")
        
        # Business error should not count as failure
        with pytest.raises(BusinessError):
            await cb.call(business_error_func)
        
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.fail_counter == 0
    
    def test_metrics(self):
        """Test circuit breaker metrics."""
        cb = CircuitBreaker("test", fail_max=5)
        metrics = cb.metrics
        
        assert metrics["name"] == "test"
        assert metrics["state"] == CircuitBreakerState.CLOSED.value
        assert metrics["fail_counter"] == 0
        assert metrics["success_counter"] == 0
        assert metrics["total_requests"] == 0
        assert metrics["failure_rate"] == 0.0


class TestRetryManager:
    """Test retry manager functionality."""
    
    @pytest.mark.asyncio
    async def test_successful_call_no_retry(self):
        """Test that successful calls don't trigger retries."""
        retry_manager = RetryManager(max_retries=3, base_delay=0.1)
        
        async def success_func():
            return "success"
        
        result = await retry_manager.execute_with_retry(success_func)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """Test retry logic on failures."""
        retry_manager = RetryManager(max_retries=2, base_delay=0.01)
        
        call_count = 0
        
        async def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success after retries"
        
        result = await retry_manager.execute_with_retry(fail_then_succeed)
        assert result == "success after retries"
        assert call_count == 3  # Initial + 2 retries
    
    @pytest.mark.asyncio
    async def test_retry_exhaustion(self):
        """Test behavior when all retries are exhausted."""
        retry_manager = RetryManager(max_retries=2, base_delay=0.01)
        
        async def always_fail():
            raise Exception("Always fails")
        
        with pytest.raises(RetryError) as exc_info:
            await retry_manager.execute_with_retry(always_fail)
        
        assert exc_info.value.attempts == 3  # Initial + 2 retries
        assert "Always fails" in str(exc_info.value.last_exception)
    
    @pytest.mark.asyncio
    async def test_non_retryable_exception(self):
        """Test that non-retryable exceptions don't trigger retries."""
        class NonRetryableError(Exception):
            pass
        
        retry_manager = RetryManager(
            max_retries=3,
            base_delay=0.01,
            retryable_exceptions=[ConnectionError]
        )
        
        call_count = 0
        
        async def non_retryable_fail():
            nonlocal call_count
            call_count += 1
            raise NonRetryableError("Should not retry")
        
        with pytest.raises(RetryError):
            await retry_manager.execute_with_retry(non_retryable_fail)
        
        assert call_count == 1  # Should not retry
    
    def test_delay_calculation(self):
        """Test exponential backoff delay calculation."""
        retry_manager = RetryManager(
            base_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0,
            jitter=False
        )
        
        # Test exponential backoff
        assert retry_manager._calculate_delay(0) == 1.0  # 1.0 * 2^0
        assert retry_manager._calculate_delay(1) == 2.0  # 1.0 * 2^1
        assert retry_manager._calculate_delay(2) == 4.0  # 1.0 * 2^2
        
        # Test max delay cap
        assert retry_manager._calculate_delay(10) == 10.0  # Capped at max_delay


class TestServiceMonitor:
    """Test service monitoring functionality."""
    
    @pytest.mark.asyncio
    async def test_successful_health_check(self):
        """Test successful health check updates metrics correctly."""
        health_check_mock = AsyncMock(return_value={"status": "healthy"})
        
        monitor = ServiceMonitor(
            service_name="test_service",
            health_check_func=health_check_mock,
            check_interval=1
        )
        
        # Perform health check
        result = await monitor._perform_health_check()
        
        assert result is True
        assert monitor.metrics.is_healthy is True
        assert monitor.metrics.success_count == 1
        assert monitor.metrics.error_count == 0
        assert monitor.metrics.consecutive_failures == 0
        
        health_check_mock.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_failed_health_check(self):
        """Test failed health check updates metrics correctly."""
        health_check_mock = AsyncMock(side_effect=Exception("Health check failed"))
        
        monitor = ServiceMonitor(
            service_name="test_service",
            health_check_func=health_check_mock,
            check_interval=1
        )
        
        # Perform health check
        result = await monitor._perform_health_check()
        
        assert result is False
        assert monitor.metrics.is_healthy is False
        assert monitor.metrics.success_count == 0
        assert monitor.metrics.error_count == 1
        assert monitor.metrics.consecutive_failures == 1
    
    @pytest.mark.asyncio
    async def test_alert_on_failure_threshold(self):
        """Test that alerts are sent when failure threshold is reached."""
        health_check_mock = AsyncMock(side_effect=Exception("Health check failed"))
        
        monitor = ServiceMonitor(
            service_name="test_service",
            health_check_func=health_check_mock,
            check_interval=1,
            failure_threshold=2
        )
        
        # Mock alert handler
        alert_handler_mock = AsyncMock()
        monitor.add_alert_handler(alert_handler_mock)
        
        # First failure - no alert yet
        await monitor._perform_health_check()
        assert alert_handler_mock.handle_alert.call_count == 1  # Health status change alert
        
        # Second failure - should trigger threshold alert
        await monitor._perform_health_check()
        assert alert_handler_mock.handle_alert.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_response_time_threshold_alert(self):
        """Test alert on response time threshold."""
        # Mock a slow health check
        async def slow_health_check():
            await asyncio.sleep(0.1)  # 100ms delay
            return {"status": "healthy"}
        
        monitor = ServiceMonitor(
            service_name="test_service",
            health_check_func=slow_health_check,
            check_interval=1,
            response_time_threshold=50.0  # 50ms threshold
        )
        
        # Mock alert handler
        alert_handler_mock = AsyncMock()
        monitor.add_alert_handler(alert_handler_mock)
        
        # Perform health check
        await monitor._perform_health_check()
        
        # Should have triggered response time alert
        alert_handler_mock.handle_alert.assert_called()
        
        # Check that the alert was for response time
        call_args = alert_handler_mock.handle_alert.call_args[0][0]
        assert "Response time" in call_args.message
        assert call_args.severity == AlertSeverity.WARNING
    
    def test_metrics_collection(self):
        """Test that metrics are collected correctly."""
        health_check_mock = MagicMock(return_value={"status": "healthy"})
        
        monitor = ServiceMonitor(
            service_name="test_service",
            health_check_func=health_check_mock,
            check_interval=1
        )
        
        metrics = monitor.get_metrics()
        
        assert metrics["service_name"] == "test_service"
        assert metrics["is_healthy"] is True
        assert metrics["error_count"] == 0
        assert metrics["success_count"] == 0
        assert metrics["total_requests"] == 0
        assert metrics["error_rate"] == 0.0
        assert metrics["consecutive_failures"] == 0


@pytest.mark.asyncio
async def test_integration_circuit_breaker_with_retry():
    """Test circuit breaker and retry working together."""
    from src.shared.external.circuit_breaker import circuit_breaker
    from src.shared.external.retry import with_retry
    
    call_count = 0
    
    @circuit_breaker("integration_test", fail_max=2, reset_timeout=0.1)
    @with_retry(max_retries=1, base_delay=0.01)
    async def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 4:
            raise Exception("Flaky failure")
        return "success"
    
    # First call: fails, retries, fails again, circuit breaker records 2 failures
    with pytest.raises(RetryError):
        await flaky_function()
    
    # Second call: circuit breaker should be open
    with pytest.raises(CircuitBreakerError):
        await flaky_function()
    
    # Wait for circuit breaker reset
    await asyncio.sleep(0.15)
    
    # Third call: should succeed after retry
    result = await flaky_function()
    assert result == "success"