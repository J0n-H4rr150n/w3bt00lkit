"""test_logger.py"""
import logging
import unittest
from unittest.mock import patch

from src import logger as custom_logger # pylint: disable=import-error

class LoggerTest(unittest.TestCase):
    """Logger test case."""

    @patch('logging.StreamHandler.handle')
    def test_no_traceback_stream_handler(self, mock_handle) -> None:
        """Test no_traceback_stream_handler."""
        record = logging.LogRecord(
            name='test_logger', level=logging.ERROR, message='Test message',
            exc_info=(ValueError, ValueError('Test exception'), None),
            pathname='testpath',
            lineno = 101,
            msg='Test message',
            args=None
        )

        handler = custom_logger.NoTracebackStreamHandler()
        handler.handle(record)

        mock_handle.assert_called_once_with(record)
        self.assertIsNotNone(record.exc_info)
        self.assertIsNone(record.exc_text)

    def test_validate_log_file(self) -> None:
        """Test validate_log_file."""
        valid_names: list[str] = ['app.log', 'my_log_123.txt', 'valid.log_with_dots']
        for name in valid_names:
            self.assertTrue(custom_logger.validate_log_file(name))

        invalid_names = ['invalid@name.log', 'has$special.chars', 'rm -rf *']
        for name in invalid_names:
            self.assertFalse(custom_logger.validate_log_file(name))

    def test_get_logger(self) -> None:
        """Test get_logger."""
        logger: logging.Logger = custom_logger.get_logger('test_logger', 'valid_log.txt')
        self.assertEqual(logger.name, 'test_logger')
        self.assertEqual(logger.level, logging.DEBUG)

        console_handler: logging.Handler = logger.handlers[0]
        self.assertIsInstance(console_handler, custom_logger.NoTracebackStreamHandler)
        self.assertEqual(console_handler.formatter._fmt, '%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(message)s') # pylint: disable=protected-access

        if len(logger.handlers) > 1:
            file_handler: logging.Handler = logger.handlers[1]
            self.assertIsInstance(file_handler, logging.FileHandler)
            self.assertEqual(file_handler.formatter._fmt, '%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(message)s\n(exc_text)s') # pylint: disable=protected-access

if __name__ == '__main__':
    unittest.main() # pragma: no cover
