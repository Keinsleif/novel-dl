from pathlib import Path
import json
from types import FunctionType, MethodType
from .default import NarouND, KakuyomuND

def get_downloader(url):
    klass = {name:func for name,func in globals().items() if name.endswith('ND')}
    for i in klass:
        if klass[i].match_url(url):
            return klass[i]
    else:
        return None

def get_file_nd(path):
    p=Path(path)
    if p.is_dir():
        with open(p / "static/db.json","r") as f:
            db=json.load(f)
        bc = get_downloader(db["url"])
        def __init__(self,em):
            em.env["delay"]=em.conf["min_delay"]
            super(self.__class__,self).__init__(db["url"],em)
        def get(self,path):
            with open(path,"r") as f:
                data=f.read()
            return data
        FileND=type("FileND",(bc,),dict(BASE_URL=path.rstrip("/")+"/",INDEX_URL="{base}/index.html",__init__=__init__,get=get))
        return FileND
    else:
        return None