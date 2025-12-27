"""
Connection monitoring and alerting for service availability.
"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Represents a monitoring alert."""
    service_name: str
    severity: AlertSeverity
    message: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        return f"[{self.severity.value.upper()}] {self.service_name}: {self.message}"


@dataclass
class ServiceMetrics:
    """Service health and performance metrics."""
    service_name: str
    is_healthy: bool = True
    response_time_ms: float = 0.0
    error_count: int = 0
    success_count: int = 0
    last_check: float = field(default_factory=time.time)
    uptime_percentage: float = 100.0
    consecutive_failures: int = 0
    
    @property
    def total_requests(self) -> int:
        return self.error_count + self.success_count
    
    @property
    def error_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.error_count / self.total_requests


class AlertHandler:
    """Base class for alert handlers."""
    
    async def handle_alert(self, alert: Alert) -> None:
        """Handle an alert."""
        raise NotImplementedError


class LogAlertHandler(AlertHandler):
    """Alert handler that logs alerts."""
    
    async def handle_alert(self, alert: Alert) -> None:
        """Log the alert with appropriate level."""
        log_level = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.ERROR: logging.ERROR,
            AlertSeverity.CRITICAL: logging.CRITICAL
        }.get(alert.severity, logging.INFO)
        
        logger.log(log_level, str(alert))


