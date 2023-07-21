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
