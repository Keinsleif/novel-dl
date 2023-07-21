from pathlib import Path
import json
from copy import deepcopy
from .default import NarouND, KakuyomuND


def get_downloader(src):
    klass = {name: func for name, func in globals().items() if name.endswith("ND")}
    for i in klass:
        if klass[i].match_url(src):
            return klass[i]
    else:
        return None


def get_file_nd(em):
    path = em.env["src"].src
    p = Path(path).expanduser()
    if p.is_dir() and (p / "static/db.json").is_file():
        with open(p / "static/db.json", "r", encoding="utf-8") as f:
            db = json.load(f)
        bc = get_downloader(db["url"])

        def __init__(self, em_orig):
            em = deepcopy(em_orig)
            em.update_options({"src": db["url"]})
            super(self.__class__, self).__init__(em)
            self.info["indexurl"] = db["url"]

        def _get(self, path):
            p = Path(path).expanduser()
            with p.open(encoding="utf-8") as f:
                data = f.read()
            return data

        def gen_db(self, db_data={}):
            return db

        if em.opts["update"]:
            FileND = type(
                "FileND",
                (bc,),
                dict(__init__=__init__),
            )
        else:
            FileND = type(
                "FileND",
                (bc,),
                dict(
                    BASE_URL=path.rstrip("/"), INDEX_URL="{base}/index.html", __init__=__init__, _get=_get, gen_db=gen_db
                ),
            )
        return FileND
    else:
        return None
