"""completers.py"""
from typing import Any, Generator
from prompt_toolkit.completion import Completer, Completion, WordCompleter

default_list: list[str] = ['add','checklists','clear','database','exit','help','proxy','pwd','remove','run','start','stop','tools','view']

add_list: list[str] = ['note','param','path','scope','target']
checklist_list: list[str] = ['owasp-wstg']
database_list: list[str] = ['setup','tables']
help_list: list[str] = ['checklists','database','proxy','targets']
proxy_list: list[str] = ['comments','options','requests','responses','search','search-requests','search-responses','start','stop']
proxy_history_list: list[str] = ['requests','responses']

requests_responses_list = ['100','101','200','201','202','204','301','302','304','400','401','403','404','405','409','418','429','500','502','503','504',
                                    'api','asc','delete','desc','distinct','foobar','get','head','js','json','options','patch',
                                    'post','put','trace']
proxy_history_requests: list[str] = requests_responses_list
proxy_history_responses: list[str] = requests_responses_list
synack_list: list[str] = ['targets']

remove_list: list[str] = ['target']
start_list: list[str] = ['proxy']
stop_list: list[str] = ['proxy']
target_list: list[str] = ['add','remove','select','view']
tools_list: list[str] = ['katana']
view_list: list[str] = ['notes','scope','targets','vulnerabilities']


class Completers(Completer):
    """Completers."""
    def __init__(self) -> None:
        self.completer = WordCompleter(default_list, ignore_case=True)

    def get_completions(self, document, complete_event) -> Generator[Completion, Any, None]: # pylint: disable=R0912
        text: str = document.text_before_cursor
        if text.startswith('add '):
            self.completer = WordCompleter(add_list, ignore_case=True)
        elif text.startswith('checklists '):
            self.completer = WordCompleter(checklist_list, ignore_case=True)
        elif text.startswith('database '):
            self.completer = WordCompleter(database_list, ignore_case=True)
        elif text.startswith('help '):
            self.completer = WordCompleter(help_list, ignore_case=True)
        elif text.startswith('proxy '):
            self.completer = WordCompleter(proxy_list, ignore_case=True)
            if 'requests' in text:
                self.completer = WordCompleter(proxy_history_requests, ignore_case=True)
            elif 'responses' in text:
                self.completer = WordCompleter(proxy_history_responses, ignore_case=True)
            else:
                self.completer = WordCompleter(proxy_list, ignore_case=True)
        elif text.startswith('remove '):
            self.completer = WordCompleter(remove_list, ignore_case=True)
        elif text.startswith('start '):
            self.completer = WordCompleter(start_list, ignore_case=True)
        elif text.startswith('synack '):
            self.completer = WordCompleter(synack_list, ignore_case=True)
        elif text.startswith('stop '):
            self.completer = WordCompleter(stop_list, ignore_case=True)
        elif text.startswith('view '):
            self.completer = WordCompleter(view_list, ignore_case=True)
        elif ' ' in text:
            return
        else:
            main_list = set(default_list + tools_list)
            main_list = list(sorted(main_list))
            self.completer = WordCompleter(main_list, ignore_case=True)

        for completion in self.completer.get_completions(document, complete_event): # pylint: disable=R1737
            yield completion
