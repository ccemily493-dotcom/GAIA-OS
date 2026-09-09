"""Structured logging configuration for GAIA OS with correlation ID propagation."""

import contextvars
import logging
import sys
from typing import cast

import structlog

# ContextVar for async-safe correlation ID propagation across await boundaries
correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default=""
)


def add_correlation_id(
    _logger: structlog.types.WrappedLogger,
    _method_name: str,
    event_dict: structlog.types.EventDict,
) -> structlog.types.EventDict:
    """Injects current context's correlation_id into every log record."""
    if cid := correlation_id_var.get():
        event_dict["correlationId"] = cid
    return event_dict


def configure_logging(level: str = "INFO") -> None:
    """Configures structlog for GAIA OS."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            add_correlation_id,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(colors=True),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )


def get_logger(name: str = "gaia") -> structlog.BoundLogger:
    """Returns a bound structlog logger."""
    return cast(structlog.BoundLogger, structlog.get_logger(name))
