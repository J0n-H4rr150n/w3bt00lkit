"""w3bt00lkit"""

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from rich.console import Console

class W3bT00lkit:
    """W3bT00lkit."""

    intro = r""" _    _  _____  _      _____  _____  _____  _  _     _  _   
| |  | ||____ || |    |_   _||  _  ||  _  || || |   (_)| |  
| |  | |    / /| |__    | |  | |/' || |/' || || | __ _ | |_ 
| |/\| |    \ \| '_ \   | |  |  /| ||  /| || || |/ /| || __|
\  /\  /.___/ /| |_) |  | |  \ |_/ /\ |_/ /| ||   < | || |_ 
 \/  \/ \____/ |_.__/   \_/   \___/  \___/ |_||_|\_\|_| \__|
                                                                                          
"""

    available_commands_default = r"""Available commands:
------------------------------------------
 target - Target menu
 exit    - Exit the w3bt00lkit     
"""
    prompt = 'w3bt00lkit> '

    def __init__(self):
        self.name = 'w3bt00lkit'
        self.words = ['target','exit']
        self.session = PromptSession()
        self.completer = WordCompleter(self.words)

    def print_output(self, *args, **kwargs):
        if len(args) > 0:
            for value in args:
                print(value)                

    def run(self):
        self.print_output(self.intro,self.available_commands_default)
        while True:
            text = self.session.prompt(f'{self.name}> ', completer=self.completer)
            if text == 'exit':
                break
            elif text == 'help':
                self.do_help()
            elif text == 'target':
                self.do_target()
            else:
                print('Unknown command.')

    def do_target(self):
        self.print_output("target","available_commands",category="menu")
        print("Target menu...")

    def do_help(self):
        print("Help Menu...")

if __name__ == '__main__':
    try:
        t00lkit = W3bT00lkit()
        t00lkit.run()
    except KeyboardInterrupt:
        print('Exiting...')
        exit(0)
