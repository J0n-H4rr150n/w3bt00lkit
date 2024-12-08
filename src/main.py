"""w3bt00lkit"""
import os
import sys
import subprocess
from logging import Logger
from prompt_toolkit import PromptSession
from modules.completers import Completers
from modules.input_handler import InputHandler
from logger import get_logger
from models import TargetModel
from modules.apphelp import AppHelp
from models import ChecklistModel
from modules.checklist import Checklist
from modules.database import Database # pylint: disable=C0412
from modules.proxy import Proxy
from modules.synack import Synack
from modules.targets import Targets
from modules.target_notes import TargetNotes
from modules.target_scope import TargetScope
from modules.tools import Tools
from modules.vulnerabilities import Vulnerabilities
from modules.common import get_quote

logger: Logger = get_logger(__name__)
BASE_CLASS_NAME = 'W3bT00lkit'
# pylint: disable=R0902,R0903,W0212,W0718


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
        self.apphelp = AppHelp(self, [])
        self.checklist = Checklist(self, [])
        self.database = Database(self, [])
        self.proxy = Proxy(self, [])
        self.synack = Synack(self, [])
        self.targets = Targets(self, [])
        self.targetnotes = TargetNotes(self, [])
        self.targetscope = TargetScope(self, [])
        self.tools = Tools(self, [])
        self.vulnerabilities = Vulnerabilities(self, [])
        self.message = None
        self.proxy_running = False
        self.missions_running = False

    def _get_base_name(self) -> str:
        return self.base_name

    def _get_selected_target(self) -> str:
        return self.selected_target

    def _callback_proxy_message(self, message) -> None:
        if "SYSTEM: PROXY STARTED" == message:
            self.proxy_running = True
            if self.selected_target is not None:
                self.name = f"{self.base_name} (proxy) ({self.selected_target.name}) "
            else:
                self.name = f"{self.base_name} (proxy) "
        elif "SYSTEM: PROXY STOPPED" == message:
            self.proxy_running = False
            if self.selected_target is not None:
                self.name = f"{self.base_name} ({self.selected_target.name}) "
            else:
                self.name = f"{self.base_name} "
        else:
            print("*** PROXY MESSAGE ***")
            print(message)

    def _callback_set_target(self, target) -> None:
        try:
            self.proxy.stop()
        except Exception as exc:
            print(exc)

        if target is None:
            self.selected_target = None
            self.name = f"{self.base_name} "
            self.message = "Target removed.\n"
        else:
            if self.proxy_running:
                self.selected_target: TargetModel = target
                self.name = f"{self.base_name} (proxy) ({self.selected_target.name}) "
                self.selected_target_in_scope = None
                self.selected_target_out_of_scope = None
            else:
                self.selected_target: TargetModel = target
                self.name = f"{self.base_name} ({self.selected_target.name}) "
                self.selected_target_in_scope = None
                self.selected_target_out_of_scope = None
        self._clear()
        self._print_output(self.INTRO)
        print(get_quote())
        self.targetscope._get_in_scope(target)
        checklist_record = ChecklistModel()
        self.targetnotes._get_checklist_notes(target, checklist_record)
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
        args = sys.argv
        if len(args) > 1:
            if args[1].lower() == '-h' or args[1].lower() == '--help':
                apphelp = AppHelp(self, [])
                apphelp._handle_input(['help'])
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
        else:
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

    def _pwd(self) -> None:
        result = subprocess.run(['pwd'], stdout=subprocess.PIPE)
        if result.returncode == 0:
            print(result.stdout.decode('utf-8').strip())

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
