"""owaspwstg.py"""
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from sqlalchemy.orm.session import Session
from typing import Any, Generator, List, Literal
import pandas as pd
from tabulate import tabulate
from modules.database import Database
from models import ChecklistModel
from .common import word_completer

# pylint: disable=C0103,W0603,W0212,R0903

current_obj_instance = None
go_to_next = False
prompt_user = True


class OWASPWSTGz():
    """OWASP Web Security Testing Guide (WSTG)"""

    def __init__(self, parent_obj, handle_input, callback_word_completer) -> None:
        self.parent_obj = parent_obj
        self._parent_callback_word_completer = callback_word_completer
        self._handle_input = handle_input
        self.session = PromptSession()
        self.completer: WordCompleter = word_completer(self)
        self.checklist_items = None
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

    def _paginated_print_x(self, data, page_size=25):
        """Prints data in paginated format.

        Args:
            data: A list of lists or a 2D array representing the data to be printed.
            page_size: The number of records to display per page.
        """

        start_index = 0
        end_index = page_size
        df = pd.DataFrame(data)
        df.index.name = '#'
        running = True
        while running and start_index < len(data):
            global prompt_user
            prompt_user = True
            page_data = df.iloc[start_index:end_index]
            print(tabulate(page_data, headers='keys', tablefmt='psql'))
            print("zzWhat would you like to do next ([enter]=select an item, [n + enter]=next page)?")
            prompt_session = PromptSession(key_bindings=self.kb)

            while prompt_user:
                text = prompt_session.prompt(' > ')
                if '' == text:
                    prompt_user = False
                    running = False
                    self.press_right = True
                    self.press_left = False
                elif 'n' == text:
                    prompt_user = False
                    running = True

            self.previous_start_index = self.start_index
            self.previous_end_index = self.end_index

            if self.press_right:
                self.start_index += page_size
                self.end_index += page_size
            elif self.press_left:
                if self.start_index > 0:
                    self.start_index -= page_size
                    self.end_index -= page_size
                else:
                    return

    def _classhelp(self):
        """Help for Web Security Testing Guide (WSTG).

        Returns:
            None
        """
        print("\nWeb Security Testing Guide (WSTG):")
        try:
            checklist_name = 'OWASP Web Security Testing Guide'
            self.checklist_items = []
            try:
                with Database._get_db() as db:
                    records: List[ChecklistModel] = db.query(ChecklistModel)\
                        .filter(ChecklistModel.active == True)\
                        .filter_by(name=checklist_name)\
                        .order_by(ChecklistModel.category_order,ChecklistModel.item_id)\
                        .all()
                    for record in records:
                        checklist_record = {
                            'item_id': record.item_id,
                            'item_name': record.item_name,
                            'item_category': record.useful_tools
                        }
                        self.checklist_items.append(checklist_record)
            except Exception as exc: # pylint: disable=W0718
                print(exc)

            self._paginated_print(self.checklist_items)
            selected: str = input("Select a checklist item by # or item_id (leave blank to cancel): ")
            if '' == selected:
                print("No input in owaspwstg.py... return")
                self._parent_callback_word_completer(self.parent_obj,"_classhelp",self.parent_obj)
                return
            for checklist_item in self.checklist_items:
                if selected == checklist_item['item_id']:
                    print("Found it!")
                    print("Go to a page for:")
                    print(checklist_item)
                    self._parent_callback_word_completer(self.parent_obj,"_classhelp",self.parent_obj)
                    return
            try:
                selected_no = int(selected)
                print("Selected number:",selected_no)
                print("Found it!")
                print("Go to a page for:")
                print(self.checklist_items[selected_no])
                self._parent_callback_word_completer(self.parent_obj,"_classhelp",self.parent_obj)
            except ValueError:
                print("ERROR: Invalid input. Input a valid number.")
                self._parent_callback_word_completer(self.parent_obj,"_classhelp",self.parent_obj)
        except Exception as database_exception: # pylint: disable=W0718
            print(database_exception)
            self._parent_callback_word_completer(self.parent_obj,"_classhelp",self.parent_obj)
