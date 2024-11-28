"""proxy.py"""
import asyncio
import threading
import logging
from datetime import datetime
from typing import List
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from mitmproxy import options
from mitmproxy.tools import dump
from rich.console import Console
from rich.table import Table
from sqlalchemy import desc
import pandas as pd
from modules.proxyhelper import ProxyHelper
from modules.database import Database
from models import ProxyModel, TargetModel

BASE_CLASS_NAME = 'W3bT00lkit'
proxy_running = False # pylint: disable=C0103
stop_flag = False # pylint: disable=C0103

logging.basicConfig(filename='proxy-error.log', level=logging.ERROR)

class ProxyConfig: # pylint: disable=R0902,R0903
    """Proxy Config."""

    def __init__(self, app_obj, args) -> None:
        self.app_obj = app_obj
        self.args = args
        #self.name = 'config'
        #self.session = PromptSession()
        #self.completer: WordCompleter = word_completer(self)
        self.loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
        self.configurations: dict = {}

    def _get(self, item) -> str:
        return self.configurations[item] or None

    def _set(self, item, value) -> None:
        self.configurations[item] = value

    def view(self) -> None:
        """View configurations."""
        print("Config:")
        print(self.configurations)

class Proxy(): # pylint: disable=R0902
    """Proxy."""

    def __init__(self, app_obj, args) -> None:
        self.app_obj = app_obj
        self.args = args
        #self.parent_obj = parent_obj
        #self._parent_callback_get_base_name = callback_get_base_name
        #self._parent_callback_word_completer = callback_word_completer
        #self._parent_callback_proxy_message = callback_proxy_message
        #self.base_name: str = self._parent_callback_get_base_name()
        #self.name = 'proxy'
        self.session = PromptSession()
        self.loop = asyncio.new_event_loop()
        self.stop_event = None
        self.threading_task = None
        self.proxy_task = None
        self.configurations = {}
        self.proxyconfig_obj = ProxyConfig(app_obj, args)
        self.stopping = False
        self.master = None
        self.prompt_user = False
        self.page_counter = 0
        self.proxy_records: List[ProxyModel] = []
        self.select_an_item = False
        self.selected_no = None
        self.previous_start_index = 0
        self.previous_start_index = 0
        self.start_index = 0
        self.end_index = 0
        self.goto_next_item = False

    def _handle_input(self, args):
        """Handle Input."""
        self.args = args
        if len(self.args) < 2:
            return
        elif len(self.args) == 3:
            try:
                class_name = self.args[0]
                function_name = self.args[1]
                action_name = self.args[2]
                args = []
                func = getattr(self, f"_{function_name}_{action_name}")
                if callable(func):
                    func(*args)
                else:
                    print('Else: Function is not callable:%s',function_name)
            except AttributeError:
                return
            except Exception as exc:
                print(exc)
        elif len(self.args) == 4:
            try:
                class_name = self.args[0]
                function_name = self.args[1]
                action_name = self.args[2]
                
                action_filter = self.args[3]
                args = []
                args.append(action_filter)

                func = getattr(self, f"_{function_name}_{action_name}")
                if callable(func):
                    func(*args)
                else:
                    print('Else: Function is not callable:%s',function_name)
            except AttributeError:
                return
            except Exception as exc:
                print(exc)
        else:
            try:
                class_name = self.args[0]
                if class_name == 'proxy':
                    function_name = self.args[1]
                else:
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

    def _get(self, item) -> str:
        return self.configurations[item] or None

    def _set(self, item, value) -> None:
        self.configurations[item] = value

    def start(self) -> None:
        """Start the proxy.

        Returns:
            None
        """
        if proxy_running == False: # pylint: disable=C0121
            if self.loop is None:
                self.loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            if self.stop_event is None:
                self.stop_event = threading.Event()
            if self.threading_task is None:
                self.threading_task = threading.Thread(target=self._loop_in_thread, args=(self.loop,), daemon=True)
                self.threading_task.start()
                print("Proxy started...")
            else:
                global stop_flag # pylint: disable=W0603
                stop_flag = False
                self.threading_task = threading.Thread(target=self._loop_in_thread, args=(self.loop,), daemon=True)
                self.threading_task.start()
                print("Proxy started again...")
        else:
            print("*** ERROR: Loop is already running. ***")
            self.app_obj._exit() # pylint: disable=W0212

    def _loop_in_thread(self, loop) -> None:
        global stop_flag # pylint: disable=W0603
        while not stop_flag:
            try:
                host = 'localhost'
                port = 8085
                target = self.app_obj.selected_target
                in_scope = self.app_obj.selected_target_in_scope
                enable_upstream = False
                upstream_host = None
                upstream_port = None
                asyncio.set_event_loop(loop)
                asyncio.run(self._start_proxy(host, port, target, in_scope, enable_upstream,
                                              self.app_obj._callback_proxy_message, upstream_host, upstream_port)
                                              )
            except Exception as exc: # pylint: disable=W0718
                print(exc)
                logging.error(exc)
            finally:
                stop_flag = True
                threading.Event().set()

    async def _start_proxy(self, host, port, target, in_scope, enable_upstream, callback_proxy_message, # pylint: disable=R0913,R0917
                           upstream_host = None, upstream_port = None
                           ) -> None: # pylint: disable=R0913,R0917
        """Start proxy.

        Args:
            host (str): The name of the host.
            port (int): The port to use.
            target (str): The name of the target.
            enable_upstream (bool): Enable an upstream proxy (True,False).

        Returns:
            None
        """
        try:
            if enable_upstream:
                upstream: list[str] = [f'upstream:http://{upstream_host}:{upstream_port}']
                opts = options.Options(listen_host=host, listen_port=port, mode=upstream, ssl_insecure=True)
            else:
                opts = options.Options(listen_host=host, listen_port=port, ssl_insecure=True)

            self.master = dump.DumpMaster(
                opts,
                with_termlog=False,
                with_dumper=False,
            )

            running = False
            global stop_flag # pylint: disable=W0602
            while not stop_flag:
                if running == False: # pylint: disable=C0121
                    running = True
                    try:
                        self.master.addons.add(ProxyHelper(target, in_scope, callback_proxy_message))
                        await self.master.run()
                    except asyncio.CancelledError:
                        print("*** self.master asyncio cancelled ***")
                    except Exception as exc: # pylint: disable=W0718
                        print("*** self.master EXCEPTION ***")
                        print(exc)
                    finally:
                        running = False

        except Exception as exc: # pylint: disable=W0718
            logging.error(exc)
            print("*** PROXY EXCEPTION ***")
            print(exc)
        finally:
            print("*** Proxy has exited. ***")

    def stop(self) -> None:
        """Stop proxy.

        Returns:
            None
        """
        print("Stopping the proxy...")
        if self.master is not None:
            try:
                self.master.shutdown()
                if self.loop is not None:
                    self.loop.close()
                global stop_flag # pylint: disable=W0603
                stop_flag = True
                self.threading_task.join()
            except Exception as exc: # pylint: disable=W0718
                print(exc)
            print()

    def options(self) -> None:
        """Proxy options.
        
        Returns:
            None
        """
        print("\nDefault options:\n")
        print("- Only store requests that are `in scope` for the selected `target`.")
        print("")

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
                table.add_column('created')
                table.add_column('full_url')

                for record in page_data[0]:
                    start_timestamp_obj = datetime.fromtimestamp(record.timestamp_start)
                    start_timestamp = start_timestamp_obj.strftime("%m/%d/%Y %H:%M:%S")
                    table.add_row(str(self.page_counter), start_timestamp, record.full_url)
                    self.page_counter += 1
                
                console = Console()
                console.print(table)
            except Exception as exc:
                print(exc)

            print("What would you like to do next ([enter]=next page; [# + enter]=select an item, [x + enter]=stop)?")
            prompt_session = PromptSession()

            while self.prompt_user:
                text = prompt_session.prompt(' > ')
                if '' == text:
                    self.prompt_user = False
                    running = True
                    self.select_an_item = False
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

    def _select_proxy_record(self, selected_no: int, proxy_record: ProxyModel):
        """View Proxy Record"""
        self.app_obj._clear()
        print(f"\nPROXY RECORD DETAILS\n")

        selected_target: TargetModel = self.app_obj._get_selected_target()
        if selected_target:
         print(f"Target: {selected_target.name}\n")

        print(f"Id: {proxy_record.id}")
        start_timestamp_obj = datetime.fromtimestamp(proxy_record.timestamp_start)
        start_timestamp = start_timestamp_obj.strftime("%m/%d/%Y %H:%M:%S")
        print(f"Created: {start_timestamp}")
        print(f"Action: {proxy_record.action}")
        print(f"Method: {proxy_record.method}")
        print(f"Status: {proxy_record.response_status_code}")
        print("")
        # action
        # method
        # status

        # REQUEST:
        print("REQUEST:")
        print("--------\n")
        print(proxy_record.raw_request)
        
        # RESPONSE:
        print("RESPONSE:")
        print("--------\n")
        print(proxy_record.raw_response)

        print("\n-----------------------------------------\n")

        print("What would you like to do next ([enter]=next record; [# + enter]=select an item, [x + enter]=stop)?")
        prompt_session = PromptSession()

        running = True
        self.prompt_user = True
        self.goto_next_item = False
        self.select_an_item = False
        continue_loop = True
        while self.prompt_user and continue_loop:
            text = prompt_session.prompt(' > ')
            if '' == text:
                self.prompt_user = False
                running = False
                self.select_an_item = False
                self.goto_next_item = True
                continue_loop = False
            else:
                try:
                    selected_no = int(text)
                    self.selected_no = selected_no
                    self.prompt_user = False
                    running = False
                    self.select_an_item = True
                    continue_loop = False
                    print("Number input.")
                except ValueError:
                    self.prompt_user = False
                    running = False
                    self.select_an_item = False
                    continue_loop = False
                    print("Number ValueError.")

        if self.goto_next_item:
            self.select_an_item = False
            self.goto_next_item = False
            try:
                selected_no = int(self.selected_no)
                selected_no += 1
                self.selected_no = selected_no
                if self.selected_no > len(self.proxy_records):
                    return
                else:
                    self._select_proxy_record(self.selected_no, self.proxy_records[self.selected_no])
            except ValueError:
                print("ERROR: Invalid input. Input a valid number.")

    def _history_requests(self, args=None) -> None:
        self.proxy_records = []
        filtered_records: List[ProxyModel] = []
        if args is None:
            with Database._get_db() as db:
                filtered_records: List[ProxyModel] = db.query(ProxyModel).filter(ProxyModel.action=='Request').order_by(desc(ProxyModel.timestamp_start)).all()
                for record in filtered_records:
                    proxy_record = ProxyModel(
                        id=record.id,
                        action=record.action,
                        timestamp_start=record.timestamp_start,
                        method=record.method,
                        response_status_code=record.response_status_code,
                        full_url=record.full_url,
                        raw_request=record.raw_request,
                        raw_response=record.raw_response
                    )
                    self.proxy_records.append(proxy_record)
            self.history(filtered_records)
        else:
            match args[0]:
                case 'js':
                    with Database._get_db() as db:
                        filtered_records: List[ProxyModel] = db.query(ProxyModel)\
                            .filter(ProxyModel.action=='Request')\
                            .filter(ProxyModel.path.endswith('.js'))\
                            .order_by(desc(ProxyModel.timestamp_start)).all()
                        for record in filtered_records:
                            proxy_record = ProxyModel(
                                id=record.id,
                                action=record.action,
                                timestamp_start=record.timestamp_start,
                                method=record.method,
                                response_status_code=record.response_status_code,
                                full_url=record.full_url,
                                raw_request=record.raw_request,
                                raw_response=record.raw_response
                            )
                            self.proxy_records.append(proxy_record)
                    self.history(filtered_records)
                case 'params':
                    pass
                case 'no-media':
                    pass
                case _:
                    return

    def _history_responses(self, args=None) -> None:
        self.proxy_records = []
        filtered_records: List[ProxyModel] = []
        if args is None:
            with Database._get_db() as db:
                if self.app_obj.selected_target is not None:
                    filtered_records: List[ProxyModel] = db.query(ProxyModel)\
                        .filter(ProxyModel.target_id==self.app_obj.selected_target.id)\
                        .filter(ProxyModel.action=='Response')\
                        .order_by(desc(ProxyModel.timestamp_start)).all()
                else:
                    filtered_records: List[ProxyModel] = db.query(ProxyModel)\
                        .filter(ProxyModel.action=='Response')\
                        .order_by(desc(ProxyModel.timestamp_start)).all()
                for record in filtered_records:
                    proxy_record = ProxyModel(
                        id=record.id,
                        action=record.action,
                        timestamp_start=record.timestamp_start,
                        method=record.method,
                        response_status_code=record.response_status_code,
                        full_url=record.full_url,
                        raw_request=record.raw_request,
                        raw_response=record.raw_response
                    )
                    self.proxy_records.append(proxy_record)
            self.history(filtered_records)
        else:
            match args:
                case 'js':
                    with Database._get_db() as db:
                        if self.app_obj.selected_target is not None:
                            filtered_records: List[ProxyModel] = db.query(ProxyModel)\
                                .filter(ProxyModel.target_id==self.app_obj.selected_target.id)\
                                .filter(ProxyModel.action=='Response')\
                                .filter(ProxyModel.path.endswith('.js'))\
                                .order_by(desc(ProxyModel.timestamp_start)).all()
                        else:
                            filtered_records: List[ProxyModel] = db.query(ProxyModel)\
                                .filter(ProxyModel.action=='Response')\
                                .filter(ProxyModel.path.endswith('.js'))\
                                .order_by(desc(ProxyModel.timestamp_start)).all()

                        for record in filtered_records:
                            proxy_record = ProxyModel(
                                id=record.id,
                                action=record.action,
                                timestamp_start=record.timestamp_start,
                                method=record.method,
                                response_status_code=record.response_status_code,
                                full_url=record.full_url,
                                raw_request=record.raw_request,
                                raw_response=record.raw_response
                            )
                            self.proxy_records.append(proxy_record)
                    self.history(filtered_records)
                case 'params':
                    pass
                case 'no-media':
                    pass
                case _:
                    return

    def history(self, filtered_records=None) -> None:
        """Proxy History."""
        self.proxy_records = []
        if filtered_records is not None:
            self.proxy_records = filtered_records
        else:
            with Database._get_db() as db:
                if self.app_obj.selected_target is not None:
                    records: List[ProxyModel] = db.query(ProxyModel)\
                        .filter(ProxyModel.target_id==self.app_obj.selected_target.id)\
                        .order_by(desc(ProxyModel.timestamp_start)).all()
                else:
                    records: List[ProxyModel] = db.query(ProxyModel).order_by(desc(ProxyModel.timestamp_start)).all()
                for record in records:
                    proxy_record = ProxyModel(
                        id=record.id,
                        action=record.action,
                        timestamp_start=record.timestamp_start,
                        method=record.method,
                        response_status_code=record.response_status_code,
                        full_url=record.full_url,
                        raw_request=record.raw_request,
                        raw_response=record.raw_response
                    )
                    self.proxy_records.append(proxy_record)
        self.page_counter = 0
        self._paginated_print(self.proxy_records)
        if self.select_an_item and self.selected_no is not None:
            try:
                selected_no = int(self.selected_no)
                self._select_proxy_record(selected_no, self.proxy_records[selected_no])
            except ValueError:
                print("ERROR: Invalid input. Input a valid number.")
