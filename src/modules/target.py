"""target.py"""
from typing import List, Literal
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from sqlalchemy.orm.query import Query
from sqlalchemy.orm.session import Session
import pandas as pd
from tabulate import tabulate
from modules.database import Database as TargetDatabase
from models import TargetModel, TargetScopeModel
from .common import word_completer

# pylint: disable=C0121

class TargetScope: # pylint: disable=R0902
    """Target Scope."""

    def __init__(self, app_obj, parent_obj, handle_input, get_selected_target, set_previous_menu) -> None: # pylint: disable=R0917,R0913
        self.app_obj = app_obj
        self.parent_obj = parent_obj
        self._handle_input = handle_input
        self._get_selected_target = get_selected_target
        self._set_previous_menu = set_previous_menu
        self.name = 'targetscope'
        self.session = PromptSession()
        self.completer: WordCompleter = word_completer(self)
        self.target_scopes_in: List[TargetModel]
        self.target_scopes_out: List[TargetModel]

    def _classhelp(self):
        """Help for TargetScope class.

        Returns:
            None
        """

    def add(self) -> None: # pylint: disable=R0914,R0911,R0912,R0915
        """Add an item to the target's scope and save to the database.

        Returns:
            None
        """
        target_name = self._get_selected_target()
        if target_name is None or self.app_obj.selected_target_obj is None:
            print("\nPlease select a target before using the 'scope' option.")
            self._set_previous_menu(self.name,'add')
            self.app_obj._back() # pylint: disable=W0212
            self._handle_input(self.app_obj, self.app_obj.target_obj, 'list', [], None)
            return

        item_in_scope = False
        item_out_of_scope = False
        item_wildcard = False
        item_fqdn = None
        item_path = None

        scope_item: str = input("Input the scope item (leave blank to cancel): ")
        if '' == scope_item:
            return
        print("Scope item >",scope_item)
        if '*' in scope_item:
            item_wildcard = True

        if '/' in scope_item:
            item_path = scope_item
        else:
            item_fqdn = scope_item

        scope_type: str = input("Is this in scope (`y` or enter == yes; `n` == no)")
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

        print(f"\nTarget name: {target_name}")
        print(f"Scope item: {scope_item}")
        print(f"Scope type: {scope_type}\n")

        save_to_database = False
        confirm = input("Is this correct? (`y` or enter == yes; `n` == no)")
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

        selected_target = self.app_obj.selected_target_obj

        db = TargetDatabase()
        db_session: Session = db.session_local()

        existing_record: Query[TargetScopeModel] = db_session.query(TargetScopeModel)\
            .filter_by(target_id=selected_target['id'], fqdn=item_fqdn, path=item_path)

        if not existing_record:
            try:
                new_target_scope = TargetScopeModel(
                    target_id = selected_target['id'],
                    fqdn = item_fqdn,
                    path = item_path,
                    in_scope_ind = item_in_scope,
                    out_of_scope_ind = item_out_of_scope,
                    wildcard_ind = item_wildcard
                )
                result: Literal[0] | Literal[1] = db._add_targetscope(db_session, new_target_scope) # pylint: disable=W0212
                if result == 0:
                    print("Target scope added to the database.\n")
                elif result == 1:
                    print("Target scope already exists.\n")
                else:
                    print("There was an error trying to add the target scope.\n")
            except Exception as database_exception: # pylint: disable=W0718
                print(database_exception)
        else:
            print("Target scope already exists.\n")

    def list(self) -> None:
        """List all items."""

        target_name = self._get_selected_target()
        if target_name is None or self.app_obj.selected_target_obj is None:
            print("\nPlease select a target before using the 'scope' option.")
            self._set_previous_menu(self.name,'add')
            self.app_obj._back() # pylint: disable=W0212
            self._handle_input(self.app_obj, self.app_obj.target_obj, 'list', [], None)
            return

        selected_target = self.app_obj.selected_target_obj

        print('\n\033[31mOut of Scope:\033[0m')
        self.target_scopes_out: List[TargetModel] = []
        try:
            target_database = TargetDatabase()
            db_session: Session = target_database.session_local()
            records: List[TargetScopeModel] = db_session.query(TargetScopeModel).filter(
                    TargetScopeModel.active == True,
                    TargetScopeModel.out_of_scope_ind == True,
                    TargetScopeModel.in_scope_ind == False,
                    TargetScopeModel.target_id == selected_target['id']
                ).order_by(TargetScopeModel.fqdn, TargetScopeModel.path).all()
            for record in records:
                targetscope_record = {
                    'fqdn': record.fqdn,
                    'path': record.path
                }
                self.target_scopes_out.append(targetscope_record)
            self.app_obj.selected_target_out_of_scope = self.target_scopes_out
            df = pd.DataFrame(self.target_scopes_out)
            df.index.name = '#'
            print(tabulate(df, headers='keys', tablefmt='psql'))
        except Exception as exc: # pylint: disable=W0718
            print(exc)

        print("")
        print('\033[32mIn Scope:\033[0m')
        self.target_scopes_in = []
        try:
            target_database = TargetDatabase()
            db_session: Session = target_database.session_local()
            records: List[TargetScopeModel] = db_session.query(TargetScopeModel).filter(
                    TargetScopeModel.active == True,
                    TargetScopeModel.in_scope_ind == True,
                    TargetScopeModel.out_of_scope_ind == False,
                    TargetScopeModel.target_id == selected_target['id']
                ).order_by(TargetScopeModel.fqdn, TargetScopeModel.path).all()
            for record in records:
                targetscope_record = {
                    'fqdn': record.fqdn,
                    'path': record.path
                }
                self.target_scopes_in.append(targetscope_record)
            self.app_obj.selected_target_in_scope = self.target_scopes_in
            df = pd.DataFrame(self.target_scopes_in)
            df.index.name = '#'
            print(tabulate(df, headers='keys', tablefmt='psql'))
        except Exception as exc: # pylint: disable=W0718
            print(exc)

        print("")

