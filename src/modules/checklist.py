"""checklist.py"""
from datetime import datetime
from typing import Any, Generator, List, Literal
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from sqlalchemy import text
from modules.owaspwstg import OWASPWSTG
from modules.database import Database
from modules.input_handler import InputHandler
from models import ChecklistModel, TargetModel
import pandas as pd
from rich.console import Console
from rich.table import Table


class Checklist(): # pylint: disable=R0903
    """Checklist."""
    def __init__(self, app_obj, args) -> None:
        self.app_obj = app_obj
        self.args = args
        self.checklist_items = None
        self.start_index = 0
        self.end_index = 0
        self.previous_start_index = 0
        self.previous_end_index = 0
        self.prompt_user = False
        self.page_counter = 0
        self.select_an_item = False
        self.selected_no = None
        self.goto_next_item = False
        self.kb = KeyBindings()
        self.press_left = False
        self.press_right = False

        @self.kb.add_binding(Keys.Left)
        def _(event):
            self.press_left = True
            self.press_right = False

            self.goto_previous_item = True
            self.goto_next_item = False

            self.prompt_user = False
            self.prompt_running = False
            self.select_an_item = False
            raise KeyboardInterrupt

        @self.kb.add_binding(Keys.Right)
        def _(event):
            self.press_right = True
            self.press_left = False

            self.goto_previous_item = False
            self.goto_next_item = True

            self.prompt_user = False
            self.prompt_running = False
            self.select_an_item = False
            raise KeyboardInterrupt

    def _handle_input(self, args):
        """Handle Input."""
        self.args = args

        if len(self.args) < 2:
            return

        try:
            class_name = self.args[0]
            if class_name == 'checklists':
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

    def _classhelp(self) -> None:
        """Help for Checklist class.

        Returns:
            None
        """
        print("\nChecklists:")

    def _paginated_print(self, data, page_size=25):
        """Prints data in paginated format.

        Args:
            data: A list of lists or a 2D array representing the data to be printed.
            page_size: The number of records to display per page.
        """
        self.start_index = 0
        self.end_index = page_size
        df = pd.DataFrame(data)
        df.index.name = '#'
        running = True
        while running and self.start_index < len(data):
            self.prompt_user = True
            try:
                page_data = df.iloc[self.start_index:self.end_index]

                table = Table()
                table.add_column('#')
                table.add_column('id')
                table.add_column('name')
                table.add_column('# Notes')

                for record in page_data[0]:
                    table.add_row(str(self.page_counter), record.item_id, record.item_name, str('' if record.note_count == 0 else record.note_count))
                    self.page_counter += 1

                console = Console()
                console.print(table)
            except Exception as exc:
                print(exc)

            print("What would you like to do next ([enter]=next page; [# + enter]=select an item, [f + enter]=mark as favorite, [x + enter]=stop)?")
            prompt_session = PromptSession()
            while self.prompt_user:
                text = prompt_session.prompt(' > ')
                if '' == text:
                    self.prompt_user = False
                    running = True
                    self.select_an_item = False
                    self.press_right = True
                    self.press_left = False
                else:
                    try:
                        selected_no = int(text)
                        self.selected_no = selected_no
                        self.prompt_user = False
                        running = False
                        self.select_an_item = True
                    except ValueError:
                        self.prompt_user = False
                        running = False
                        self.select_an_item = False

            self.previous_start_index = self.start_index
            self.previous_end_index = self.end_index

            self.start_index += page_size
            self.end_index += page_size

    def _get_checklist(self, checklist_name):
        """Get checklist."""
        checklists: List = []
        self.start_index = 0
        self.end_index = 0
        self.previous_start_index = 0
        self.previous_end_index = 0
        self.page_counter = 0

        try:
            with Database._get_db() as db:
                selected_target: TargetModel = self.app_obj._get_selected_target()
                if selected_target:
                    query = text("SELECT id, name, checklist_version, category, category_id, category_order," + 
                                "item_id, item_name, objectives, useful_tools, link, created_timestamp," + 
                                "modified_timestamp, active, " +
                                "(SELECT count(*) FROM targetnote WHERE target_id=:targetid " + 
                                "AND checklist_item_id=checklist.item_id) as note_count " + 
                                " FROM checklist " + 
                                "WHERE name=:name " + 
                                "ORDER BY category_order, item_id")
                    result = db.execute(query, {"targetid": selected_target.id,"name": checklist_name})
                    records = result.fetchall()

                else:
                    records: List[ChecklistModel] = db.query(ChecklistModel)\
                        .filter(ChecklistModel.active == True)\
                        .filter_by(name=checklist_name)\
                        .order_by(ChecklistModel.category_order,ChecklistModel.item_id)\
                        .all()
                
                for record in records:
                    checklist_record = ChecklistModel(
                        category = record.category,
                        item_id = record.item_id,
                        name = record.name,
                        checklist_version = record.checklist_version,
                        item_name = record.item_name,
                        objectives = record.objectives,
                        useful_tools = record.useful_tools,
                        link = record.link,
                        note_count = record.note_count
                    )
                    checklists.append(checklist_record)
        except Exception as exc: # pylint: disable=W0718
            print(exc)
        return checklists

    def _select_checklist_record(self, selected_no: int, checklist_record: ChecklistModel):
        """View Checklist Record"""
        self.app_obj._clear()

        selected_target: TargetModel = self.app_obj._get_selected_target()
        if selected_target:
            print(f"Target: {selected_target.name}")
            print('---------' + '-'*len(selected_target.name))
            print()

        print(checklist_record.name,checklist_record.checklist_version)
        print()
        print(checklist_record.category.upper())
        print()
        print(f"{checklist_record.item_id}: {checklist_record.item_name}")
        print()
        
        print(checklist_record.link)
        print()

        if checklist_record.objectives is not None:
            print("Objectives:")
            print("-----------")
            if ';' in checklist_record.objectives:
                objectives = checklist_record.objectives.split(";")
                for objective in objectives:
                    print(f"- {objective}")
            else:
                print(checklist_record.objectives)

        if checklist_record.useful_tools is not None:
            print("\nPotential useful tools:")
            print("-----------------------")
            useful_tools = checklist_record.useful_tools.split(";")
            for tool in useful_tools:
                print(f"- {tool}")

        if selected_target:
            try:
                self.app_obj.targetnotes._get_checklist_notes(selected_target, checklist_record)
            except Exception as exc:
                pass

        print()
        if selected_target:
            print("What would you like to do next ([enter]=next record; [n + enter]=add a note; [x + enter]=stop)?")
        else:
            print("What would you like to do next ([enter]=next record; [x + enter]=stop)?")

        prompt_session = PromptSession()

        self.prompt_user = True
        self.goto_next_item = False
        self.select_an_item = False
        continue_loop = True
        while self.prompt_user and continue_loop:
            text = prompt_session.prompt(' > ')
            if '' == text:
                self.prompt_user = False
                self.select_an_item = False
                self.goto_next_item = True
                continue_loop = False
            elif 'n' == text.lower():
                try:
                    text = f'note add [[item_id={checklist_record.item_id}]]'
                    handler = InputHandler(self.app_obj, text)
                    handler._handle_input()
                except Exception as exc:
                    print(exc)
            else:
                try:
                    selected_no = int(text)
                    self.selected_no = selected_no
                    self.prompt_user = False
                    self.select_an_item = True
                    continue_loop = False
                    self._select_checklist_record(selected_no, checklist_record)
                except ValueError:
                    self.prompt_user = False
                    self.select_an_item = False
                    continue_loop = False

        if self.goto_next_item:
            self.select_an_item = False
            self.goto_next_item = False
            try:
                selected_no = int(self.selected_no)
                selected_no += 1
                self.selected_no = selected_no
                if self.selected_no > len(self.checklist_items):
                    return
                self._select_checklist_record(self.selected_no, self.checklist_items[self.selected_no])
            except ValueError:
                print("ERROR: Invalid input. Input a valid number.")


    def owasp_wstg(self) -> None:
        """OWASP Web Security Testing Guide (WSTG)"""
        print("OWASP Web Security Testing Guide")

        self.start_index = 0
        self.end_index = 0
        self.previous_start_index = 0
        self.previous_end_index = 0

        checklist_name = 'OWASP Web Security Testing Guide'
        self.checklist_items: list = self._get_checklist(checklist_name)
        self._paginated_print(self.checklist_items)
        if self.select_an_item and self.selected_no is not None:
            try:
                selected_no = int(self.selected_no)
                self._select_checklist_record(selected_no, self.checklist_items[selected_no])
            except ValueError:
                print("ERROR: Invalid input. Input a valid number.")
