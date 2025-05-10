import logging
import sys
import os


def configure_logging(debug=False):
    """
    Configure logging for the entire application.

    Args:
        debug: Whether to enable debug logging or not
    """
    # Set log level based on debug flag or environment variable
    log_level = (
        logging.DEBUG if (debug or os.environ.get("DEBUG") == "1") else logging.INFO
    )

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)

    # Disable propagation for third-party loggers
    logging.getLogger("uvicorn").propagate = False

    return root_logger


def get_logger(name):
    """
    Get a logger for a module.

    Args:
        name: Module name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
