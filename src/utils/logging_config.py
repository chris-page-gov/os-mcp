import logging
import sys
import os
import re


class APIKeySanitisingFilter(logging.Filter):
    """Filter to sanitise API keys from log messages"""

    def __init__(self):
        super().__init__()
        self.patterns = [
            r"[?&]key=[^&\s]*",
            r"[?&]api_key=[^&\s]*",
            r"[?&]apikey=[^&\s]*",
            r"[?&]token=[^&\s]*",
        ]

    def filter(self, record: logging.LogRecord) -> bool:
        """Sanitise the log record message"""
        if hasattr(record, "msg") and isinstance(record.msg, str):
            record.msg = self._sanitise_text(record.msg)

        if hasattr(record, "args") and record.args:
            sanitised_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    sanitised_args.append(self._sanitise_text(arg))
                else:
                    sanitised_args.append(arg)
            record.args = tuple(sanitised_args)

        return True

    def _sanitise_text(self, text: str) -> str:
        """Remove API keys from text"""
        sanitised = text
        for pattern in self.patterns:
            sanitised = re.sub(pattern, "", sanitised, flags=re.IGNORECASE)

        sanitised = re.sub(r"[?&]$", "", sanitised)
        sanitised = re.sub(r"&{2,}", "&", sanitised)
        sanitised = re.sub(r"\?&", "?", sanitised)

        return sanitised


def configure_logging(debug: bool = False) -> logging.Logger:
    """
    Configure logging for the entire application.

    Args:
        debug: Whether to enable debug logging or not
    """
    log_level = (
        logging.DEBUG if (debug or os.environ.get("DEBUG") == "1") else logging.INFO
    )

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    api_key_filter = APIKeySanitisingFilter()
    console_handler.addFilter(api_key_filter)

    root_logger.addHandler(console_handler)

    logging.getLogger("uvicorn").propagate = False

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a module.

    Args:
        name: Module name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
