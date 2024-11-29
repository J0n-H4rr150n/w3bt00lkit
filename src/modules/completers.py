"""completers.py"""
from typing import Any, Generator, Iterable
from prompt_toolkit.completion import Completer, Completion, WordCompleter

default_list: list[str] = ['add','clear','database','exit','help','proxy','remove','start','stop','view']

add_list: list[str] = ['note','param','path','scope','target']
database_list: list[str] = ['setup','tables']
proxy_list: list[str] = ['history','options','start','stop']
proxy_history_list: list[str] = ['requests','responses']
#proxy_history_requests: list[str] = ['js','params','no-media']
#proxy_history_responses: list[str] = ['js','params','no-media']
proxy_history_requests: list[str] = ['js','patch','post','put']
proxy_history_responses: list[str] = ['delete','foobar','get','js','json','options','patch','post','put','trace']
remove_list: list[str] = ['target']
start_list: list[str] = ['proxy']
stop_list: list[str] = ['proxy']
target_list: list[str] = ['add','remove','select','view']
view_list: list[str] = ['checklists','notes','scope','targets']

class Completers(Completer):
    """Completers."""
    def __init__(self) -> None:
        self.completer = WordCompleter(default_list, ignore_case=True)

    def get_completions(self, document, complete_event) -> Generator[Completion, Any, None]:
        text: str = document.text_before_cursor
        if text.startswith('add '):
            self.completer = WordCompleter(add_list, ignore_case=True)
        elif text.startswith('database '):
            self.completer = WordCompleter(database_list, ignore_case=True)
        elif text.startswith('proxy '):
            if 'history' in text:
                self.completer = WordCompleter(proxy_history_list, ignore_case=True)
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
        elif text.startswith('stop '):
            self.completer = WordCompleter(stop_list, ignore_case=True)
        elif text.startswith('view '):
            self.completer = WordCompleter(view_list, ignore_case=True)
        elif ' ' in text:
            return
        else:
            self.completer = WordCompleter(default_list, ignore_case=True)

        for completion in self.completer.get_completions(document, complete_event):
            yield completion
