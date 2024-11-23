"""test_logger.py"""
import unittest
from unittest.mock import patch

from src.modules import common # pylint: disable=import-error
from prompt_toolkit.completion import WordCompleter

SYSTEM_STRINGS: list[str] = ['back','clear','cls','help','exit']
NORMAL_STRINGS: list[str] = ['alpha','bravo','charlie','delta']

class CommonTest(unittest.TestCase):
    """Common test case."""

    def test_fix_selection(self) -> None:
        """Test validate_log_file."""
        
        for name in SYSTEM_STRINGS:
            function_name = common.fix_selection(name)
            self.assertEqual(function_name, f"_{name}")

        for name in NORMAL_STRINGS:
            function_name = common.fix_selection(name)
            self.assertEqual(function_name, function_name)


    def test_word_completer(self) -> WordCompleter:
        """Automatically generate words to use as commands.
        
        Args:
            obj: The object to generate words from.
        
        Returns:
            The list of available words that can be used.
        """
        self.assertTrue(common.word_completer(self))

if __name__ == '__main__':
    unittest.main() # pragma: no cover