class ServiceMonitor:
    """
    Monitor service health and generate alerts based on configurable thresholds.
    """
    
    def __init__(
        self,
        service_name: str,
        health_check_func: Callable[[], Any],
        check_interval: int = 30,
        failure_threshold: int = 3,
        response_time_threshold: float = 1000.0,  # milliseconds
        error_rate_threshold: float = 0.1  # 10%
    ):
        """
        Initialize service monitor.
        
        Args:
            service_name: Name of the service to monitor
            health_check_func: Function to call for health checks
            check_interval: Seconds between health checks
            failure_threshold: Consecutive failures before alerting
            response_time_threshold: Response time threshold in milliseconds
            error_rate_threshold: Error rate threshold (0.0 to 1.0)
        """
        self.service_name = service_name
        self.health_check_func = health_check_func
        self.check_interval = check_interval
        self.failure_threshold = failure_threshold
        self.response_time_threshold = response_time_threshold
        self.error_rate_threshold = error_rate_threshold
        
        self.metrics = ServiceMetrics(service_name=service_name)
        self.alert_handlers: List[AlertHandler] = []
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Add default log handler
        self.add_alert_handler(LogAlertHandler())
    
    def add_alert_handler(self, handler: AlertHandler) -> None:
        """Add an alert handler."""
        self.alert_handlers.append(handler)
    
    async def _send_alert(self, severity: AlertSeverity, message: str, metadata: Dict[str, Any] = None) -> None:
        """Send an alert to all handlers."""
        alert = Alert(
            service_name=self.service_name,
            severity=severity,
            message=message,
            metadata=metadata or {}
        )
        
        for handler in self.alert_handlers:
            try:
                await handler.handle_alert(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
    
    async def _perform_health_check(self) -> bool:
        """Perform health check and update metrics."""
        start_time = time.time()
        
        try:
            # Call health check function
            if asyncio.iscoroutinefunction(self.health_check_func):
                result = await self.health_check_func()
            else:
                result = self.health_check_func()
            
            # Calculate response time
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            self.metrics.response_time_ms = response_time
            self.metrics.last_check = time.time()
            
            # Determine if healthy based on result
            if isinstance(result, dict):
                is_healthy = result.get("status") == "healthy"
            elif isinstance(result, bool):
                is_healthy = result
            else:
                is_healthy = True  # Assume healthy if no exception
            
            # Update metrics
            if is_healthy:
                self.metrics.success_count += 1
                self.metrics.consecutive_failures = 0
                
                # Check response time threshold
                if response_time > self.response_time_threshold:
                    await self._send_alert(
                        AlertSeverity.WARNING,
                        f"Response time ({response_time:.2f}ms) exceeds threshold ({self.response_time_threshold}ms)",
                        {"response_time_ms": response_time, "threshold_ms": self.response_time_threshold}
                    )
            else:
                self.metrics.error_count += 1
                self.metrics.consecutive_failures += 1
                
                # Check failure threshold
                if self.metrics.consecutive_failures >= self.failure_threshold:
                    await self._send_alert(
                        AlertSeverity.ERROR,
                        f"Service unhealthy for {self.metrics.consecutive_failures} consecutive checks",
                        {"consecutive_failures": self.metrics.consecutive_failures}
                    )
            
            # Update health status
            was_healthy = self.metrics.is_healthy
            self.metrics.is_healthy = is_healthy
            
            # Alert on health status change
            if was_healthy and not is_healthy:
                await self._send_alert(
                    AlertSeverity.ERROR,
                    "Service became unhealthy",
                    {"previous_status": "healthy", "current_status": "unhealthy"}
                )
            elif not was_healthy and is_healthy:
                await self._send_alert(
                    AlertSeverity.INFO,
                    "Service recovered",
                    {"previous_status": "unhealthy", "current_status": "healthy"}
                )
            
            # Check error rate threshold
            if self.metrics.total_requests > 10:  # Only check after some requests
                error_rate = self.metrics.error_rate
                if error_rate > self.error_rate_threshold:
                    await self._send_alert(
                        AlertSeverity.WARNING,
                        f"Error rate ({error_rate:.2%}) exceeds threshold ({self.error_rate_threshold:.2%})",
                        {"error_rate": error_rate, "threshold": self.error_rate_threshold}
                    )
            
            return is_healthy
            
        except Exception as e:
            self.metrics.error_count += 1
            self.metrics.consecutive_failures += 1
            self.metrics.is_healthy = False
            self.metrics.last_check = time.time()
            
            await self._send_alert(
                AlertSeverity.ERROR,
                f"Health check failed: {str(e)}",
                {"exception": str(e), "exception_type": type(e).__name__}
            )
            
            return False
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        logger.info(f"Starting monitoring for service '{self.service_name}'")
        
        while self._running:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop for '{self.service_name}': {e}")
                await asyncio.sleep(self.check_interval)
        
        logger.info(f"Monitoring stopped for service '{self.service_name}'")
    
    def start_monitoring(self) -> None:
        """Start monitoring the service."""
        if self._running:
            logger.warning(f"Monitoring already running for service '{self.service_name}'")
            return
        
        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info(f"Started monitoring for service '{self.service_name}'")
    
    async def stop_monitoring(self) -> None:
        """Stop monitoring the service."""
        if not self._running:
            return
        
        self._running = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None
        
        logger.info(f"Stopped monitoring for service '{self.service_name}'")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current service metrics."""
        return {
            "service_name": self.metrics.service_name,
            "is_healthy": self.metrics.is_healthy,
            "response_time_ms": self.metrics.response_time_ms,
            "error_count": self.metrics.error_count,
            "success_count": self.metrics.success_count,
            "total_requests": self.metrics.total_requests,
            "error_rate": self.metrics.error_rate,
            "uptime_percentage": self.metrics.uptime_percentage,
            "consecutive_failures": self.metrics.consecutive_failures,
            "last_check": self.metrics.last_check
        }

class MonitoringManager:
    """
    Manager for multiple service monitors with centralized control.
    """
    
    def __init__(self):
        self._monitors: Dict[str, ServiceMonitor] = {}
        self._global_alert_handlers: List[AlertHandler] = []
    
    def add_global_alert_handler(self, handler: AlertHandler) -> None:
        """Add a global alert handler that receives alerts from all monitors."""
        self._global_alert_handlers.append(handler)
        
        # Add to existing monitors
        for monitor in self._monitors.values():
            monitor.add_alert_handler(handler)
    
    def create_monitor(
        self,
        service_name: str,
        health_check_func: Callable[[], Any],
        check_interval: int = 30,
        failure_threshold: int = 3,
        response_time_threshold: float = 1000.0,
        error_rate_threshold: float = 0.1,
        auto_start: bool = True
    ) -> ServiceMonitor:
        """
        Create and optionally start a service monitor.
        
        Args:
            service_name: Name of the service to monitor
            health_check_func: Function to call for health checks
            check_interval: Seconds between health checks
            failure_threshold: Consecutive failures before alerting
            response_time_threshold: Response time threshold in milliseconds
            error_rate_threshold: Error rate threshold (0.0 to 1.0)
            auto_start: Whether to start monitoring immediately
            
        Returns:
            ServiceMonitor instance
        """
        if service_name in self._monitors:
            logger.warning(f"Monitor for service '{service_name}' already exists")
            return self._monitors[service_name]
        
        monitor = ServiceMonitor(
            service_name=service_name,
            health_check_func=health_check_func,
            check_interval=check_interval,
            failure_threshold=failure_threshold,
            response_time_threshold=response_time_threshold,
            error_rate_threshold=error_rate_threshold
        )
        
        # Add global alert handlers
        for handler in self._global_alert_handlers:
            monitor.add_alert_handler(handler)
        
        self._monitors[service_name] = monitor
        
        if auto_start:
            monitor.start_monitoring()
        
        return monitor
    
    def get_monitor(self, service_name: str) -> Optional[ServiceMonitor]:
        """Get a monitor by service name."""
        return self._monitors.get(service_name)
    
    def start_all_monitoring(self) -> None:
        """Start monitoring for all services."""
        for monitor in self._monitors.values():
            monitor.start_monitoring()
    
    async def stop_all_monitoring(self) -> None:
        """Stop monitoring for all services."""
        stop_tasks = [monitor.stop_monitoring() for monitor in self._monitors.values()]
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all monitored services."""
        return {name: monitor.get_metrics() for name, monitor in self._monitors.items()}
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary."""
        total_services = len(self._monitors)
        healthy_services = sum(1 for monitor in self._monitors.values() if monitor.metrics.is_healthy)
        
        return {
            "total_services": total_services,
            "healthy_services": healthy_services,
            "unhealthy_services": total_services - healthy_services,
            "overall_health": "healthy" if healthy_services == total_services else "degraded",
            "health_percentage": (healthy_services / max(total_services, 1)) * 100
        }


# Global monitoring manager instance
_monitoring_manager = MonitoringManager()


def get_monitoring_manager() -> MonitoringManager:
    """Get the global monitoring manager."""
    return _monitoring_manager


async def setup_default_monitoring() -> None:
    """Set up default monitoring for core services."""
    from .opensearch import get_opensearch_health
    from .redis import get_redis_health
    from ..database.connection import get_database_health
    
    manager = get_monitoring_manager()
    
    # Monitor database
    manager.create_monitor(
        service_name="database",
        health_check_func=get_database_health,
        check_interval=30,
        failure_threshold=3,
        response_time_threshold=500.0,  # 500ms for database
        error_rate_threshold=0.05  # 5% for database
    )
    
    # Monitor Redis
    manager.create_monitor(
        service_name="redis",
        health_check_func=get_redis_health,
        check_interval=30,
        failure_threshold=3,
        response_time_threshold=200.0,  # 200ms for Redis
        error_rate_threshold=0.1  # 10% for Redis
    )
    
    # Monitor OpenSearch
    manager.create_monitor(
        service_name="opensearch",
        health_check_func=get_opensearch_health,
        check_interval=60,  # Less frequent for search
        failure_threshold=3,
        response_time_threshold=2000.0,  # 2s for search operations
        error_rate_threshold=0.15  # 15% for search
    )
    
    logger.info("Default service monitoring configured")


async def close_monitoring() -> None:
    """Close all monitoring and cleanup resources."""
    await _monitoring_manager.stop_all_monitoring()