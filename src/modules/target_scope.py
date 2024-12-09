"""target_scope.py"""
from typing import List
from sqlalchemy.orm.query import Query
from rich.console import Console
from rich.table import Table
from modules.database import Database
from models import TargetModel, TargetScopeModel

# pylint: disable=C0121,W0212,W0718


class TargetScope: # pylint: disable=R0902
    """Target Scope."""

    def __init__(self, app_obj, args):
        self.app_obj = app_obj
        self.args = args
        self.target_scopes_in: None
        self.target_scopes_out: None

    def _handle_input(self, args) -> None:
        """Handle Input."""
        self.args = args
        if len(self.args) < 2:
            return

        try:
            function_name = self.args[0]
            args = []
            func = getattr(self, function_name)
            if callable(func):
                func(*args)
            else:
                print('Else: Function is not callable:%s',function_name)
        except AttributeError:
            return
        except Exception as exc:
            print(exc)

    def _classhelp(self):
        """Help for TargetScope class.

        Returns:
            None
        """

    def _get_in_scope(self, selected_target):
        """Get In Scope items."""
        self.target_scopes_in = []
        try:
            with Database._get_db() as db:
                records: List[TargetScopeModel] = db.query(TargetScopeModel).filter(
                        TargetScopeModel.active == True,
                        TargetScopeModel.in_scope_ind == True,
                        TargetScopeModel.out_of_scope_ind == False,
                        TargetScopeModel.target_id == selected_target.id
                    ).order_by(TargetScopeModel.fqdn, TargetScopeModel.path).all()

                for record in records:
                    targetscope_record = {
                        'fqdn': record.fqdn,
                        'path': record.path
                    }
                    self.target_scopes_in.append(targetscope_record)
                self.app_obj.selected_target_in_scope = self.target_scopes_in

                print('\033[32mIn Scope:\033[0m')
                table = Table()
                table.add_column('#')
                table.add_column('scope')
                table.add_column('fqdn')
                table.add_column('path')

                counter = 0
                for record in records:
                    table.add_row(str(counter), 'In', record.fqdn, record.path)
                    counter += 1

                console = Console()
                console.print(table)

        except Exception as exc: # pylint: disable=W0718
            print(exc)

    def _get_out_of_scope(self, selected_target):
        """Get Out of Scope items."""
        self.target_scopes_out: List[TargetScopeModel] = []
        try:
            with Database._get_db() as db:
                records: List[TargetScopeModel] = db.query(TargetScopeModel).filter(
                        TargetScopeModel.active == True,
                        TargetScopeModel.out_of_scope_ind == True,
                        TargetScopeModel.in_scope_ind == False,
                        TargetScopeModel.target_id == selected_target.id
                    ).order_by(TargetScopeModel.fqdn, TargetScopeModel.path).all()

                for record in records:
                    targetscope_record = {
                        'fqdn': record.fqdn,
                        'path': record.path
                    }
                    self.target_scopes_out.append(targetscope_record)
                self.app_obj.selected_target_out_of_scope = self.target_scopes_out

                print('\n\033[31mOut of Scope:\033[0m')
                table = Table()
                table.add_column('#')
                table.add_column('scope')
                table.add_column('fqdn')
                table.add_column('path')

                counter = 0
                for record in records:
                    table.add_row(str(counter), 'Out', record.fqdn, record.path)
                    counter += 1

                console = Console()
                console.print(table)

        except Exception as exc: # pylint: disable=W0718
            print(exc)


    def add(self) -> None: # pylint: disable=R0914,R0911,R0912,R0915
        """Add an item to the target's scope and save to the database.

        Returns:
            None
        """
        selected_target: TargetModel = self.app_obj._get_selected_target()
        if selected_target is None:
            print("\nPlease select a target before using the 'scope' option.\n")
            return

        item_in_scope = False
        item_out_of_scope = False
        item_wildcard = False
        item_fqdn = None
        item_path = None

        scope_item: str = input("Input the scope item (leave blank to cancel):\n")
        if '' == scope_item:
            return
        print("Scope item >",scope_item)
        if '*' in scope_item:
            item_wildcard = True

        if '/' in scope_item:
            item_path = scope_item
        else:
            item_fqdn = scope_item

        scope_type: str = input("Is this in scope? (`y` or enter == yes; `n` == no)\n")
        valid_scope_type = False

        if '' == scope_type or 'y' == scope_type.lower() or 'yes' == scope_type.lower():
            scope_type = "in"
            valid_scope_type = True
            item_in_scope = True
        elif 'n' == scope_type.lower().strip() or 'no' == scope_type.lower().strip():
            scope_type = "out"
            valid_scope_type = True
            item_out_of_scope = True
        elif valid_scope_type == False:
            print("Invalid scope type.")
            self.app_obj._back() # pylint: disable=W0212
            return
        else:
            print("Other issues. Return...")
            return

        print(f"\nTarget name: {selected_target.name}")
        print(f"Scope item: {scope_item}")
        print(f"Scope type: {scope_type}\n")

        save_to_database = False
        confirm = input("Is this correct? (`y` or enter == yes; `n` == no)\n")
        if '' == confirm or 'y' == confirm.lower():
            save_to_database = True

        if 'n' == confirm.lower().strip() or 'N' == confirm.lower().strip():
            print("Cancel.")
            return

        if scope_type not in ('in', 'out'):
            print("Cancel for other reason.")
            return

        if save_to_database == False:
            print("Cancel.")
            return

        with Database._get_db() as db:
            existing_record: Query[TargetScopeModel] = db.query(TargetScopeModel)\
                .filter_by(target_id=selected_target.id, fqdn=item_fqdn, path=item_path).first()

            if not existing_record:
                try:
                    new_target_scope = TargetScopeModel(
                        target_id = selected_target.id,
                        fqdn = item_fqdn,
                        path = item_path,
                        in_scope_ind = item_in_scope,
                        out_of_scope_ind = item_out_of_scope,
                        wildcard_ind = item_wildcard
                    )
                    db.add(new_target_scope)
                    db.commit()
                    db.refresh(new_target_scope)
                except Exception as database_exception: # pylint: disable=W0718
                    print(database_exception)
            else:
                print("Target scope already exists.\n")

    def view(self) -> None:
        """List all items."""

        selected_target: TargetModel = self.app_obj._get_selected_target()
        if selected_target is None:
            print("\nPlease select a target before using the 'scope' option.\n")
            return

        self._get_out_of_scope(selected_target)
        self._get_in_scope(selected_target)
        print("")
