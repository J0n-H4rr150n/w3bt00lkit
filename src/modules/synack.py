"""synack.py"""
import os
import sys
import datetime
import requests
from datetime import timezone
from sqlalchemy.orm.query import Query
from typing import List, Literal, LiteralString
from rich.console import Console
from rich.table import Table
from rich.text import Text
from modules.database import Database
from models import SynackTargetModel, TargetModel
from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.shortcuts import input_dialog
from sqlalchemy import desc, or_, select, func
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

load_dotenv()


class Synack:
    """Synack."""
    def __init__(self, app_obj, args):
        self.app_obj = app_obj
        self.args = args
        self.prompt_user = False
        self.synack_base = os.environ.get("SYNACK_BASE")
        self.synack_api = os.environ.get("SYNACK_API")
        self.slack_url = os.environ.get("SLACK_URL")
        self.slack_slug = os.environ.get("SLACK_SLUG")

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
                    .order_by(SynackTargetModel.activated_at).all()
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
            print("*** SYNACK EXCEPTION ***")
            print(database_exception)

    def put_request(self, vars: dict, url: str, payload):
        """PUT request."""
        if self.app_obj.auth_token is not None and 'undefined' != self.app_obj.auth_token:
            max_retries = 3
            current_retries = 0
            cookies = {}
            headers = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-US,en;q=0.9',
                'Authorization': f'Bearer {self.app_obj.auth_token}',
                'Cache-Control': 'no-cache',
                'Content-Type': 'application/json',
                'Content-Length': '27',
                'Pragma': 'no-cache',
                'Referer': f'{self.synack_base}/',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Origin': self.synack_base,
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
                'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Linux"',
                'Connection': 'close'
            }

            response = requests.put(url, headers=headers, data=payload)
            try:
                if response.status_code == 401:
                    print("\nNeed to refresh credentials.")
                    if current_retries > max_retries:
                        print("Process halted!")
                    else:
                        print("Waiting to see if mitmproxy will refresh...")
                        current_retries = current_retries + 1
                        time.sleep(30)
                elif response.status_code == 400:
                    print("BAD REQUEST:")
                    print(response.__dict__)

                    headers = {
                            'Accept': '*/*',
                            'Accept-Language': 'en-US,en;q=0.9',
                            'Authorization': f'Bearer {self.app_obj.auth_token}',
                            'Cache-Control': 'no-cache',
                            'Connection': 'keep-alive',
                            'Pragma': 'no-cache',
                            'Referer': f'{self.synack_base}/',
                            'Sec-Fetch-Dest': 'empty',
                            'Sec-Fetch-Mode': 'cors',
                            'Sec-Fetch-Site': 'same-origin',
                            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
                            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
                            'sec-ch-ua-mobile': '?0',
                            'sec-ch-ua-platform': '"Linux"'
                        }

                    print("")
                    response_two = requests.put(url, headers=headers, data=payload)
                    print(response_two.status_code)
                    print(response_two.text)
                    print("")

                elif response.status_code == 200:
                    json = response.json()
                    print("\nResults @",datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
                    print(json)
                    print("+--------\n")
                    return json
                elif response.status_code == 404:
                    json = response.json()
                    print("\nResults @",datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
                    print("Please select a different target. This one is not currently available.\n")
                    # TODO - Set this target as inactive in the database.
                    return json 
                else:
                    print(url, headers, payload)
                    print("------")
                    print(response)
                    print("------")
                    print("OTHER. Need to refresh credentials? Proxy stopped working?")
            except Exception as exc:
                print(exc)
                print("\nProcess halted! [EXCPH0001]\n")

    def _select_target(self, selected_no: int, targets: List[TargetModel]):
        """Select a target

        Args:
            selection (int): The number of the selected target in the targets list.

        Returns:
            None
        """
        print("Select target #:", selected_no)
        selected_target: TargetModel = targets[selected_no]
        self.app_obj._callback_set_synack_target(selected_target)

    def _switch_target(self, target_slug) -> None:
        """Switch target

        Args:
            selection (str): The taret slug.

        Returns:
            None
        """
        if target_slug is not None and len(target_slug) == 10:
            vars = {}
            url = f'{self.synack_base}/api/launchpoint'
            data = '{\"listing_id\":\"' + target_slug + '\"}'
            results = self.put_request(vars, url, data)
            if results is not None:
                if 'connected' == results["status"]:
                    return True
        return False
