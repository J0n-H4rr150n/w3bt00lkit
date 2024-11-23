"""proxyhelper.py"""
import sys
import signal
from datetime import datetime, timezone
import warnings
from urllib.parse import ParseResult, urlparse
from mitmproxy import http
from sqlalchemy.orm.session import Session
from modules.database import Database as ProxyDatabase
from models import ProxyModel

# pylint: disable=C0121,W0718,R0914

warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=UserWarning)

request_url_list = set()

def signal_handler(sig, frame) -> None: # pylint: disable=W0613
    """Signal handler.
    
    Args:
        sig: The signal to handle.
        frame: The frame to handle.

    Returns:
        None
    """
    print("\n\nProcess halted!")
    timestamp_end: str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    print("Ended at:",timestamp_end,"(UTC)")
    print("")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

class ProxyHelper:
    """ProxyHelper."""
    target: str = ''
    exclusion_list: list = []

    def __init__(self, target, in_scope, parent_callback_proxy_message) -> None:
        self.target = target
        self.in_scope = in_scope
        self._parent_callback_proxy_message = parent_callback_proxy_message
        #print("proxyhelper.py >", target)
        #print("proxyhelper.py > in scope,  > ", in_scope)
        #if self.in_scope is not None:
        #    for item in in_scope:
        #        if item['fqdn'] is not None:
        #            print(item['fqdn'])

    def request(self, flow: http.HTTPFlow) -> None: # pylint: disable=R0914
        """Proxy request.
        
        Args:
            flow: The flow object for the request.

        Returns:
            None
        """
        #for exclusion in self.exclusion_list:
        #    if exclusion in flow.request.host:
        #        print("Skip: %s", exclusion)
        #        return

        if self.target is None or self.in_scope is None:
            return

        save_request = False
        for item in self.in_scope:
            if item['fqdn'] is not None:
                if flow.request.host == item['fqdn']:
                    save_request = True
                if '*' in item['fqdn']:
                    tmp_fqdn = item['fqdn'].replace('*','')
                    if flow.request.host.endswith(tmp_fqdn):
                        save_request = True

        if save_request == False:
            return

        #self._parent_callback_proxy_message(f"REQUEST: {flow.request.pretty_url}")

        request = flow.request

        host = flow.request.host
        port = flow.request.port
        method = flow.request.method
        scheme = flow.request.scheme
        authority = flow.request.authority
        path = flow.request.path

        try:
            content = flow.request.text.replace('\x00', '')
        except Exception as exc:
            self._parent_callback_proxy_message(f"REQUEST: clean content exception - {exc}")

        timestamp_start = flow.request.timestamp_start
        timestamp_end = flow.request.timestamp_end

        full_url: str = f'{request.scheme}://{request.host}:{request.port}{request.path}'

        parsed: ParseResult = urlparse(full_url)
        path: str = parsed.path
        url: str = f'{parsed.scheme}://{parsed.netloc.replace(":443","")}{parsed.path}'

        try:
            proxy_database = ProxyDatabase()
            db_session: Session = proxy_database.session_local()

            headers_string = ", ".join([f"{k}: {v}" for k, v in flow.request.headers.items()])

            new_request = ProxyModel(
                target_id=int(self.target['id']),
                name=None,
                request=None,
                action='Request',
                host=host,
                port=port,
                method=method,
                scheme=scheme,
                authority=authority,
                path=path,
                headers=headers_string,
                content=content,
                timestamp_start=timestamp_start,
                timestamp_end=timestamp_end,
                full_url=full_url,
                parsed_full_url=str(parsed),
                parsed_path=path,
                parsed_url=url
            )

            #self._parent_callback_proxy_message(new_request.__dict__)

            proxy_database._add_request(db_session, new_request) # pylint: disable=W0212
        except Exception as database_exception: # pylint: disable=W0718
            self._parent_callback_proxy_message("REQUEST: database_exception - ", database_exception)
            print("Database exception:",database_exception)

    def response(self, flow: http.HTTPFlow) -> None:
        """Proxy response.
        
        Args:
            flow: The flow object for the response.

        Returns:
            None
        """

        #self._parent_callback_proxy_message(flow.request.host)

        if self.target is None or self.in_scope is None:
            self._parent_callback_proxy_message("RESPONSE: self in_scope is none")
            return

        save_response = False

        try:
            for item in self.in_scope:
                if item['fqdn'] is not None:
                    if flow.request.host == item['fqdn']:
                        save_response = True
                    if '*' in item['fqdn']:
                        tmp_fqdn = item['fqdn'].replace('*','')
                        if flow.request.host.endswith(tmp_fqdn):
                            save_response = True
            if save_response == False:
                return
        except Exception as exc:
            self._parent_callback_proxy_message(f"{flow.request.pretty_url} ---> \n {exc}")

        request = flow.request

        host = flow.request.host
        port = flow.request.port
        method = flow.request.method
        scheme = flow.request.scheme
        authority = flow.request.authority
        path = flow.request.path

        headers = flow.request.headers

        try:
            content = flow.request.text.replace('\x00', '')
        except Exception as exc:
            self._parent_callback_proxy_message(f"RESPONSE: clean content exception - {exc}")

        timestamp_start = flow.request.timestamp_start
        timestamp_end = flow.request.timestamp_end

        full_url: str = f'{request.scheme}://{request.host}:{request.port}{request.path}'

        parsed: ParseResult = urlparse(full_url)
        path: str = parsed.path
        url: str = f'{parsed.scheme}://{parsed.netloc.replace(":443","")}{parsed.path}'

        try:
            proxy_database = ProxyDatabase()
            db_session: Session = proxy_database.session_local()

            #headers_string = ", ".join([f"{k}: {v}" for k, v in flow.response.headers.items()])

            new_request = ProxyModel(
                target_id=int(self.target['id']),
                name=None,
                request=None,
                action='Response',
                response_status_code=flow.response.status_code,
                response_reason=flow.response.reason,
                response_headers=None,
                response_text=flow.response.text,
                host=host,
                port=port,
                method=method,
                scheme=scheme,
                authority=authority,
                path=path,
                headers=str(headers),
                content=content,
                timestamp_start=timestamp_start,
                timestamp_end=timestamp_end,
                full_url=full_url,
                parsed_full_url=str(parsed),
                parsed_path=path,
                parsed_url=url
            )

            proxy_database._add_request(db_session, new_request) # pylint: disable=W0212
        except Exception as database_exception: # pylint: disable=W0718
            self._parent_callback_proxy_message("RESPONSE: database_exception - ", database_exception)
            print("Response database exception:", database_exception)
