"""checklist.py"""
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from modules.owaspwstg import OWASPWSTG
from .common import word_completer


class Checklist(): # pylint: disable=R0903
    """Checklist."""
    def __init__(self, parent_obj, handle_input, callback_word_completer) -> None:
        self.parent_obj = parent_obj
        self._parent_callback_word_completer = callback_word_completer
        self._handle_input = handle_input
        self.name = 'checklist'
        self.session = PromptSession()
        self.completer: WordCompleter = word_completer(self)
        self.owaspwstg_obj = OWASPWSTG(self, handle_input, callback_word_completer)

    def owasp_wstg(self) -> None:
        """OWASP Web Security Testing Guide (WSTG)"""
        self._parent_callback_word_completer(OWASPWSTG, 'owaspwstg', OWASPWSTG)

    def _classhelp(self) -> None:
        """Help for Checklist class.

        Returns:
            None
        """
        print("\nChecklists:")
