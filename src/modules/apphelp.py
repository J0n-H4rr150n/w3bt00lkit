"""apphelp.py"""


class AppHelp():
    """App Help."""

    def __init__(self, app_obj, args) -> None:
        self.app_obj = app_obj
        self.args = args

    def _handle_input(self, args):
        """Handle Input."""
        self.args = args

        if len(args) == 0:
            return
        
        if len(args) == 1:
            self.main()
        else:
            try:
                class_name = self.args[0]
                if class_name == 'help':
                    function_name = self.args[1]
                else:
                    function_name = self.args[0]
                args = []
                function_name = function_name.replace('-','_')
                func = getattr(self, function_name)
                if callable(func):
                    func(*args)
                else:
                    print('Else: Function is not callable:%s',function_name)
            except AttributeError:
                return
            except Exception as exc:
                print(exc)


    def main(self) -> None: # pylint: disable=unused-argument
        """Help menu for proxy.
        
        Args:
            *args: dynamic tuple of args

        Returns:
            None
        """
        message = """
Usage:

    Press TAB to see available options.

The main commands are:

    add         add something new to the database (i.e. `add target`)
    checklists  view available checklists (i.e. `checklists owasp-wstg`)
    database    options for the database (i.e. `database setup`)
    show        show a list of something (i.e. `show targets`)
    start       start something (i.e. `start proxy`)
    stop        stop something (i.e. `stop proxy`)
    view        view something (i.e. `view targets`)

Additional commands:

    clear       clear the screen (`cls` works as well)
    help        this help menu
    exit        exit the app (or `CTRL + D` on linux)

Use "help <command>" to see help information for a specific command.

"""

        print(message)

    def checklists(self, *args) -> None:
        """Help menu for checklists.
        
        Args:
            *args: dynamic tuple of args

        Returns:
            None
        """
        print("Checklists Help...")        

    def database(self, *args) -> None: # pylint: disable=unused-argument
        """Help menu for database.
        
        Args:
            *args: dynamic tuple of args

        Returns:
            None
        """
        print("Database Help...")

    def proxy(self, *args) -> None: # pylint: disable=unused-argument
        """Help menu for proxy.
        
        Args:
            *args: dynamic tuple of args

        Returns:
            None
        """
        print("Proxy Help...")

    def targets(self) -> None: # pylint: disable=unused-argument
        """Help menu for targets.
        
        Args:
            *args: dynamic tuple of args

        Returns:
            None
        """
        print("Targets Help...")
