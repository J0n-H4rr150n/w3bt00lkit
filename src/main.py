"""w3bt00lkit"""
from logging import Logger
import os
import sys
from typing import Optional
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from logger import get_logger
from modules import checklist, database, apphelp, proxy, target
from modules.target import TargetScope
from modules.common import fix_selection, word_completer

logger: Logger = get_logger(__name__)

BASE_CLASS_NAME = 'W3bT00lkit'

def run_function(app_obj, obj, class_name, function_name, args) -> None:
    """Dynamically run a function.
    
    Args:
        obj: The object the function lives in.
        function_name: The name of the function to run.
        args: Arguments to pass to the function.

    Returns:
        None
    """
    match class_name.lower():
        case 'checklist':
            if function_name == 'owaspwstg':
                obj = app_obj.checklist_obj.owaspwstg_obj
                function_name = '_classhelp'
            else:
                obj = app_obj.checklist_obj
        case 'database':
            obj = app_obj.database_obj
        case 'proxy':
            obj = app_obj.proxy_obj
        case 'proxyconfig':
            obj = app_obj.proxy_obj.proxyconfig_obj
        case 'target':
            if function_name == 'targetscope':
                obj = app_obj.target_obj.targetscope_obj
            else:
                obj = app_obj.target_obj
        case 'targetscope':
            obj = app_obj.target_obj.targetscope_obj
            if 'targetscope' == function_name:
                function_name = '_classhelp'

    try:
        func = getattr(obj, function_name)
        if callable(func):
            func(*args)
        else:
            logger.debug('Else: Function is not callable:%s',function_name)
    except Exception as exc: # pylint: disable=W0718
        logger.error(exc, exc_info=True)

def handle_input(app_obj, obj, text, args, sub_obj=None) -> None: # pylint: disable=R0915
    """Handle Input.
    
    Args:
        text: The input from the user.

    Returns:
        None
    """
    class_name: str = app_obj.class_name

    if text == 'targetscope':
        obj = TargetScope
        sub_obj = obj
        class_name = 'TargetScope'
        app_obj.class_name = 'TargetScope'

    if ' ' in text:
        print("handle_input with space")
        function_name: str
        arg_str: str
        function_name, arg_str = text.split(' ', 1)
        function_name = fix_selection(function_name)
        args = arg_str.split()
        run_function(app_obj, obj, class_name, function_name, args)
    else:
        function_name = fix_selection(text)
        if function_name.startswith('_'):
            match function_name:
                case '_back':
                    app_obj._back() # pylint: disable=W0212
                case '_clear':
                    app_obj._clear() # pylint: disable=W0212
                case '_cls':
                    app_obj._cls() # pylint: disable=W0212
                case '_help':
                    h = apphelp.AppHelp()
                    match app_obj.class_name.lower():
                        case app_obj.base_name:
                            h.main()
                        case 'proxy':
                            h.proxy()
                        case 'target':
                            h.target()
                        case 'database':
                            h.database()
                case '_exit':
                    app_obj._exit() # pylint: disable=W0212
                case _:
                    return
        else:
            app_obj.previous_class_name = app_obj.class_name
            app_obj.previous_name = app_obj.name

            match function_name:
                case 'checklist':
                    app_obj.class_name = function_name
                case 'database':
                    app_obj.class_name = function_name
                case 'proxy':
                    app_obj.class_name = function_name
                case 'target':
                    app_obj.class_name = function_name
                case 'targetscope':
                    app_obj.class_name = function_name
                case 'proxyconfig':
                    app_obj.class_name = function_name
                case _:
                    app_obj.function_name = function_name.capitalize()

            if app_obj.selected_target is not None:
                app_obj.name = f"{app_obj.base_name} ({app_obj.selected_target}) ({app_obj.class_name.lower()}) "
                if sub_obj is not None:
                    if app_obj.class_name.lower() == 'targetscope':
                        app_obj.name = f"{app_obj.base_name} ({app_obj.selected_target}) (target) (scope) "
                        run_function(app_obj, obj, class_name, function_name, args)
                else:
                    app_obj.name = f"{app_obj.base_name} ({app_obj.selected_target}) ({app_obj.class_name.lower()}) "
                    run_function(app_obj, obj, class_name, function_name, args)
            else:
                if sub_obj is not None:
                    if app_obj.class_name.lower() == 'targetscope':
                        app_obj.name = f"{app_obj.base_name} (target) (scope) "
                        run_function(app_obj, obj, class_name, function_name, args)
                else:
                    app_obj.name = f"{app_obj.base_name} ({app_obj.class_name.lower()}) "
                    run_function(app_obj, obj, class_name, function_name, args)