class Target(): # pylint: disable=R0902
    """Target."""
    def __init__(self, parent_obj, callback_set_target, handle_input, # pylint: disable=R0913,R0917
                 callback_word_completer, get_selected_target, set_previous_menu
                 ) -> None:
        self.parent_obj = parent_obj
        self._parent_callback_set_target = callback_set_target
        self._parent_callback_word_completer = callback_word_completer
        self._handle_input = handle_input
        self._get_selected_target = get_selected_target
        self._set_previous_meu = set_previous_menu
        self.name = 'target'
        self.session = PromptSession()
        self.completer: WordCompleter = word_completer(self)
        self.targetscope_obj = TargetScope(parent_obj,self, handle_input, get_selected_target, self._set_previous_meu)
        self.current_target = None
        self.targets = None
        self.target_scopes_in: List[TargetModel] = []

    def add(self) -> None:
        """Add a new target."""
        target_name: str = input("Target Name (leave blank to cancel): ")
        if '' == target_name:
            return
        print("Target Name >",target_name)
        platform_name: str = input("Platform Name (leave blank to cancel): ")
        if '' == platform_name:
            return
        print("Platform Name >",platform_name)
        try:
            db = TargetDatabase()
            db_session: Session = db.session_local()

            existing_record: Query[TargetModel] = db_session.query(TargetModel)\
                .filter(TargetModel.name.ilike(f"%{target_name}%")).filter(TargetModel.platform.ilike(f"%{platform_name}"))

            if not existing_record:
                new_target = TargetModel(
                    name=target_name,
                    platform=platform_name,
                    active=True
                )
                result: Literal[0] | Literal[1] = db._add_target(db_session, new_target) # pylint: disable=W0212
                if result == 0:
                    print("Target added to the database.\n")
                elif result == 1:
                    print("Target already exists.\n")
                else:
                    print("There was an error trying to add the target.\n")
            else:
                print("Target already exists.\n")
        except Exception as database_exception: # pylint: disable=W0718
            print(database_exception)

    def _select_target(self, selected_no: int) -> None:
        """Select a target

        Args:
            selection (int): The number of the selected target in the targets list.

        Returns:
            None
        """
        print("Select target #:", selected_no)
        self._parent_callback_set_target(self.targets[selected_no])

        self.target_scopes_in = []
        try:
            target_database = TargetDatabase()
            db_session: Session = target_database.session_local()
            records: List[TargetScopeModel] = db_session.query(TargetScopeModel).filter(
                    TargetScopeModel.active == True,
                    TargetScopeModel.in_scope_ind == True,
                    TargetScopeModel.out_of_scope_ind == False,
                    TargetScopeModel.target_id == self.targets[selected_no]['id']
                ).order_by(TargetScopeModel.fqdn, TargetScopeModel.path).all()
            for record in records:
                targetscope_record = {
                    'fqdn': record.fqdn,
                    'path': record.path
                }
                self.target_scopes_in.append(targetscope_record)
            self.parent_obj.selected_target_in_scope = self.target_scopes_in
            df = pd.DataFrame(self.target_scopes_in)
            df.index.name = '#'
            print('\033[32mIn Scope:\033[0m')
            print(tabulate(df, headers='keys', tablefmt='psql'))
            print("")
        except Exception as exc: # pylint: disable=W0718
            print(exc)


    def list(self) -> None:
        """List all active targets.

        Returns:
            None
        """
        print("")
        try:
            db = TargetDatabase()
            db_session: Session = db.session_local()
            self.targets: list = db._get_targets(db_session) # pylint: disable=W0212
            df = pd.DataFrame(self.targets)
            df.index.name = '#'
            print(tabulate(df, headers='keys', tablefmt='psql'))
            selected: str = input("Select a target by # (leave blank to cancel): ")
            if '' == selected:
                return
            try:
                selected_no = int(selected)
                self._select_target(selected_no)
            except ValueError:
                print("ERROR: Invalid input. Input a valid number.")
                self._handle_input(self.parent_obj, self, 'list', [], None)
        except Exception as database_exception: # pylint: disable=W0718
            print(database_exception)

    def info(self) -> None:
        """Get info about a target by name.

        Returns:
            None
        """
        target_name: str = input("Target Name (leave blank to cancel): ")
        if '' == target_name:
            return
        print("Target Name >",target_name)

    def scope(self) -> None:
        """Manage the scope for a target.

        Returns:
            None
        """
        self._parent_callback_word_completer(TargetScope, 'targetscope', TargetScope)

    def select(self) -> None:
        """Select a target by name.

        Returns:
            None
        """
        target_name: str = input("Target Name (leave blank to cancel): ")
        if '' == target_name:
            return
        print("Target Name >",target_name)
