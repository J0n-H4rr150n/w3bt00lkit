"""tools.py"""
import os
import subprocess


class Tools:
    """Tools."""

    def __init__(self, app_obj, args):
        self.app_obj = app_obj
        self.args = args

    def _handle_input(self, args):
        """Handle Input."""
        self.args = args
        print("tools:",self.args)
        if len(self.args) < 2:
            return

        try:
            class_name = self.args[1]
            function_name = self.args[0]
            args = self.args
            func = getattr(self, function_name) # pylint: disable=W0621
            if callable(func):
                func(args=args)
            else:
                print('Else: Function is not callable:%s',function_name)
        except AttributeError:
            return
        except Exception as exc:
            print(exc)

    def _pwd(self):
        path = None
        result = subprocess.run(['pwd'], stdout=subprocess.PIPE)
        if result.returncode == 0:
            path = (result.stdout.decode('utf-8').strip())
            return path

    def _home(self):
        home_path = None
        try:
            home_path = os.path.expanduser('~')
            return home_path
        except Exception as exc:
            print(exc)

    def katana(self, args):
        print("Run katana...\n")
        #print("Handle katana...")
        #print(args)
        if args is not None and args[0] == 'katana':
            command = args
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
            if result.returncode == 0:
                results = result.stdout.splitlines()
                print(results)
            else:
                home_path = self._home()
                if home_path is not None:
                    path = [f"{home_path}/go/bin/katana"]
                    args_suffix = args[1:]
                    command = path + args_suffix
                    command = ' '.join(command)
                    print(command)
                    print()
                    #result = subprocess.run(command, capture_output=True, text=True)
            
                    #if result.returncode == 0:
                    #    results = result.stdout.splitlines()
                    #    print(results)
                    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)

                    while True:
                        output = process.stdout.readline()
                        if output == '':
                            break
                        print(output.strip())

                    rc = process.poll()
                    if rc:
                        print(f"Process returned non-zero exit code {rc}")
                        print(process.stderr.read())
