"""input_handler.py"""
from modules.proxy import Proxy
from modules.targets import Targets


class InputHandler:
    """Input Handler."""
    def __init__(self, app_obj, text):
        self.app_obj = app_obj
        self.text = text
        self.args = None
        self.obj = None

    def _handle_input(self):
        """Handle input."""
        if len(self.text) == 0:
            return
        self.args = self.text.split()
        if len(self.args) == 0:
            return
        elif len(self.args) == 1:
            match self.args[0]:
                case x if x in ['clear','clr']:
                    self.app_obj._clear()
                case 'exit':
                    self.app_obj._exit()
        elif len(self.args) == 3:
            match self.args[0]:
                case 'proxy':
                    self.obj = self.app_obj.proxy._handle_input(self.args)
            return
        elif len(self.args) == 4:
            match self.args[0]:
                case 'proxy':
                    self.obj = self.app_obj.proxy._handle_input(self.args)
            return
        else:
            try:
                match self.args[0]:
                    case 'database':
                        self.obj = self.app_obj.database._handle_input(self.args)
                    case 'proxy':
                        self.obj = self.app_obj.proxy._handle_input(self.args)

                match self.args[1]:
                    case x if x in ['note','notes']:
                        self.obj = self.app_obj.targetnotes._handle_input(self.args)
                    case 'scope':
                        self.obj = self.app_obj.targetscope._handle_input(self.args)
                    case x if x in ['target','targets']:
                        self.obj = self.app_obj.targets._handle_input(self.args)
                    case 'proxy':
                        self.obj = self.app_obj.proxy._handle_input(self.args)
                    case _:
                        return
            except IndexError:
                return
            except Exception as exc:
                print("*** UNHANDLED EXCEPTION ***")
                print(exc)