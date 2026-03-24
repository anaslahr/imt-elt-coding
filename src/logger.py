"""
TP3 — Structured JSON Logging
==============================
Create a reusable logger that outputs structured JSON logs.

Each log line should be a JSON object like:
    {"timestamp": "2026-03-18T10:30:00Z", "level": "INFO", "module": "extract", "function": "extract_products", "message": "..."}
"""

import json
import logging
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """
    Custom log formatter that outputs JSON.

    Override the format() method to return a JSON string instead of plain text.
    """

    def format(self, record: logging.LogRecord) -> str:
        # TODO: Build a dictionary with the following keys:
        #   - "timestamp": current UTC time in ISO format → datetime.now(timezone.utc).isoformat()
        #   - "level": the log level name → record.levelname
        #   - "module": the module that logged → record.module
        #   - "function": the function that logged → record.funcName
        #   - "message": the log message → record.getMessage()
        #
        # Then return json.dumps(log_entry)
        #
        # Bonus: if record.exc_info contains an exception, add an "exception" key
        #   if record.exc_info and record.exc_info[0] is not None:
        #       log_entry["exception"] = self.formatException(record.exc_info)

        pass  # ← Replace with your implementation


def get_logger(name: str) -> logging.Logger:
    """
    Create and return a logger with JSON-formatted output.

    Args:
        name: Logger name (usually __name__ of the calling module)

    Returns:
        A configured logging.Logger instance
    """
    # TODO: Complete the function:
    #   1. Create a logger: logging.getLogger(name)
    #   2. Only add a handler if none exist yet (if not logger.handlers:)
    #      This prevents duplicate log lines if get_logger() is called multiple times
    #   3. Create a StreamHandler() (outputs to console)
    #   4. Set its formatter to JSONFormatter()
    #   5. Add the handler to the logger
    #   6. Set the logger level to logging.DEBUG
    #   7. Return the logger

    pass  # ← Replace with your implementation
