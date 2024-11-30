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


class OWASPWSTG():
    """OWASP Web Security Testing Guide (WSTG)"""

    def __init__(self, parent_obj, handle_input, callback_word_completer) -> None:
        self.parent_obj = parent_obj
        self._parent_callback_word_completer = callback_word_completer
        self._handle_input = handle_input
        self.session = PromptSession()
        self.completer: WordCompleter = word_completer(self)
        self.checklist_items = None

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
            print("What would you like to do next ([enter]=select an item, [n + enter]=next page)?")
            prompt_session = PromptSession()

            while prompt_user:
                text = prompt_session.prompt(' > ')
                if '' == text:
                    prompt_user = False
                    running = False
                elif 'n' == text:
                    prompt_user = False
                    running = True

            start_index += page_size
            end_index += page_size

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
