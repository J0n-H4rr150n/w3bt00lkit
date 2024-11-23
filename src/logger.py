"""logger.py"""
import logging
import os
import re


class NoTracebackStreamHandler(logging.StreamHandler):
    """NoTracebackStreamHandler."""
    def handle(self, record):
        info, cache = record.exc_info, record.exc_text
        record.exc_info, record.exc_text = None, None
        try:
            super().handle(record)
        finally:
            record.exc_info = info
            record.exc_text = cache

def validate_log_file(log_file: str) -> bool:
    """Check a string to ensure it only contains specifical characters.

    Args:
        log_file: The string to validate.

    Returns:
        True if the string is valid, False otherwise.
    """
    return bool(re.match(r'^[a-zA-Z0-9._]*$', log_file))

def get_logger(name, log_file='app.log'):
    """Get Custom Logger.

    Args:
        log_file: The string of the log filename.

    Returns:
        An instance of the custom logger.
    """
    logger: logging.Logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(message)s')
    console_handler = NoTracebackStreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(message)s\n(exc_text)s')
    current_dir: str = os.path.dirname(os.path.abspath(__file__))

    if validate_log_file(log_file):
        file_handler = logging.FileHandler(f"{current_dir}/{log_file}", mode='a+')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger
