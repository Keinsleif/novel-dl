import sys, os, re
from pathlib import Path
from urllib.parse import urljoin
import importlib.util
from .info import __appname__

URL_REG = re.compile("https?://[\w/:%#\$&\?\(\)~\.=\+\-]+")


class NovelDLException(Exception):
    def __init__(self, msg, **kw):
        id = kw.pop("id", 0)
        msg = msg.format(**kw)
        self.msg = "novel-dl: " + msg
        self.errmsg = msg
        self.id = id
        super().__init__(msg)

    def console_message(self):
        print(self.msg, file=sys.stderr)


def get_config_path():
    if os.name == "nt":
        path = Path(os.getenv("APPDATA"))
    else:
        path = Path("~/.config").expanduser()

    return path / __appname__.lower()


def import_from_file(name, path):
    if not os.path.isfile(path):
        raise FileNotFoundError
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def deepupdate(dict_base, other):
    for k, v in other.items():
        if isinstance(v, dict) and k in dict_base:
            deepupdate(dict_base[k], v)
        elif isinstance(v, list) and k in dict_base:
            dict_base[k] += [i for i in v if not i in dict_base[k]]
        else:
            dict_base[k] = v


def cjoin(base, part):
    if URL_REG.match(base):
        return urljoin(base, part)
    else:
        return Path(base) / Path(part)
