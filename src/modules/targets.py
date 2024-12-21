"""targets.py"""
from typing import List
from sqlalchemy import func
from sqlalchemy.orm.query import Query
from rich.console import Console
from rich.table import Table
from modules.database import Database
from models import TargetModel

# pylint: disable=C0121,E1102,R0903,W0212,W0718


class Targets:
    """Targets."""

    def __init__(self, app_obj, args):
        self.app_obj = app_obj
        self.args = args

    def _handle_input(self, args):
        """Handle Input."""
        self.args = args
        if len(self.args) < 2:
            return

        try:
            class_name = self.args[1]
            function_name = self.args[0]
            args = []
            match class_name:
                case 'target':
                    function_name = f"_{function_name}_target"
                case 'targets':
                    function_name = f"_{function_name}_targets"
                case _:
                    return

            func = getattr(self, function_name) # pylint: disable=W0621
            if callable(func):
                func(*args)
            else:
                print('Else: Function is not callable:%s',function_name)
        except AttributeError:
            return
        except Exception as exc:
            print(exc)

    def _add_target(self):
        """Add a target."""
        target_name: str = input("Target Name (leave blank to cancel): ")
        if '' == target_name:
            return
        print("Target Name >",target_name)
        platform_name: str = input("Platform Name (leave blank to cancel): ")
        if '' == platform_name:
            return
        print("Platform Name >",platform_name)
        with Database._get_db() as db:
            try:
                existing_record: Query[TargetModel] = db.query(TargetModel)\
                    .filter(TargetModel.name.ilike(f"{target_name}")).filter(TargetModel.platform.ilike(f"{platform_name}")).first()
            except Exception as exc:
                print(exc)

            if not existing_record:
                new_target = TargetModel(
                    name=target_name,
                    platform=platform_name,
                    active=True
                )
                db.add(new_target)
                db.commit()
                db.refresh(new_target)
                print("Target added!\n")
            else:
                if existing_record.active == False:
                    existing_record.active = True
                    existing_record.modified_timestamp = func.now()
                    db.commit()
                    print("Reactivated target. It exists but was disabled!\n")
                else:
                    print("Target already exists.\n")

    def _remove_target(self):
        """Remove target."""
        if self.app_obj.selected_target is None:
            return
        selected_target: TargetModel = self.app_obj.selected_target
        confirm = input("Are you sure you want to remove the current target ('y','yes'==YES; 'n','no',enter==CANCEL) ?\n")
        if confirm.lower() in ('y','yes'):
            with Database._get_db() as db:
                existing_record: Query[TargetModel] = db.query(TargetModel)\
                    .filter_by(id=selected_target.id).first()

                if existing_record:
                    existing_record.active = False
                    existing_record.modified_timestamp = func.now()
                    db.commit()
                    self.app_obj._callback_set_target(None)



    def _select_target(self, selected_no: int, targets: List[TargetModel]):
        """Select a target

        Args:
            selection (int): The number of the selected target in the targets list.

        Returns:
            None
        """
        print("Select target #:", selected_no)
        selected_target: TargetModel = targets[selected_no]
        self.app_obj._callback_set_target(selected_target)

    def _view_targets(self):
        """List all active targets.

        Returns:
            None
        """
        print("")
        try:
            with Database._get_db() as db:
                records: List[TargetModel] = db.query(TargetModel).filter(TargetModel.active == True).order_by(TargetModel.name).all()

                table = Table(title='Targets')
                table.add_column('#')
                table.add_column('name')
                table.add_column('platform')

                counter = 0
                for record in records:
                    table.add_row(str(counter), record.name, record.platform)
                    counter += 1

                console = Console()
                console.print(table)

            selected: str = input("Select a target by #, or leave blank and press enter to cancel: ")
            if '' == selected:
                return
            try:
                selected_no = int(selected)
                self._select_target(selected_no, records)
            except ValueError:
                return
        except Exception as database_exception: # pylint: disable=W0718
            print("*** TARGETS EXCEPTION ***")
            print(database_exception)
