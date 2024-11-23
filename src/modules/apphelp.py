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
        print("Main help menu.")

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
