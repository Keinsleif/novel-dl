import os
import io
from pathlib import Path
import json
import sys
from copy import deepcopy
from argparse import ArgumentParser
from .utils import (
    get_config_path,
    NovelDLException as NDLE,
    deepupdate,
)
from .info import (
    __version__,
    __appname__,
    __description__,
)

root = Path(__file__).parent.resolve()


class MultipleSrc(object):
    def __init__(self, lists):
        self.__sources = lists
        self.src = lists[0]
        self.index = 0
        self.length = len(lists)

    def next(self):
        if self.index + 1 < self.length:
            self.index += 1
            self.src = self.__sources[self.index]

    def has_next(self):
        if self.index + 1 < self.length:
            return True
        else:
            return False


class EnvManager(object):
    def __init__(self):
        self.classname = self.__class__.__name__
        self.conf = dict()
        self.env = {"THEMES": list(), "bar_output": sys.stdout, "delay": 1, "src": MultipleSrc([""])}
        self._default_conf = {
            "default_theme": "auto",
            "theme_path": [root / "themes"],
            "default_delay": 1,
            "min_delay": 0.1,
            "retries": 3,
            "user_agant": "",
            "output_path": ".",
            "output_format": "{title}",
            "symlink_static": False,
        }
        self.load_default()
        self.config_dir = get_config_path()
        self.config_file = self.config_dir / "settings.json"
        self.init_parser()

    def __deepcopy__(self, memo):
        cls = self.__class__
        em = cls.__new__(cls)
        memo[id(em)] = em
        for k, v in self.__dict__.items():
            if k == "env":
                tmp = {}
                for k2, v2 in self.env.items():
                    if isinstance(v2, io.TextIOWrapper):
                        tmp[k2] = v2
                    else:
                        tmp[k2] = deepcopy(v2, memo)
                setattr(em, "env", tmp)
            else:
                setattr(em, k, deepcopy(v, memo))
        return em

    def load_default(self):
        self.conf = deepcopy(self._default_conf)
        valid_themes = ["auto"]
        [
            valid_themes.append(j.name)
            for i in self.conf["theme_path"]
            for j in i.iterdir()
            if not j.name.startswith(".") and not j.name in valid_themes
        ]
        self.env["THEMES"] = valid_themes

    def load_usercfg(self):
        if not self.config_dir.is_dir():
            return
        try:
            with self.config_file.open(mode="r") as f:
                conf = json.load(f)
        except json.decoder.JSONDecodeError as e:
            raise NDLE("[{klass}] Config load error: " + e.msg, klass=self.classname)
        else:
            conf["theme_path"] = list(map(Path, conf["theme_path"]))
            conf["output_path"] = Path(conf["output_path"])
            self.update_config(conf)

    def update_config(self, data):
        deepupdate(self.conf, self.verify_config(data))
        valid_themes = ["auto"]
        [
            valid_themes.append(j.name)
            for i in self.conf["theme_path"]
            for j in i.iterdir()
            if not j.name.startswith(".") and not j.name in valid_themes
        ]
        self.env["THEMES"] = valid_themes

    def save_usercfg(self):
        if not self.config_dir.is_dir():
            self.config_dir.mkdir()
            (self.config_dir / "themes").mkdir()
            self.conf["theme_path"] += [self.config_dir / "themes"]
        sconf = deepcopy(self.conf)
        sconf["theme_path"].remove(self._default_conf[0])
        sconf["theme_path"] = list(map(str, sconf["theme_path"]))
        sconf["output_path"] = str(sconf["output_path"])
        with self.config_file.open(mode="w") as f:
            json.dump(self.conf, f, ensure_ascii=False, indent=4)

    def verify_config(self, sd):
        for key in list(sd):
            if key not in self.conf:
                sd.pop(key)
            elif type(sd[key]) != type(self.conf[key]):
                sd.pop(key)

        theme_paths = self._default_conf["theme_path"]
        for path in sd.get("theme_path"):
            if not path.is_dir():
                sd["theme_path"].remove(path)
            if not path in theme_paths:
                theme_paths.append(path)

        valid_themes = ["auto"]
        [
            valid_themes.append(j.name)
            for i in theme_paths
            for j in i.iterdir()
            if not j.name.startswith(".") and not j.name in valid_themes
        ]

        rules_dict = {
            "default_theme": valid_themes,
        }

        for key, valid_values in list(rules_dict.items()):
            if sd[key] not in valid_values:
                sd.pop(key)

        dd = self.conf["default_delay"]
        if sd.get("default_delay"):
            if sd["default_delay"] < 0:
                sd.pop("default_delay")
            else:
                dd = sd["default_delay"]
        if sd.get("min_delay"):
            if sd["min_delay"] < 0 or sd["min_delay"] > dd:
                sd.pop("min_delay")

        if sd.get("retries") and sd.get("retries") < 0:
            sd.pop("min_delay")

        if sd.get("output_format"):
            try:
                sd["output_format"].format("", ncode="", title="")
            except:
                sd.pop("output_format")
        return sd

    def init_parser(self):
        kw = {
            "prog": __appname__.lower(),
            "usage": "%(prog)s [OPTIONS] URL [URL ...]\n       %(prog)s [-f] [-u] PATH [PATH ...]",
            "description": __description__,
            "conflict_handler": "resolve",
        }

        def error_handler(msg):
            self.parser.print_usage()
            raise NDLE("[{klass}] " + msg, klass=self.classname)

        self.parser = ArgumentParser(**kw)
        self.parser.error = error_handler
        self.parser.add_argument("src", help="novel fetch source (URL or Path)", default="", nargs="+")
        general = self.parser.add_argument_group("General Options")
        general.add_argument("-h", "--help", action="help", help="show this help text and exit")
        general.add_argument("-v", "--version", action="version", version="%(prog)s {}".format(__version__))
        general.add_argument("-q", "--quiet", action="store_true", help="suppress non-messages")
        downloader = self.parser.add_argument_group("Downloader Options")
        downloader.add_argument("-a", "--axel", action="store_true", help="turn on axceleration mode")
        downloader.add_argument("-f", "--from-file", action="store_true", help="turn on extract from downloaded file")
        downloader.add_argument("-u", "--update", action="store_true", help="fetch & update novels from internet")
        formatter = self.parser.add_argument_group("Formatter Options")
        formatter.add_argument("-t", "--theme", default=self.conf["default_theme"], help="set novel's theme", type=str)
        formatter.add_argument(
            "-m", "--media", default="", help="generate html supporting only one media type", type=str
        )
        formatter.add_argument("-r", "--renew", action="store_true", help="force to update all files")
        formatter.add_argument(
            "-e", "--episode", default=0, help="set download single episode as short novel", type=int
        )
        output = self.parser.add_argument_group("Output Options")
        output.add_argument(
            "-n", "--name", default=self.conf["output_format"], help="set output directory/file name", type=str
        )
        output.add_argument(
            "-d", "--dir", default=str(self.conf["output_path"]), help="set output directory", type=str
        )
        index = ["src", "quiet", "axel", "episode", "theme", "media", "renew", "name", "dir", "from_file", "update"]
        self.opts = {i: self.parser.get_default(i) for i in index}
        self.opts["dir"] = Path(self.opts["dir"])
        self.opts["src"] = [self.opts["src"]]

    def parse_args(self, args):
        option = self.parser.parse_args(args).__dict__
        option["dir"] = Path(option["dir"])
        self.opts = self.verify_options(option)

    def update_args(self, args):
        deepupdate(self.opts, self.verify_options(args))

    def verify_options(self, opts):
        if not isinstance(opts.get("src", []), list):
            opts["src"] = [opts["src"]]

        for key in list(opts):
            if key not in self.opts:
                opts.pop(key)
            elif type(opts[key]) != type(self.opts[key]):
                opts.pop(key)

        if opts.get("src"):
            self.env["src"] = MultipleSrc(opts["src"])

        if opts.get("quiet"):
            self.env["bar_output"] = [sys.stdout, open(os.devnull, "w")][opts["quiet"]]

        if opts.get("update"):
            opts["renew"] = True

        if opts.get("theme") and not opts["theme"] in self.env["THEMES"]:
            raise NDLE("Invalid theme name `" + opts["theme"] + "`")

        if opts.get("axel"):
            self.env["delay"] = self.conf["min_delay"]
        elif opts.get("axel") is False:
            self.env["delay"] = self.conf["default_delay"]

        return opts
