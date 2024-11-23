"""proxy.py"""
import asyncio
import threading
import logging
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from mitmproxy import options
from mitmproxy.tools import dump
from modules.proxyhelper import ProxyHelper
from .common import word_completer

BASE_CLASS_NAME = 'W3bT00lkit'
proxy_running = False # pylint: disable=C0103
stop_flag = False # pylint: disable=C0103

logging.basicConfig(filename='proxy-error.log', level=logging.ERROR)

class ProxyConfig: # pylint: disable=R0902,R0903
    """Proxy Config."""

    def __init__(self) -> None:
        self.name = 'config'
        self.session = PromptSession()
        self.completer: WordCompleter = word_completer(self)
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

    def __init__(self, parent_obj, callback_get_base_name, callback_word_completer, callback_proxy_message) -> None:
        self.parent_obj = parent_obj
        self._parent_callback_get_base_name = callback_get_base_name
        self._parent_callback_word_completer = callback_word_completer
        self._parent_callback_proxy_message = callback_proxy_message
        self.base_name: str = self._parent_callback_get_base_name()
        self.name = 'proxy'
        self.session = PromptSession()
        self.completer: WordCompleter = word_completer(self)
        self.loop = asyncio.new_event_loop()
        self.stop_event = None
        self.threading_task = None
        self.proxy_task = None
        self.configurations = {}
        self.proxyconfig_obj = ProxyConfig()
        self.stopping = False
        self.master = None

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
            self.parent_obj._exit() # pylint: disable=W0212

    def _loop_in_thread(self, loop) -> None:
        global stop_flag # pylint: disable=W0603
        while not stop_flag:
            try:
                host = 'localhost'
                port = 8085
                target = self.parent_obj.selected_target_obj
                in_scope = self.parent_obj.selected_target_in_scope
                enable_upstream = False
                upstream_host = None
                upstream_port = None
                asyncio.set_event_loop(loop)
                asyncio.run(self._start_proxy(host, port, target, in_scope, enable_upstream,
                                              self._parent_callback_proxy_message, upstream_host, upstream_port)
                                              )
            except Exception as exc: # pylint: disable=W0718
                print(exc)
                logging.error(exc)
            finally:
                stop_flag = True
                threading.Event().set()

    async def _start_proxy(self, host, port, target, in_scope, enable_upstream, parent_callback_proxy_message, # pylint: disable=R0913,R0917
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
                        self.master.addons.add(ProxyHelper(target, in_scope, parent_callback_proxy_message))
                        await self.master.run()
                    except asyncio.CancelledError:
                        print("*** self.master asyncio cancelled ***")
                    except Exception as exc: # pylint: disable=W0718
                        print("*** self.master EXCEPTION ***")
                        print(exc)
                    finally:
                        running = False
                        print("Proxy stopped.")

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
        print("Stopping the proxy.")
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
