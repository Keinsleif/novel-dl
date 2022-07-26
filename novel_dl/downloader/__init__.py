from pathlib import Path
import json
from copy import copy
from .default import NarouND, KakuyomuND


def get_downloader(url):
    klass = {name: func for name, func in globals().items() if name.endswith("ND")}
    for i in klass:
        if klass[i].match_url(url):
            return klass[i]
    else:
        return None


def get_file_nd(path):
    p = Path(path).expanduser()
    if p.is_dir():
        with open(p / "static/db.json", "r") as f:
            db = json.load(f)
        bc = get_downloader(db["url"])

        def __init__(self, em_orig):
            em = copy(em_orig)
            em.env["delay"] = em.conf["min_delay"]
            em.update_args({"url": db["url"]})
            super(self.__class__, self).__init__(em)

        def get(self, path):
            p = Path(path).expanduser()
            with p.open() as f:
                data = f.read()
            return data

        def gen_db(self, db_data={}):
            return db

        FileND = type(
            "FileND",
            (bc,),
            dict(BASE_URL=path.rstrip("/"), INDEX_URL="{base}/index.html", __init__=__init__, get=get, gen_db=gen_db),
        )
        return FileND
    else:
        return None
