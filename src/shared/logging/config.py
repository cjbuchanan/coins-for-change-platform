"""Structured logging configuration with OpenTelemetry integration."""

import logging
import sys
from typing import Any, Dict

import structlog
from opentelemetry import trace

from src.shared.config import get_settings


def setup_logging() -> None:
    """Configure structured logging with OpenTelemetry correlation."""
    settings = get_settings()
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level),
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            # Add OpenTelemetry trace context
            add_trace_context,
            # Add timestamp
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            # Add service name
            add_service_context,
            # JSON formatting for production, pretty for development
            structlog.dev.ConsoleRenderer() if settings.debug 
            else structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def add_trace_context(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add OpenTelemetry trace context to log entries."""
    span = trace.get_current_span()
    if span:
        span_context = span.get_span_context()
        if span_context.is_valid:
            event_dict["trace_id"] = format(span_context.trace_id, "032x")
            event_dict["span_id"] = format(span_context.span_id, "016x")
    
    return event_dict


def add_service_context(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add service context to log entries."""
    import os
    
    service_name = os.getenv("SERVICE_NAME", "unknown")
    event_dict["service"] = service_name
    
    return event_dict


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)