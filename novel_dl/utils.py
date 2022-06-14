import sys,os
import importlib.util
from .info import __appname__

class NovelDLException(Exception):
    def console_message(self):
        print(self.return_message(),file=sys.stderr)
    def return_message(self):
        return "novel-dl: "+self.args[0]
    def return_id(self):
        return self.args[1]


def raise_error(msg,id=0):
    raise NovelDLException(msg,id)

def get_config_path():
    if os.name == 'nt':
        path = os.getenv('APPDATA')
    else:
        path = os.path.expanduser('~/.config')

    return os.path.join(path, __appname__.lower())

def import_from_file(name,path):
    if not os.path.isfile(path):
        raise FileNotFoundError
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
