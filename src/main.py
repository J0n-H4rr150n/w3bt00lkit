"""w3bt00lkit"""
import os
import sys
from logging import Logger
from logger import get_logger
from prompt_toolkit import PromptSession
from modules.completers import Completers
from modules.input_handler import InputHandler
from models import TargetModel
from modules.database import Database
from modules.proxy import Proxy
from modules.targets import Targets
from modules.target_notes import TargetNotes
from modules.target_scope import TargetScope
from modules.common import get_quote

logger: Logger = get_logger(__name__)

BASE_CLASS_NAME = 'W3bT00lkit'


class W3bT00lkit:
    """W3bT00lkit."""

    INTRO = r""" _    _  _____  _      _____  _____  _____  _  _     _  _
| |  | ||____ || |    |_   _||  _  ||  _  || || |   (_)| |
| |  | |    / /| |__    | |  | |/' || |/' || || | __ _ | |_
| |/\| |    \ \| '_ \   | |  |  /| ||  /| || || |/ /| || __|
\  /\  /.___/ /| |_) |  | |  \ |_/ /\ |_/ /| ||   < | || |_
 \/  \/ \____/ |_.__/   \_/   \___/  \___/ |_||_|\_\|_| \__|

"""

    def __init__(self) -> None:
        self.base_name: str = BASE_CLASS_NAME.lower()
        self.name: str = f'{self.base_name} '
        self.class_name: str = 'W3bT00lkit'
        self.selected_target = None
        self.selected_target_in_scope = None
        self.selected_target_out_of_scope = None
        self.session = PromptSession(completer=Completers())
        self.database = Database(self, [])
        self.proxy = Proxy(self, [])
        self.targets = Targets(self, [])
        self.targetnotes = TargetNotes(self, [])
        self.targetscope = TargetScope(self, [])
        self.message = None

    def _get_base_name(self) -> str:
        return self.base_name

    def _get_selected_target(self) -> str:
        return self.selected_target

    def _callback_proxy_message(self, message) -> None:
        print("*** PROXY MESSAGE ***")
        print(message)

    def _callback_set_target(self, target) -> None:
        if target is None:
            self.selected_target = None
            self.name = f"{self.base_name} "
            self.message = "Target removed.\n"
        else:
            self.selected_target: TargetModel = target
            self.name = f"{self.base_name} ({self.selected_target.name}) "
            self.selected_target_in_scope = None
            self.selected_target_out_of_scope = None
        self._clear()
        self._print_output(self.INTRO)
        print(get_quote())
        self.targetscope._get_in_scope(target)
        print()
        if self.message is not None:
            print(self.message)
            self.message = None

    def _print_output(self, *args, **kwargs) -> None:
        if len(args) > 0:
            for value in args:
                print(value)

        if len(kwargs) > 0:
            print(kwargs)

    def _run(self) -> None:
        self._print_output(self.INTRO)
        print(get_quote())
        while True:
            try:
                # https://python-prompt-toolkit.readthedocs.io/en/master/pages/reference.html#prompt_toolkit.shortcuts.PromptSession
                text: str = self.session.prompt(message=f'{self.name}> ')
                handler = InputHandler(self, text)
                handler._handle_input()
            except KeyboardInterrupt:
                continue
            except EOFError:
                break

    def _clear(self) -> None:
        """Clear the screen."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def _exit(self) -> None:
        """Exit the app."""
        sys.exit(0)

if __name__ == '__main__':
    try:
        t00lkit = W3bT00lkit()
        t00lkit._run() # pylint: disable=protected-access
    except KeyboardInterrupt:
        print('Exiting...')
        sys.exit(0)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        print("*** UNHANDLED EXCEPTION ***")
        logger.error(exc, exc_info=True)
