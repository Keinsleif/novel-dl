from .default import NarouND, KakuyomuND

def get_downloader(url):
    klass = {name:func for name,func in globals().items() if name.endswith('ND')}
    for i in klass:
        if klass[i].match_url(url):
            return klass[i]
    else:
        return None
