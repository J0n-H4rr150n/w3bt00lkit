"""synack.py"""
import datetime
from sqlalchemy.orm.query import Query
from typing import List, Literal, LiteralString
from rich.console import Console
from rich.table import Table
from rich.text import Text
from modules.database import Database
from models import SynackTargetModel
from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.shortcuts import input_dialog
from sqlalchemy import desc, or_, select, func
from urllib.parse import urlparse, parse_qs

class Synack:
    """Synack."""
    def __init__(self, app_obj, args):
        self.app_obj = app_obj
        self.args = args
        self.prompt_user = False

    def _handle_input(self, args):
        """Handle Input."""
        self.args = args
        if len(self.args) < 2:
            return

        try:
            class_name = self.args[0]
            function_name = self.args[1]
            args = []
            func = getattr(self, f"_{function_name}")
            if callable(func):
                func(*args)
            else:
                print('Else: Function is not callable:%s',function_name)
        except AttributeError:
           return
        except Exception as exc:
            print(exc)


    def _targets(self):
        """List all active targets.

        Returns:
            None
        """
        print("")
        try:
            with Database._get_db() as db:
                records: List[SynackTargetModel] = db.query(SynackTargetModel)\
                    .filter(SynackTargetModel.active == True)\
                    .filter(SynackTargetModel.vulnerability_discovery == True)\
                    .order_by(desc(SynackTargetModel.activated_at)).all()
                    #.order_by(desc(SynackTargetModel.collaboration_criteria), SynackTargetModel.target_codename).all()

                table = Table(title='Synack Targets')
                table.add_column('#')
                table.add_column('org')
                table.add_column('id')
                table.add_column('slug')
                table.add_column('name')
                table.add_column('collab')
                table.add_column('activated')

                counter = 0
                for record in records:
                    activated_timestamp = datetime.datetime.fromtimestamp(record.activated_at)
                    table.add_row(str(counter), record.target_org_id, record.target_id, record.target_codename, 
                        record.target_name, record.collaboration_criteria,
                        str(activated_timestamp))
                    counter += 1

                console = Console()
                console.print(table)

            selected: str = input("Select a Synack target by #, or leave blank and press enter to cancel: ")
            if '' == selected:
                return
            try:
                selected_no = int(selected)
                self._select_target(selected_no, records)
            except ValueError:
                return
        except Exception as database_exception: # pylint: disable=W0718
            print("*** EXCEPTION ***")
            print(database_exception)