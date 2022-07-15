from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateNotFound
import time
import re
import sys
import os
import shutil
import argparse
import json
import urllib.parse
from datetime import datetime
from .downloader import get_downloader
from .utils import (
    NovelDLException as NDLE,
    deepupdate,
)
from .info import __version__

root = os.path.abspath(os.path.dirname(__file__))+"/"
THEMES = ["auto"]+os.listdir(root+"themes/")
url_reg = re.compile("https?://[\w/:%#\$&\?\(\)~\.=\+\-]+")


def main(args):
    if args["quiet"]:
        bar_output = open(os.devnull, "w")
    else:
        bar_output = sys.stdout

    if not args["theme"] in THEMES:
        raise NDLE('Invalid theme name `'+args["theme"]+'`')

    if args["axel"]:
        delay = 0.1
    else:
        delay = 1

    nd_klass = get_downloader(args["url"])
    if nd_klass:
        nd = nd_klass(args["url"], delay=delay, bar_output=bar_output)
    else:
        raise NDLE("URL is not supported")

    nd.extract_info()

    if args["episode"]:
        if not re.match(r'^\d*$', args["episode"]) or int(args["episode"]) > nd.info["num_parts"] or int(args["episode"]) < 0:
            raise NDLE("Incorrect episode number `"+args["episode"]+"`")
        nd.mark_all("skip")
        nd.mark_part("dl", int(args["episode"]))
        args["episode"] = int(args["episode"])

        # Load themes
    if args["theme"] == "auto":
        args["theme"] = nd.auto_theme
    THEME_DIR = root+"themes/"+args["theme"]+"/"
    conf_file = os.path.join(THEME_DIR, "config.json")
    conf = {}
    if os.path.isfile(conf_file):
        with open(conf_file, "r") as f:
            conf = json.load(f)
    else:
        raise NDLE("Cannot load theme config. config.json not found")

    if conf.get('parent'):
        env_paths = [THEME_DIR, os.path.join(root, "themes", conf['parent'])]
        lstatic = os.listdir(THEME_DIR+"static/")
        static_files = [THEME_DIR+"static/"+i for i in lstatic]+[os.path.join(
            env_paths[1], "static", i) for i in os.listdir(os.path.join(env_paths[1], "static")) if not i in lstatic]
        pconf_file = os.path.join(
            root, "themes", conf['parent'], "config.json")
        if os.path.isfile(pconf_file):
            with open(pconf_file, "r") as f:
                deepupdate(conf, json.load(f))
        else:
            raise NDLE(
                "Cannot load theme config. parent config.json not found")
    else:
        env_paths = THEME_DIR
        static_files = [os.path.join(THEME_DIR, "static", i)
                        for i in os.listdir(os.path.join(THEME_DIR, "static"))]

    MEDIAS = [""]
    if conf.get("medias"):
        MEDIAS = conf["medias"]
    if not args["media"] in MEDIAS:
        MEDIAS.remove("")
        raise NDLE("Invalid media type\nAvailable medias in this theme: ({})".format(
            " ".join(MEDIAS)))

    if args["media"]:
        htmls = {"base": "base_{}.html".format(args["media"]), "index": "index_{}.html".format(
            args["media"]), "single": "single_{}.html".format(args["media"])}
    else:
        htmls = {"base": "base.html",
                 "index": "index.html", "single": "single.html"}
    env = Environment(loader=FileSystemLoader(env_paths, encoding='utf8'))
    try:
        htmls = {i: env.get_template(htmls[i]) for i in htmls}
    except TemplateNotFound as e:
        raise NDLE("Cannot load theme file: "+e.name)
    loads = {"js": [], "css": []}
    if conf.get('loads'):
        if type(conf["loads"].get('js')) is list:
            loads["js"] = conf['loads']['js']

        if type(conf["loads"].get('css')) is dict:
            loads["css"] = [[j, k] for k, v in conf["loads"]['css'].items()
                            for j in v]

    try:
        if nd.info["num_parts"] == 0 or args["episode"]:
            ntype = "short"
        else:
            ntype = "series"
        if args["episode"]:
            args["name"] = args["name"].format("", ncode=nd.ncode, title=re.sub(
                r'[\\|/|:|?|.|"|<|>|\|]', '', nd.info["title"]), media=args["media"], theme=args["theme"], type=ntype,episode=args["episode"])
        args["name"] = args["name"].format("", ncode=nd.ncode, title=re.sub(
            r'[\\|/|:|?|.|"|<|>|\|]', '', nd.info["title"]), media=args["media"], theme=args["theme"], type=ntype)
    except KeyError:
        raise NDLE("Incorrect directory name format")
    now = datetime.now()
    args["name"] = now.strftime(args["name"])
    db_data = {}

    if nd.info["num_parts"] == 0 or args["episode"]:
        if args["dir"]:
            ndir = os.path.abspath(args["dir"])+"/"
        else:
            ndir = os.getcwd()+"/"
    else:
        if args["dir"]:
            ndir = os.path.abspath(args["dir"])+"/"+args["name"]+"/"
        else:
            ndir = os.getcwd()+"/"+args["name"]+"/"
        if os.path.isfile(ndir+"static/db.json") and not args["renew"]:
            with open(ndir+"static/db.json", "r") as f:
                db_data = json.load(f)
            nd.mark_all("skip")
            if nd.info["num_parts"] > db_data["num_parts"]:
                nd.mark_part("dl", db_data["num_parts"])
            for i in nd.info["epis"].keys():
                if not str(i) in db_data["epis"]:
                    nd.mark_part("dl", i)
                elif nd.info["epis"][i]["time"] > datetime.fromisoformat(db_data["epis"][str(i)]):
                    nd.mark_part("dl", i)

    try:
        nd.extract_novels()
    except NovelDLException as e:
        if e.return_id() == 1:
            e.console_message()
        else:
            raise e

    # Create directory
    if not os.path.isdir(ndir):
        os.makedirs(ndir)

    if nd.info["type"] == "short" or args["episode"]:
        style = []
        script = []
        for file in loads['css']:
            paths = [re.match(
                ".*/"+file[0], i).string for i in static_files if re.match(".*/"+file[0], i)]
            if paths:
                with open(paths[0], "r", encoding="utf-8") as f:
                    style.append([f.read(), file[1]])
        for file in loads['js']:
            paths = [re.match(
                ".*/"+file, i).string for i in static_files if re.match(".*/"+file, i)]
            if paths:
                with open(paths[0], "r", encoding="utf-8") as f:
                    script.append(f.read())

        if args["episode"]:
            contents = htmls['single'].render(title=nd.novels[args["episode"]][0], author=nd.info["author"], contents=nd.novels[args["episode"]]
                                              [1], style=style, script=script, lines=len(nd.novels[args["episode"]][1]), url=args["url"])
        else:
            contents = htmls['single'].render(title=nd.info["title"], author=nd.info["author"], contents=nd.novels[0]
                                              [1], style=style, script=script, lines=len(nd.novels[0][1]), url=args["url"])
        with open(ndir+args["name"]+".html", "w") as f:
            f.write(contents)
        return ndir+args["name"]+".html"
    else:
        # Gen index.html
        contents = htmls['index'].render(title=nd.info["title"], author=nd.info["author"], desc=nd.info["desc"],
                                         index=nd.info["index"], total=nd.info["num_parts"], url=nd.indexurl, loads=loads)
        with open(ndir+"index.html", "w", encoding="utf-8") as f:
            f.write(contents)

            # Copy statics
        if not os.path.islink(ndir+"static"):
            if os.path.isdir(ndir+"static"):
                shutil.rmtree(ndir+"static")
            elif os.path.isfile(ndir+"static"):
                os.remove(ndir+"static")
            # os.symlink(THEME_DIR+"static",ndir+"static")
            os.mkdir(ndir+"static")
            for file in static_files:
                shutil.copyfile(file, ndir+"static/"+os.path.basename(file))

        with open(ndir+"static/db.json", "w") as f:
            json.dump(nd.gen_db(db_data), f, ensure_ascii=False,
                      indent=4, sort_keys=True, separators=(',', ': '))

        for part in nd.novels:
            contents = htmls['base'].render(title=nd.info["title"], author=nd.info["author"], subtitle=nd.novels[part][0], part=part, total=nd.info["num_parts"],
                                            contents=nd.novels[part][1], lines=len(nd.novels[part][1]), index=nd.info["index"], epis=nd.info["epis"], url=nd.info["epis"][part]["url"], loads=loads)
            with open(ndir+str(part)+".html", "w", encoding="utf-8") as f:
                f.write(contents)
        return ndir


