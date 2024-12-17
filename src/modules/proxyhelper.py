"""proxyhelper.py"""
import os
import json
import re
import random
import requests
import string
import sys
import signal
import threading
import traceback
import time
from datetime import datetime, timezone
import warnings
from urllib.parse import ParseResult, urlparse
import chardet
from mitmproxy import http
from mitmproxy.net.http.http1.assemble import assemble_request, assemble_response
from dotenv import load_dotenv
from modules.database import Database
from models import ProxyModel, SynackTargetModel

load_dotenv()

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

class ProxyHelper: # pylint: disable=R0902
    """ProxyHelper."""
    target: str = ''
    exclusion_list: list = []

    def __init__(self, app_obj, target, in_scope, parent_callback_proxy_message) -> None:
        self.app_obj = app_obj
        self.target = target
        self.synack_target = False
        self.in_scope = in_scope
        self._parent_callback_proxy_message = parent_callback_proxy_message
        if target is not None and target.name.lower() == 'synack' and target.platform.lower() == 'synack':
            self.synack_target = True
        self.request_count = 0
        self.response_count = 0
        self.auth_token = None
        self.auth_token_created_timestamp = None
        self.auth_token_created_timestamp_str = None
        self.synack_base = os.environ.get("SYNACK_BASE")
        self.synack_api = os.environ.get("SYNACK_API")
        self.slack_url = os.environ.get("SLACK_URL")
        self.slack_slug = os.environ.get("SLACK_SLUG")
        self.missions_running = False

    def random_string(self, length):
        """Generate a random string."""
        letters = string.ascii_letters
        result_str = ''.join(random.choice(letters) for i in range(length))
        return result_str

    def clean_string(self, string_value):
        """Clean string with null byte."""
        if string_value is not None:
            try:
                if isinstance(string_value, str):
                    string_value = string_value.replace('\x00','')
                elif isinstance(string_value, bytes):
                    string_value = string_value.replace(b'\x00', b'')
            except Exception as exc:
                print(exc)
        return string_value

    def post_request(self, url: str) -> str:
        """POST Request."""
        if self.auth_token is not None:
            max_retries = 3
            current_retries = 0
            cookies = {}
            headers = {
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Authorization': f'Bearer {self.auth_token}',
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
            data = ''
            response = requests.get(url, headers=headers)
            try:
                if response.status_code == 401:
                    print("\nNeed to refresh credentials.")
                    if current_retries > max_retries:
                        print("Process halted!")
                    else:
                        print("Waiting to see if mitmproxy will refresh...")
                        current_retries += 1
                        time.sleep(30)
                elif response.status_code == 200:
                    response_json = response.json()
                    if response_json is not None and len(response_json) > 0:
                        print("\nResults @",datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
                        print(response_json)
                        print("+++")
                    return response_json
                else:
                    print(response)
            except Exception as exc:
                print(exc)

    def get_request(self, vars, url):
        """GET Request."""
        max_retries = 3
        current_retries = 0
        cookies = {}
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Authorization': f'Bearer {self.auth_token}',
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
        data = ''
        response = requests.get(url, headers=headers)

        try:
            if response.status_code == 401:
                print("\nNeed to refresh credentials.")
                if current_retries > max_retries:
                    print("Process halted!")
                else:
                    print("Waiting to see if mitmproxy will refresh...")
                    current_retries = current_retries + 1
                    time.sleep(30)
            elif response.status_code == 200:
                json = response.json()
                if json is not None and len(json) > 0:
                    print("\nResults @",datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
                    print(json)
                    print("--------\n")
                return json
            else:
                print(response.status_code)
                print(response)
                print("Process halted!")
        except Exception as exc:
            print(exc)
            print("\nProcess halted!\n")

    def put_request(self, vars: dict, url: str, payload):
        """PUT request."""
        max_retries = 3
        current_retries = 0
        cookies = {}
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Authorization': f'Bearer {self.auth_token}',
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
                        'Authorization': f'Bearer {self.auth_token}',
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
                response_two = requests.get(url, headers=headers)
                print(response_two.status_code)
                print(response_two.text)
                print("")

            elif response.status_code == 200:
                json = response.json()
                print("\nResults @",datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
                print(json)
                print("+--------\n")
                return json
            else:
                print(url, headers)
                print("------")
                print(response)
                print("------")
                print("Need to refresh credentials? Proxy stopped working?")
                print("Process halted! [PH0001]")
        except Exception as exc:
            print(exc)
            print("\nProcess halted! [EXCPH0001]\n")

    def claim_mission(self, mission):
        print(str(mission))

        data = {
            "type": "CLAIM"
        }

        title = mission["title"]
        desc = mission["description"]
        campaignName = mission["campaignName"]
        orgId = mission["organizationUid"]
        listingId = mission["listingUid"]
        listingCodename = mission["listingCodename"]
        campaignId = mission["campaignUid"]
        taskId = mission["id"]
        payout = str(mission["payout"]["amount"])

        url = f'{self.synack_base}/api/tasks/v1/organizations/{orgId}/listings/{listingId}/campaigns/{campaignId}/tasks/{taskId}/transitions'
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")

        print("url:")
        print(url)

        headers = {
            'Content-Length': '16',
            'Sec-Ch-Ua': '\"Google Chrome\";v=\"119\", \"Chromium\";v=\"119\", \"Not?A_Brand\";v=\"24\"',
            'Content-Type': 'application/json',
            'Sec-Ch-Ua-Mobile': '?0',
            'Authorization': f'Bearer {self.auth_token}',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Sec-Ch-Ua-Platform': '\"Linux\"',
            'Accept': '*/*',
            'Origin': self.synack_base,
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': f'{self.synack_base}/missions?status=PUBLISHED',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'close'
        }

        #results = get_request(vars, url, data)
        try:
            #data = '{"type":"CLAIM"}'
            data = '{\"type\":\"CLAIM\"}'
            claim_request = requests.post(url, headers=headers, data=data)
            print("")
            print("Claim request text:")
            print(claim_request.text)
            print("*******************")
            print(headers)
            print("+++++++++++++++++++")
            print(data)

            if claim_request.status_code == 201:
                try:
                    headers = {
                        'Accept': '*/*',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Content-type': 'application/json'
                    }
                    slack_url = self.slack_url
                    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S:%f")
                    slack_message = '{"text":"Mission claimed at ' + str(timestamp) + ' ' + self.slack_slug + '!"}'
                    slack_request = requests.post(slack_url, headers=headers, data=slack_message)
                    print(slack_request.text)
                except Exception as slack_exc:
                    print("SLACK Exception for mission claim:")
                    print(slack_exc)

            elif claim_request.status_code == 400:
                print("[400] Malformed request...")
            elif claim_request.status_code == 403:
                print("[403] You are not authorized to access this resource or perform this operation.")
            else:
                print("Other claim_request status code!")

            time.sleep(3)
            return claim_request
        except Exception as slack_exc:
            print("Failed to claim a mission!")
            print(slack_exc)
            time.sleep(3)
            return None

    def get_missions(self, stop_event, random_string):
        while self.app_obj.missions_running and not stop_event.is_set() and self.app_obj.proxy_running:
            time.sleep(30)
            if self.auth_token is not None and self.synack_api is not None:
                vars = []
                url = f"{self.synack_api}tasks?perPage=20&viewed=true&page=1&status=PUBLISHED&sort=CLAIMABLE&sortDir=DESC&includeAssignedBySynackUser=true" # pylint: disable=C0301
                results = self.get_request(vars, url)
                if results:
                    print(results)
                    self._parent_callback_proxy_message(f"REQUEST: Mission results... {results}")
                    try:
                        headers = {
                            'Accept': '*/*',
                            'Accept-Language': 'en-US,en;q=0.9',
                            'Content-type': 'application/json'
                        }
                        slack_url = self.slack_url
                        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S:%f")
                        slack_message = '{"text":"New mission(s) at ' + str(timestamp) + ' ' + self.slack_slug + '!"}'
                        slack_request = requests.post(slack_url, headers=headers, data=slack_message)
                        print(slack_request.text)
                    except Exception as slack_exc:
                        print(slack_exc)

                    for result in results:
                        claim_this = True
                        try:
                            amount = result['payout']['amount']
                            print("Payout amount:", amount)
                            #if int(amount) < 20:
                            #    claim_this = False
                        except Exception as payout_exc:
                            print(payout_exc)

                        if claim_this:
                            #claim_results = self.claimMission(vars, result)
                            claim_results = self.claim_mission(result)
                            print("Mission Claim Results:")
                            print(claim_results)
                            print("\n----------")
                            print(result)
                            print("----------")
                            #if print_output:

        #print("app obj:", self.app_obj.missions_running)
        #print("stop event:", stop_event.is_set())
        print("Mission thread exiting...", random_string)
        self.app_obj.missions_running = False

    def request(self, flow: http.HTTPFlow) -> None: # pylint: disable=R0914
        """Proxy request.
        
        Args:
            flow: The flow object for the request.

        Returns:
            None
        """

        headers = flow.request.headers

        if 'synack' in flow.request.host:
            for header in headers:
                if "authorization" == header or "Authorization" == header:
                    try:
                        now = datetime.now(timezone.utc)
                        if self.auth_token_created_timestamp is None and headers[header].startswith("Bearer"):
                            print("\n\n***** AUTHORIZATION TOKEN *****")
                            self.auth_token = headers[header].replace("Bearer ","")
                            self.auth_token_created_timestamp = datetime.now(timezone.utc)
                            self.auth_token_created_timestamp_str = self.auth_token_created_timestamp.strftime("%Y-%m-%d %H:%M:%S")
                            #print(self.auth_token_created_timestamp_str,'->', self.auth_token)
                            print(self.auth_token_created_timestamp_str,'->', '[auth_token]')
                            print("-------------------------------\n")
                        else:
                            new_auth_token = headers[header].replace("Bearer ","")
                            previous_auth_token = self.auth_token
                            if new_auth_token != previous_auth_token and new_auth_token.startswith("Bearer"):
                                print("\n\n***** NEW AUTHORIZATION TOKEN *****")
                                self.auth_token = headers[header].replace("Bearer ","")
                                self.auth_token_created_timestamp = datetime.now(timezone.utc)
                                self.auth_token_created_timestamp_str = self.auth_token_created_timestamp.strftime("%Y-%m-%d %H:%M:%S")
                                diff = now - auth_token_created_timestamp
                                print("Diff (minutes):", (diff.seconds / 60))
                                #print(self.auth_token_created_timestamp_str,'->', self.auth_token)
                                print(self.auth_token_created_timestamp_str,'->', '[auth_token]')
                                print("-----------------------------------\n")
                    except Exception as exc:
                        print("\nAUTHORIZATION EXCEPTION:")
                        print(exc)
                        print("")

        if self.target is None or self.in_scope is None:
            return

        self.request_count = self.request_count + 1

        dynamic_host = None
        dynamic_fqdn = False
        dynamic_full_url = None

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

        try:
            parsed: ParseResult = urlparse(full_url)
            path: str = parsed.path
            url: str = f'{parsed.scheme}://{parsed.netloc.replace(":443","")}{parsed.path}'
        except Exception as exc:
            parsed = None
            path = None
            url = None
            self._parent_callback_proxy_message(f"REQUEST (CHECK EXC): {exc}")

        try:
            raw_request = assemble_request(flow.request).decode('utf-8')
        except Exception as exc:
            self._parent_callback_proxy_message("REQUEST:",exc)
            raw_request = None

        try:
            headers_string = ", ".join([f"{k}: {v}" for k, v in flow.request.headers.items()])
        except Exception as exc:
            headers_string = None

        try:
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

            with Database._get_db() as db:
                db.add(new_request)
                db.commit()
                db.refresh(new_request)

        except Exception as database_exception: # pylint: disable=W0718
            self._parent_callback_proxy_message("REQUEST: database_exception...")
            self._parent_callback_proxy_message(str(database_exception))

        if self.auth_token is not None and self.synack_api is not None:
            if self.app_obj.missions_running == False:
                self.missions_running = True
                self.app_obj.missions_running = True
                stop_event = threading.Event()
                try:
                    print("\nStart polling for missions...\n")
                    self.missions_thread = threading.Thread(target=self.get_missions, args=(stop_event,self.random_string(10)))
                    self.missions_thread.daemon = True
                    self.missions_thread.start()
                except Exception as exc:
                    print(exc)
                    self._parent_callback_proxy_message(f"REQUEST: {exc}")
                    stop_event.set()

    def response(self, flow: http.HTTPFlow) -> None:
        """Proxy response.
        
        Args:
            flow: The flow object for the response.

        Returns:
            None
        """
        self.response_count = self.response_count + 1
        if self.target is None or self.in_scope is None:
            self._parent_callback_proxy_message("RESPONSE: self in_scope is none")
            return

        dynamic_host = None
        dynamic_fqdn = False
        dynamic_full_url = None

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
            new_response = ProxyModel(
                target_id=int(self.target.id),
                name=None,
                request=None,
                action='Response',
                response_status_code=flow.response.status_code,
                response_reason=str(flow.response.reason),
                response_headers=str(response_headers),
                response_text=self.clean_string(flow.response.text),
                host=host,
                port=port,
                method=method,
                scheme=scheme,
                authority=authority,
                path=path,
                headers=str(headers),
                content=self.clean_string(content),
                timestamp_start=timestamp_start,
                timestamp_end=timestamp_end,
                full_url=full_url,
                parsed_full_url=parsed,
                parsed_path=path,
                parsed_url=url,
                raw_request=self.clean_string(raw_request),
                raw_response=self.clean_string(raw_response),
                decoded_content=self.clean_string(decoded_content),
                flow=full_flow,
                dynamic_host=dynamic_host,
                dynamic_full_url=dynamic_full_url
            )

            with Database._get_db() as db:
                db.add(new_response)
                db.commit()
                db.refresh(new_response)

        except Exception as database_exception: # pylint: disable=W0718
            self._parent_callback_proxy_message("RESPONSE: database_exception...")
            self._parent_callback_proxy_message(database_exception)
            self._parent_callback_proxy_message(traceback.print_exc())

        if self.auth_token is not None and self.synack_api is not None:

            if flow.request.pretty_url.startswith(self.synack_base) and '/api/targets/registered_summary' == flow.request.path:
                self._parent_callback_proxy_message(f"RESPONSE: {flow.request.pretty_url}")
                targets = json.loads(self.clean_string(flow.response.text))

                for target in targets:
                    new_target = SynackTargetModel(
                        target_id = target['id'],
                        target_codename = target['codename'],
                        target_org_id = target['organization_id'],
                        activated_at = target['activated_at'],
                        target_name = target['name'],
                        category = str(target['category']),
                        outage_windows = str(target['outage_windows']),
                        vulnerability_discovery = target['vulnerability_discovery'],
                        collaboration_criteria = str(target['collaboration_criteria'])
                    )

                    with Database._get_db() as db:
                        db.add(new_target)
                        db.commit()
                        db.refresh(new_target)