class W3bT00lkit: # pylint: disable=R0902
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
        self.previous_name: str = self.name
        self.class_name: str = 'W3bT00lkit'
        self.previous_class_name: str = self.class_name
        self.function_name: Optional[str] = None
        self.previous_function_name: Optional[str] = None
        self.session: PromptSession = PromptSession()
        self.completer: WordCompleter = word_completer(self)
        self.checklist_obj = checklist.Checklist(self, handle_input, self._callback_word_completer)
        self.database_obj = database.Database()
        self.proxy_obj = proxy.Proxy(self, self._get_base_name, self._callback_word_completer, self._callback_proxy_message)
        self.target_obj = target.Target(self, self._callback_set_target, handle_input, self._callback_word_completer,
                                        self._get_selected_target, self._set_previous_menu
                                        )
        self.selected_target = None
        self.selected_target_obj = None
        self.selected_target_in_scope = None
        self.selected_target_out_of_scope = None
        self.previous_menu = None

    def _get_base_name(self) -> str:
        return self.base_name

    def _get_selected_target(self) -> str:
        return self.selected_target

    def _callback_proxy_message(self, message) -> None:
        print("*** PROXY MESSAGE ***")
        print(message)

    def _callback_set_target(self, target_name) -> None:
        self.selected_target = target_name['name']
        self.selected_target_obj = target_name
        self._clear()
        self._print_output(self.INTRO)
        self._back()
        if self.previous_menu is not None:
            self.completer: WordCompleter = word_completer(TargetScope)
            handle_input(self, self, self.previous_menu['obj_name'], [])

    def _get_previous_menu(self) -> str:
        return self.previous_menu

    def _set_previous_menu(self, obj_name, previous_menu) -> str:
        self.previous_menu = {'obj_name': obj_name, 'previous_menu': previous_menu}
        print("Previous menu set to:",self.previous_menu)

    def _callback_word_completer(self, obj, function_name, sub_obj=None) -> None: # pylint: disable=W0613
        self.completer: WordCompleter = word_completer(obj)
        handle_input(self, obj, function_name, [], None)

    def _run(self) -> None:
        self._print_output(self.INTRO)
        while True:
            text: str = self.session.prompt(f'{self.name}> ', completer=self.completer)
            args: list = []

            if text == '':
                continue
            handle_input(self, self, text, args, None)

    def _print_output(self, *args, **kwargs) -> None:
        if len(args) > 0:
            for value in args:
                print(value)

        if len(kwargs) > 0:
            print(kwargs)

    def _back(self) -> None:
        """Go back to the main menu."""
        self._main()

    def _cls(self) -> None:
        """Clear the screen with 'cls' as input."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def _clear(self) -> None:
        """Clear the screen with 'clear' as input."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def _exit(self) -> None:
        """Exit the app."""
        print("Exiting...")
        sys.exit(0)

    def _main(self) -> None:
        """Go to the Main Menu."""
        self.name = f'{self.base_name} '
        self.previous_name = self.name
        self.class_name = 'W3bT00lkit'
        self.previous_class_name = self.class_name
        self.session = PromptSession()
        self.completer: WordCompleter = word_completer(self)

        if self.selected_target is not None:
            self.name = f'{self.base_name} ({self.selected_target}) '

    def checklist(self, *args) -> None: # pylint: disable=unused-argument
        """Checklist.
        
        Args:
            *args: dynamic tuple of args

        Returns:
            None
        """
        self.completer: WordCompleter = word_completer(checklist.Checklist)

    def database(self, *args) -> None: # pylint: disable=unused-argument
        """Database.
        
        Args:
            *args: dynamic tuple of args

        Returns:
            None
        """
        self.completer: WordCompleter = word_completer(database.Database)

    def proxy(self, *args) -> None: # pylint: disable=unused-argument
        """Proxy.
        
        Args:
            *args: dynamic tuple of args

        Returns:
            None
        """
        self.completer: WordCompleter = word_completer(proxy.Proxy)

    def target(self, *args) -> None: # pylint: disable=unused-argument
        """Target.
        
        Args:
            *args: dynamic tuple of args

        Returns:
            None
        """
        self.completer: WordCompleter = word_completer(target.Target)


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
