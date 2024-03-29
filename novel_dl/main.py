import re
import sys
import shutil
import json
from pathlib import Path
import traceback
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateNotFound
from pytz import timezone
from .downloader import get_downloader
from .option import EnvManager
from .utils import (
    NovelDLException as NDLE,
    deepupdate,
)
from .info import __version__

root = Path(__file__).parent.resolve()


def novel_dl(em):
    while True:
        nd_klass = get_downloader(em.env["src"].src)
        if nd_klass:
            nd = nd_klass(em)
        else:
            raise NDLE("src is not supported")

        nd.fetch_info()

        if em.opts["episode"]:
            if not (0 < em.opts["episode"] <= nd.info["num_parts"]):
                raise NDLE("Incorrect episode number `{num}`", num=em.opts["episode"])
            nd.mark_all("skip")
            nd.mark_part("get", em.opts["episode"])

            # Load themes
        if em.opts["theme"] == "auto":
            em.update_options({"theme": nd.AUTO_THEME})
        THEME_DIR = root / "themes" / em.opts["theme"]
        conf_file = THEME_DIR / "config.json"
        conf = {}
        if conf_file.is_file():
            with conf_file.open(encoding="utf-8") as f:
                conf = json.load(f)
        else:
            raise NDLE("Cannot load theme config. config.json not found")

        if conf.get("parent"):
            env_paths = [THEME_DIR, root / "themes" / conf["parent"]]
            lstatic = (THEME_DIR / "static").iterdir()
            static_files = list(lstatic) + [i for i in (env_paths[1] / "static").iterdir() if not i in lstatic]
            pconf_file = root / "themes" / conf["parent"] / "config.json"
            if pconf_file.is_file():
                with pconf_file.open(encoding="utf-8") as f:
                    pconf = json.load(f)
                    deepupdate(pconf, conf)
                    conf = pconf
            else:
                raise NDLE("Cannot load theme config. parent config.json not found")
        else:
            env_paths = [THEME_DIR]
            static_files = [i for i in (THEME_DIR / "static").iterdir()]

        MEDIAS = [""]
        if conf.get("medias"):
            MEDIAS = conf["medias"]
        if not em.opts["media"] in MEDIAS:
            MEDIAS.remove("")
            raise NDLE("Invalid media type\nAvailable medias in this theme: ({m})", m=", ".join(MEDIAS))

        if em.opts["media"]:
            htmls = {i: i + "_" + em.opts["media"] for i in {"base", "index", "single"}}
        else:
            htmls = {"base": "base.html", "index": "index.html", "single": "single.html"}
        env = Environment(loader=FileSystemLoader(map(str, env_paths), encoding="utf8"))
        try:
            htmls = {i: env.get_template(htmls[i]) for i in htmls}
        except TemplateNotFound as e:
            raise NDLE("Cannot load theme file: {file}", file=e.name)
        loads = {"js": [], "css": []}
        if conf.get("loads"):
            if type(conf["loads"].get("js")) is list:
                loads["js"] = conf["loads"]["js"]

            if type(conf["loads"].get("css")) is dict:
                loads["css"] = [[j, k] for k, v in conf["loads"]["css"].items() for j in v]

        try:
            if em.opts["episode"]:
                em.env["name"] = em.opts["name"].format(
                    "",
                    ncode=nd.ncode,
                    title=re.sub(r'[\\|/|:|?|.|"|<|>|\|]', "", nd.info["title"]),
                    media=em.opts["media"],
                    theme=em.opts["theme"],
                    type=nd.info["type"],
                    episode=em.opts["episode"],
                )
            em.env["name"] = em.opts["name"].format(
                "",
                ncode=nd.ncode,
                title=re.sub(r'[\\|/|:|?|.|"|<|>|\|]', "", nd.info["title"]),
                media=em.opts["media"],
                theme=em.opts["theme"],
                type=nd.info["type"],
            )
        except KeyError:
            raise NDLE("Incorrect directory name format")
        now = datetime.now()
        em.env["name"] = (
            now.strftime(em.env["name"].encode("unicode-escape").decode()).encode().decode("unicode-escape")
        )
        db_data = {}

        if nd.info["type"] == "short" or em.opts["episode"]:
            if em.opts["dir"]:
                ndir = em.opts["dir"].resolve()
            else:
                ndir = Path.cwd()
        else:
            if em.opts["dir"]:
                ndir = em.opts["dir"].resolve() / em.env["name"]
            else:
                ndir = Path.cwd() / em.env["name"]
            if (ndir / "static/db.json").is_file() and not em.opts["renew"]:
                with (ndir / "static/db.json").open(mode="r", encoding="utf-8") as f:
                    db_data = json.load(f)
                nd.mark_all("skip")
                if nd.info["num_parts"] > db_data["num_parts"]:
                    for i in range(db_data["num_parts"] + 1, nd.info["num_parts"] + 1):
                        nd.mark_part("get", i)
                for i in nd.info["epis"].keys():
                    if not str(i) in db_data["epis"]:
                        nd.mark_part("get", i)
                    elif nd.info["epis"][i]["time"] > datetime.fromisoformat(db_data["epis"][str(i)]).replace(tzinfo=timezone("Asia/Tokyo")):
                        nd.mark_part("get", i)

        try:
            nd.fetch_novels()
        except NDLE as e:
            if e.id == 1:
                e.console_message()
            else:
                raise e

        # Create directory
        if not ndir.is_dir():
            ndir.mkdir(parents=True)

        if nd.info["type"] == "short" or em.opts["episode"]:
            style = []
            script = []
            for file in loads["css"]:
                paths = [i for i in static_files if Path(file[0]).name == i.name]
                if paths:
                    with paths[0].open("r", encoding="utf-8") as f:
                        style.append([f.read(), file[1]])
            for file in loads["js"]:
                paths = [i for i in static_files if Path(file).name == i.name]
                if paths:
                    with paths[0].open("r", encoding="utf-8") as f:
                        script.append(f.read())

            if em.opts["episode"]:
                contents = htmls["single"].render(
                    title=nd.novels[em.opts["episode"]][0],
                    author=nd.info["author"],
                    contents=nd.novels[em.opts["episode"]][1],
                    style=style,
                    script=script,
                    lines=len(nd.novels[em.opts["episode"]][1]),
                    url=nd.info["indexurl"],
                )
            else:
                contents = htmls["single"].render(
                    title=nd.info["title"],
                    author=nd.info["author"],
                    contents=nd.novels[0][1],
                    style=style,
                    script=script,
                    lines=len(nd.novels[0][1]),
                    url=nd.info["indexurl"],
                )
            with (ndir / (em.env["name"] + ".html")).open(mode="w", encoding="utf-8") as f:
                f.write(contents)
        #            return ndir / em.env["name"] + ".html"
        else:
            # Gen index.html
            contents = htmls["index"].render(
                title=nd.info["title"],
                author=nd.info["author"],
                desc=nd.info["desc"],
                index=nd.info["index"],
                total=nd.info["num_parts"],
                url=nd.info["indexurl"],
                loads=loads,
            )
            with (ndir / "index.html").open(mode="w", encoding="utf-8") as f:
                f.write(contents)

            # Copy statics
            static_dst = ndir / "static"
            if static_dst.is_dir():
                shutil.rmtree(static_dst)
            elif static_dst.is_file():
                static_dst.unlink()
            static_dst.mkdir()
            if em.conf["symlink_static"]:
                for file in static_files:
                    (ndir / "static" / file.name).symlink_to(file)
            else:
                for file in static_files:
                    shutil.copyfile(file, ndir / "static" / file.name)

            with (ndir / "static/db.json").open("w", encoding="utf-8") as f:
                json.dump(nd.gen_db(db_data), f, ensure_ascii=False, indent=4, sort_keys=True, separators=(",", ": "))

            for part in nd.novels:
                contents = htmls["base"].render(
                    title=nd.info["title"],
                    author=nd.info["author"],
                    subtitle=nd.novels[part][0],
                    part=part,
                    total=nd.info["num_parts"],
                    contents=nd.novels[part][1],
                    lines=len(nd.novels[part][1]),
                    index=nd.info["index"],
                    epis=nd.info["epis"],
                    url=nd.info["epis"][part]["url"],
                    loads=loads,
                )
                with (ndir / (str(part) + ".html")).open(mode="w", encoding="utf-8") as f:
                    f.write(contents)
        #            return ndir
        if em.env["src"].has_next():
            em.env["src"].next()
        else:
            break


def command_line():
    return_code = 0
    try:
        em = EnvManager()
        em.load_usercfg()
        em.init_parser()
        em.parse_args(sys.argv[1:])
        novel_dl(em)
    except NDLE as e:
        e.console_message()
        return_code = 1
    except Exception:
        e = NDLE("Unexpected error occurred.\n{err}", err=traceback.format_exc())
        print(e.msg, file=sys.stderr)
    else:
        if not em.opts["quiet"]:
            print("Successfully downloaded")
    finally:
        em.save_usercfg()
        return return_code


def setup_em(**kw):
    em = EnvManager()
    em.load_usercfg()
    em.init_parser()
    em.update_options(kw)
    return em


if __name__ == "__main__":
    sys.exit(1)