def command_line():
    kw = {
        'usage': '%(prog)s [OPTIONS] URL',
        'conflict_handler': 'resolve'
    }
    parser = argparse.ArgumentParser(**kw)
    parser.add_argument('url', help="URL")
    general = parser.add_argument_group("General Options")
    general.add_argument('-h', '--help', action="help",
                         help="show this help text and exit")
    general.add_argument('-v', '--version', action="version",
                         version="%(prog)s {}".format(__version__))
    general.add_argument('-q', "--quiet", action='store_true',
                         help="suppress non-messages")
    downloader = parser.add_argument_group("Downloader Options")
    downloader.add_argument('-a', "--axel", action='store_true',
                            help="turn on axceleration mode")
    formatter = parser.add_argument_group("Formatter Options")
    formatter.add_argument('-e', "--episode", default="",
                           help="set download single episode as short novel")
    formatter.add_argument('-t', "--theme", default="auto",
                           help="set novel's theme")
    formatter.add_argument('-m', "--media", default="",
                           help="generate html supporting only one media type")
    formatter.add_argument('-r', "--renew", action='store_true',
                           help="force to update all files")
    output = parser.add_argument_group("Output Options")
    output.add_argument(
        '-n', "--name", default="{title}", help="set output directory/file name")
    output.add_argument('-d', "--dir", default="", help="set output directory")
    print(parser.parse_args().__dict__)
    args = parser.parse_args()
    args = args.__dict__
    return_code=0
    try:
        main(args)
    except NovelDLException as e:
        e.console_message()
        return_code=1
    else:
        if not args["quiet"]:
            print("Successfully downloaded")
    finally:
        return return_code

def args(url="", save_dir="", renew=False, axel=False, episode="", theme="", media=""):
    return {"url": url, "dir": save_dir, "renew": renew, "axel": axel, "episode": episode, "theme": theme, "media": media}


if __name__ == "__main__":
    command_line()
