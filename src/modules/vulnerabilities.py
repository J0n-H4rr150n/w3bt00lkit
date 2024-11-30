"""targets.py"""
from typing import List
from sqlalchemy import func
from sqlalchemy.orm.query import Query
from rich.console import Console
from rich.table import Table
from modules.database import Database
from models import TargetModel, VulnerabilityModel

# pylint: disable=C0121,E1102,R0903,W0212,W0718


class Vulnerabilities:
    """Vulnerabilities."""

    def __init__(self, app_obj, args):
        self.app_obj = app_obj
        self.args = args
        self.vulnerabilities = None
        self.selected_vulnerability = None

    def _handle_input(self, args):
        """Handle Input."""
        self.args = args
        if len(self.args) < 2:
            return

        try:
            class_name = self.args[1]
            function_name = self.args[0]
            args = []
            func = getattr(self, function_name) # pylint: disable=W0621
            if callable(func):
                func(*args)
            else:
                print('Else: Function is not callable:%s',function_name)
        except AttributeError:
            return
        except Exception as exc:
            print(exc)

    def _select_vulnerability(self, selected_no: int, vulnerabilities: List[VulnerabilityModel]):
        """Select a vulnerability

        Args:
            selection (int): The number of the selected vulnerability in the vulnerabilities list.

        Returns:
            None
        """
        self.app_obj._clear()

        selected_target: TargetModel = self.app_obj._get_selected_target()
        if selected_target:
            print(f"Target: {selected_target.name}")

        print("\nVULNERABILITY DETAILS:")

        selected_vulnerability: VulnerabilityModel = vulnerabilities[selected_no]

        table = Table()
        table.add_column('id')
        table.add_column('category id')
        table.add_column('acronym')
        table.add_column('category')

        table.add_row(str(selected_vulnerability.id), 
                      selected_vulnerability.vuln_category_id,
                      selected_vulnerability.category_acronym,
                      selected_vulnerability.category_name
                    )
        console = Console()
        console.print(table)

        print()
        if selected_vulnerability.cheatsheets is not None and len(selected_vulnerability.cheatsheets) > 0:
            print("CHEATSHEETS:")
            for record in selected_vulnerability.cheatsheets:
                print(f"- {record['link']}")

        print()
        if selected_vulnerability.payload_lists is not None and len(selected_vulnerability.payload_lists) > 0:
            print("PAYLOAD LISTS:")
            for record in selected_vulnerability.payload_lists:
                print(f"- {record['link']}")

        print()
        if selected_vulnerability.references is not None and len(selected_vulnerability.references) > 0:
            print("REFERENCES:")
            for record in selected_vulnerability.references:
                print(f"- {record['link']}")

        print()
        if selected_vulnerability.tools is not None and len(selected_vulnerability.tools) > 0:
            print("TOOLS:")
            for record in selected_vulnerability.tools:
                print(f"- {record['link']}")

        print()
        if selected_vulnerability.tests is not None and len(selected_vulnerability.tests) > 0:
            print("SAMPLE TESTS:\n")
            counter = 1
            for record in selected_vulnerability.tests:
                output = f"{counter}: {record['name']}"
                print(output)
                print("-" * len(output))
                counter += 1
                print()
                payloads = set()
                for example in record['examples']:
                    for payload in example['payloads']:
                        payloads.add(payload)
                for payload in payloads:
                    print(payload)
                print()

        print()

    def view(self):
        """List all active vulnerabilities.

        Returns:
            None
        """
        print("")
        try:
            with Database._get_db() as db:
                records: List[VulnerabilityModel] = db.query(VulnerabilityModel)\
                    .filter(VulnerabilityModel.active == True)\
                    .order_by(VulnerabilityModel.vuln_category_id).all()

                table = Table(title='Vulnerabilities')
                table.add_column('#')
                table.add_column('acronym')
                table.add_column('category')

                counter = 0
                for record in records:
                    table.add_row(str(counter), record.category_acronym, record.category_name)
                    counter += 1

                console = Console()
                console.print(table)

            selected: str = input("Select a vulnerability by #, or leave blank and press enter to cancel: ")
            if '' == selected:
                return
            try:
                selected_no = int(selected)
                self._select_vulnerability(selected_no, records)
            except ValueError:
                return
        except Exception as database_exception: # pylint: disable=W0718
            print("*** EXCEPTION ***")
            print(database_exception)
