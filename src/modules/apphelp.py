"""help.py"""


class AppHelp():
    """Help class."""

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

    add       add something new to the database
    clear     clear the screen
    cls       clear the screen
    help      this help menu
    select    select something from the database
    setup     setup the database
    show      show a list of something
    stop      stop something

    exit      exit the app

Use "help <command>" to see help information for a specific command.

"""

        print(message)

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

    def target(self) -> None: # pylint: disable=unused-argument
        """Help menu for target.
        
        Args:
            *args: dynamic tuple of args

        Returns:
            None
        """
        print("Target Help...")
