"""
Central logging configuration for the Ansible PlayTest framework.

This module provides a centralized logging configuration for the entire project.
It configures a root logger with customizable handlers and formatters.
All modules in the project should import and use this module for logging.

Example:
    from ansible_playtest.utils.logger import get_logger

    # Get a logger with the current module name
    logger = get_logger(__name__)

    # Use the logger
    logger.info("This is an info message")
    logger.debug("This is a debug message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
"""

import logging
import os
import sys
from typing import Optional, Dict, Any

# Define constants for the project
PROJECT_NAME = "ansible_playtest"

# Default log format
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Default log level
DEFAULT_LOG_LEVEL = logging.INFO

# Keep track of whether the logger has been initialized
_logger_initialized = False

# Store configuration
_config: Dict[str, Any] = {
    "level": DEFAULT_LOG_LEVEL,
    "format": DEFAULT_LOG_FORMAT,
    "handlers": [],
}


def setup_logging(
    level: Optional[int] = None,
    format_str: Optional[str] = None,
    log_file: Optional[str] = None,
    use_console: bool = True,
) -> None:
    """
    Set up the logging configuration for the entire project.

    Args:
        level: The logging level to use. If None, uses the value from
              ANSIBLE_PLAYTEST_LOG_LEVEL env var or DEFAULT_LOG_LEVEL.
        format_str: The log format string to use. If None, uses the value from
                   ANSIBLE_PLAYTEST_LOG_FORMAT env var or DEFAULT_LOG_FORMAT.
        log_file: Path to a file where logs should be written. If None, no file
                 logging is enabled.
        use_console: Whether to log to the console. Default is True.
    """
    global _logger_initialized, _config

    if _logger_initialized:
        # Logger already initialized, reconfigure it
        logging.getLogger(PROJECT_NAME).handlers = []

    # Get log level from environment or use default/provided value
    env_level = os.environ.get("ANSIBLE_PLAYTEST_LOG_LEVEL", "")

    level = DEFAULT_LOG_LEVEL

    if env_level:
        try:
            level = getattr(logging, env_level.upper())
        except (AttributeError, TypeError):
            level = DEFAULT_LOG_LEVEL

    # Get log format from environment or use default/provided value
    format_str = format_str or os.environ.get(
        "ANSIBLE_PLAYTEST_LOG_FORMAT", DEFAULT_LOG_FORMAT
    )

    # Store the configuration
    _config["level"] = level
    _config["format"] = format_str
    _config["handlers"] = []

    # Configure the root logger for the project
    logger = logging.getLogger(PROJECT_NAME)
    logger.setLevel(level)

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create formatter
    formatter = logging.Formatter(format_str)

    # Add console handler if requested
    if use_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        _config["handlers"].append(("console", console_handler))

    # Add file handler if a log file is specified
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            _config["handlers"].append(("file", file_handler))
        except (IOError, PermissionError) as e:
            # Log to console that we couldn't create the file handler
            if use_console:
                print(f"Warning: Could not create log file at {log_file}: {str(e)}")

    # Make sure the logger doesn't propagate to the root logger
    logger.propagate = False

    _logger_initialized = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given name.

    Args:
        name: The name of the logger, typically __name__

    Returns:
        A Logger instance configured according to the project settings
    """
    # Initialize logging if it hasn't been done yet
    if not _logger_initialized:
        setup_logging()

    # If the name starts with the project name, use it directly
    if name.startswith(PROJECT_NAME):
        return logging.getLogger(name)

    # Otherwise, prefix it with the project name
    return logging.getLogger(f"{PROJECT_NAME}.{name}")


def get_log_config() -> Dict[str, Any]:
    """
    Get the current logging configuration.

    Returns:
        A dictionary containing the current logging configuration
    """
    return _config.copy()


def set_log_level(level: int) -> None:
    """
    Set the log level for all project loggers.

    Args:
        level: The new logging level
    """
    global _config

    _config["level"] = level

    # Set the level for the project logger
    logging.getLogger(PROJECT_NAME).setLevel(level)


# Initialize logging with default settings when the module is imported
if not _logger_initialized:
    # Check for environment variables
    env_log_file = os.environ.get("ANSIBLE_PLAYTEST_LOG_FILE")
    env_console = os.environ.get("ANSIBLE_PLAYTEST_LOG_CONSOLE", "").lower() != "false"

    setup_logging(log_file=env_log_file, use_console=env_console)
