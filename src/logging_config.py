"""
Structured Logging Configuration

Provides structured logging with JSON format support for production environments.
"""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """
    Structured log formatter that outputs JSON

    Features:
    - JSON formatted logs
    - Timestamp in ISO format
    - Structured fields (level, logger, message, etc.)
    - Extra context support
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON

        Args:
            record: Log record to format

        Returns:
            JSON formatted string
        """
        log_data: Dict[str, Any] = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }

        # Add standard fields
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        if hasattr(record, 'task_id'):
            log_data['task_id'] = record.task_id

        if hasattr(record, 'agent_name'):
            log_data['agent_name'] = record.agent_name

        # Add extra fields from record.__dict__
        reserved_attrs = {
            'name', 'msg', 'args', 'created', 'filename', 'funcName',
            'levelname', 'levelno', 'lineno', 'module', 'msecs',
            'message', 'pathname', 'process', 'processName',
            'relativeCreated', 'stack_info', 'thread', 'threadName',
            'exc_info', 'exc_text'
        }

        for key, value in record.__dict__.items():
            if key not in reserved_attrs and not key.startswith('_'):
                log_data[key] = value

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """
    Colored console formatter for development

    Features:
    - Color-coded log levels
    - Human-readable format
    - Timestamp and context
    """

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors

        Args:
            record: Log record to format

        Returns:
            Colored formatted string
        """
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']

        # Format: [2025-01-13 10:30:45] [INFO] [scheduler] Task completed
        formatted = (
            f"[{self.formatTime(record, '%Y-%m-%d %H:%M:%S')}] "
            f"{color}[{record.levelname:8s}]{reset} "
            f"[{record.name}] {record.getMessage()}"
        )

        if record.exc_info:
            formatted += '\n' + self.formatException(record.exc_info)

        return formatted


def setup_logging(
    level: str = "INFO",
    format_type: str = "colored",
    log_file: Optional[str] = None,
    enable_file_logging: bool = False
) -> logging.Logger:
    """
    Setup structured logging for the application

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Formatter type ("colored" for console, "json" for structured)
        log_file: Path to log file (optional)
        enable_file_logging: Enable file logging in addition to console

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logging(level="DEBUG", format_type="colored")
        >>> logger.info("Application started", extra={'version': '1.0.0'})
        >>> logger.error("Task failed", extra={'task_id': '123', 'error': 'timeout'})
    """
    # Create root logger
    logger = logging.getLogger("multi-agent-scheduler")
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))

    if format_type == "json":
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(ColoredFormatter())

    logger.addHandler(console_handler)

    # File handler (optional)
    if enable_file_logging or log_file:
        log_path = Path(log_file or "logs/app.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(StructuredFormatter())  # Always use JSON for files
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "multi-agent-scheduler") -> logging.Logger:
    """
    Get logger instance

    Args:
        name: Logger name (default: root logger)

    Returns:
        Logger instance

    Example:
        >>> logger = get_logger("scheduler")
        >>> logger.info("Task scheduled", extra={'task_id': 'task123'})
    """
    return logging.getLogger(name)


# Convenience functions for common logging patterns
class LogContext:
    """
    Context manager for adding context to logs

    Example:
        >>> with LogContext(task_id="task123", agent="claude"):
        >>>     logger.info("Processing task")  # Will include task_id and agent
    """

    def __init__(self, **kwargs):
        """Initialize log context

        Args:
            **kwargs: Context fields to add to logs
        """
        self.context = kwargs
        self.old_factory = None

    def __enter__(self):
        """Enter context"""
        old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record

        logging.setLogRecordFactory(record_factory)
        self.old_factory = old_factory
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context"""
        if self.old_factory:
            logging.setLogRecordFactory(self.old_factory)


# Initialize default logger (can be overridden)
_default_logger: Optional[logging.Logger] = None


def init_default_logger(
    level: str = "INFO",
    format_type: str = "colored"
) -> logging.Logger:
    """
    Initialize default logger for the application

    Args:
        level: Log level
        format_type: Formatter type

    Returns:
        Configured logger
    """
    global _default_logger
    _default_logger = setup_logging(level=level, format_type=format_type)
    return _default_logger


# Export commonly used functions
__all__ = [
    'setup_logging',
    'get_logger',
    'LogContext',
    'init_default_logger',
    'StructuredFormatter',
    'ColoredFormatter'
]
