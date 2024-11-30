"""proxyhelper.py"""
import re
import sys
import signal
from datetime import datetime, timezone
import warnings
from urllib.parse import ParseResult, urlparse
import chardet
from mitmproxy import http
from mitmproxy.net.http.http1.assemble import assemble_request, assemble_response
from modules.database import Database
from models import ProxyModel

# pylint: disable=C0121,W0212,W0718,R0912,R0914,R0915

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
            #self._parent_callback_proxy_message(f"REQUEST: No target selected.")
            return

        dynamic_host = None
        dynamic_fqdn = False
        save_request = False
        for item in self.in_scope:
            if item['fqdn'] is not None:
                if flow.request.host == item['fqdn']:
                    save_request = True
                if '*' in item['fqdn']:
                    tmp_fqdn = item['fqdn'].replace('*','')
                    if flow.request.host.endswith(tmp_fqdn):
                        save_request = True
                if '{dynamic}' in item['fqdn']:
                    tmp_fqdn = item['fqdn']
                    match = re.search(r"{dynamic}(.+)", item['fqdn'])
                    if match:
                        tmp_fqdn = match.group(1)
                        if flow.request.host.endswith(tmp_fqdn):
                            dynamic_host = item['fqdn']
                            dynamic_fqdn = True
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

        if dynamic_host is not None and dynamic_fqdn:
            dynamic_full_url: str = f'{request.scheme}://{dynamic_host}:{request.port}{request.path}'

        parsed: ParseResult = urlparse(full_url)
        path: str = parsed.path
        url: str = f'{parsed.scheme}://{parsed.netloc.replace(":443","")}{parsed.path}'

        try:
            raw_request = assemble_request(flow.request).decode('utf-8')
            #print(assemble_request(flow.request).decode('utf-8'))
        except Exception as exc:
            self._parent_callback_proxy_message("REQUEST:",exc)
            raw_request = None

        try:
            headers_string = ", ".join([f"{k}: {v}" for k, v in flow.request.headers.items()])
            new_request = ProxyModel(
                target_id=int(self.target.id),
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
                parsed_url=url,
                raw_request=raw_request,
                raw_response=None,
                decoded_content=None,
                flow=None,
                dynamic_host=dynamic_host,
                dynamic_full_url=dynamic_full_url
            )

            #self._parent_callback_proxy_message(new_request.__dict__)
            with Database._get_db() as db:
                db.add(new_request)
                db.commit()
                db.refresh(new_request)

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
        if self.target is None or self.in_scope is None:
            #self._parent_callback_proxy_message("RESPONSE: self in_scope is none")
            return

        dynamic_host = None
        dynamic_fqdn = False
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
                    if '{dynamic}' in item['fqdn']:
                        tmp_fqdn = item['fqdn']
                        match = re.search(r"{dynamic}(.+)", item['fqdn'])
                        if match:
                            tmp_fqdn = match.group(1)
                            if flow.request.host.endswith(tmp_fqdn):
                                dynamic_host = item['fqdn']
                                dynamic_fqdn = True
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
        response_headers = None

        try:
            response_string = f"HTTP/1.1 {flow.response.status_code}\n"
            for key, value in flow.response.headers.items():
                tmp_key = None
                tmp_value = None
                if isinstance(key, str):
                    tmp_key = key
                elif isinstance(key, bytes):
                    encoding = chardet.detect(key)['encoding']
                    tmp_key = key.decode(encoding)

                if isinstance(value, str):
                    tmp_value = value
                elif isinstance(value, bytes):
                    encoding = chardet.detect(key)['encoding']
                    tmp_value = value.decode(encoding)

                if tmp_key is not None and tmp_value is not None:
                    response_string += f"{tmp_key}: {tmp_value}"
                    response_string += "\n"
                    response_headers = response_string
        except Exception as exc:
            self._parent_callback_proxy_message(f"RESPONSE: response headers string - {exc}")
            response_headers = str(flow.response.headers)

        try:
            content = flow.request.text.replace('\x00', '')
        except Exception as exc:
            self._parent_callback_proxy_message(f"RESPONSE: clean content exception - {exc}")
            content = None

        timestamp_start = flow.request.timestamp_start
        timestamp_end = flow.request.timestamp_end

        full_url: str = f'{request.scheme}://{request.host}:{request.port}{request.path}'

        if dynamic_host is not None and dynamic_fqdn:
            dynamic_full_url: str = f'{request.scheme}://{dynamic_host}:{request.port}{request.path}'

        parsed: ParseResult = urlparse(full_url)
        path: str = parsed.path
        url: str = f'{parsed.scheme}://{parsed.netloc.replace(":443","")}{parsed.path}'

        try:
            raw_request = assemble_request(flow.request).decode('utf-8')
        except Exception as exc:
            self._parent_callback_proxy_message("RESPONSE: raw request - ", exc)
            raw_request = None

        try:
            raw_response = assemble_response(flow.response).decode('utf-8','replace')
        except UnicodeDecodeError as exc:
            try:
                raw_response = str(assemble_response(flow.response))
            except Exception as assemble_exc:
                raw_response = None
                self._parent_callback_proxy_message(flow.request.pretty_url)
                self._parent_callback_proxy_message(str(assemble_exc))
                detected_encoding = chardet.detect(flow.response)['encoding']
                try:
                    raw_response = flow.response.decode(detected_encoding)
                except UnicodeDecodeError as decode_exc:
                    print(f"Failed to decode byte string: {decode_exc}")
                    raw_response = ""
        except Exception as exc:
            self._parent_callback_proxy_message(flow.request.pretty_url)
            self._parent_callback_proxy_message(str(exc))
            raw_response = None

        try:
            decoded_content = None
            if flow.response.content:
                size = len(flow.response.content)
                size  = min(size, 20)
                if flow.response.content[0:size] != flow.response.get_decoded_content()[0:size]:
                    decoded_content = flow.response.get_decoded_content()
                else:
                    decoded_content = flow.response.get_content()
        except Exception as exc:
            decoded_content = None

        try:
            full_flow = None
        except Exception as exc:
            full_flow = None

        try:
            #headers_string = ", ".join([f"{k}: {v}" for k, v in flow.response.headers.items()])

            new_response = ProxyModel(
                target_id=int(self.target.id),
                name=None,
                request=None,
                action='Response',
                response_status_code=flow.response.status_code,
                response_reason=flow.response.reason,
                response_headers=str(response_headers),
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
                parsed_url=url,
                raw_request=raw_request,
                raw_response=raw_response,
                decoded_content=decoded_content,
                flow=full_flow,
                dynamic_host=dynamic_host,
                dynamic_full_url=dynamic_full_url
            )

            with Database._get_db() as db:
                db.add(new_response)
                db.commit()
                db.refresh(new_response)

        except Exception as database_exception: # pylint: disable=W0718
            self._parent_callback_proxy_message("RESPONSE: database_exception - ", database_exception)
            print("Response database exception:", database_exception)
