import time, re
from urllib.parse import urlparse, urljoin
from datetime import datetime as dtime
from pytz import timezone
from requests import Session
from requests.exceptions import ConnectionError
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup as bs4
from tqdm import tqdm
from ..utils import (
    NovelDLException as NDLE,
    cjoin,
)


class NovelDownloader(object):
    _markers = ["get", "skip"]

    def __init__(self, em):
        self.classname = self.__class__.__name__
        self.status = []
        self._set_status = self.status.append
        self._em = em
        self.bar_output = self._em.env["bar_output"]
        self.initialize()

    def __del__(self):
        pass

    def initialize(self):
        self.info = {
            "title": "",
            "desc": "",
            "author": [],
            "type": "",
            "num_parts": 0,
            "index": [],
            "epis": {},
            "indexurl": "",
        }
        self._mark = []
        self.novels = {}
        self._set_status("INIT")

    def mark_part(self, com, part):
        if not "INFO" in self.status:
            self.fetch_info()
        if not com in self._markers:
            raise NDLE("[{klass}] mark error: Invalid mark name", klass=self.classname)
        if part > 0 and part <= self.info["num_parts"]:
            if com == "skip" and part in self._mark:
                self._mark.remove(part)
            elif com == "get" and not part in self._mark:
                self._mark.append(part)

    def mark_all(self, com):
        if not "INFO" in self.status:
            self.fetch_info()
        if not com in self._markers:
            raise NDLE("[{klass}] mark error: Invalid mark name", klass=self.classname)
        if com == "skip":
            self._mark.clear()
        elif com == "get":
            self._mark = list(range(1, self.info["num_parts"] + 1))

    @classmethod
    def match_url(cls, url):
        pass

    def fetch_info(self):
        try:
            if "NOVELS" in self.status:
                self.initialize()
            self._real_fetch_info()
        except KeyboardInterrupt:
            raise NDLE("Operation canceled by user")
        else:
            self._set_status("INFO")
            self._mark = list(range(1, self.info["num_parts"] + 1))
        return self

    def fetch_novels(self):
        if not "INFO" in self.status:
            self.fetch_info()
        print(
            "Fetching {title} / {author[0]} {to_get} / {num_parts} parts".format(**self.info, to_get=len(self._mark)),
            file=self.bar_output,
        )
        try:
            self._real_fetch_novels()
        except KeyboardInterrupt:
            raise NDLE("Operation was canceled by user")
        self._set_status("NOVELS")
        return self

    def _real_fetch_info(self):
        pass

    def _real_fetch_novels(self):
        pass

    def gen_db(self, db_data={}):
        db = {
            "url": self.info["indexurl"],
            "title": self.info["title"],
            "num_parts": self.info["num_parts"],
            "author": self.info["author"],
            "epis": {},
        }
        if db_data:
            db["epis"] = {int(i): j for i, j in db_data["epis"].items()}
        db["epis"].update({i: self.info["epis"][i]["time"].isoformat() for i in self.novels})
        return db


class HttpNovelDownloader(NovelDownloader):
    HEADER = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0"}
    COOKIE = {}
    URL_REG = re.compile(r"https?://[\w/:%#\$&\?\(\)~\.=\+\-]+")

    def __init__(self, em):
        super().__init__(em)
        self.url = self._em.env["src"].src
        self.delay = self._em.env["delay"]
        self.params = {}
        self.session = Session()
        self.set_headers(self.HEADER,self._em.conf["headers"])
        self.set_cookies(self.COOKIE,self._em.conf["cookies"])
        self.timeout=self._em.conf["timeout"]
        retries = Retry(total=self._em.conf["retries"], backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        self.session.mount("http://", HTTPAdapter(max_retries=retries))

    def __del__(self):
        self.session.close()

    @classmethod
    def match_url(cls, url):
        if re.match(r"https?://[\w/:%#\$&\?\(\)~\.=\+\-]+", url):
            return True
        else:
            return False

    def set_cookies(self, *cookies):
        [self.session.cookies.update(c) for c in cookies]

    def get_cookies(self):
        return self.session.cookies

    def set_headers(self, *headers):
        [self.session.headers.update(h) for h in headers]

    def get_headers(self):
        return self.session.headers

    def _get(self, url, params=None, timeout=()):
        if not params:
            params = self.params
        if not timeout:
            timeout = self.timeout
        result = self.session.get(url, params=params, timeout=self.timeout)
        return result.content

    def fetch_info(self):
        try:
            if "NOVELS" in self.status:
                self.initialize()
            self._real_fetch_info()
        except KeyboardInterrupt:
            raise NDLE("Operation canceled by user")
        except ConnectionError as e:
            raise NDLE("[{klass}] Network Error", klass=self.classname)
        else:
            self._mark = list(range(1, self.info["num_parts"] + 1))
            self._set_status("INFO")
        return self

    def fetch_novels(self):
        if not "INFO" in self.status:
            self.fetch_info()
        try:
            self._real_fetch_novels()
        except KeyboardInterrupt:
            raise NDLE("Operation was canceled by user")
        except ConnectionError as e:
            raise NDLE("Network Error", id=1, klass=self.classname)
        self._set_status("NOVELS")
        return self


class NarouND(HttpNovelDownloader):
    COOKIE = {"over18": "yes"}
    BASE_URL = "{scheme}://{host}"
    INDEX_URL = "{base}/{ncode}"
    AUTO_THEME = "narou"
    NCODE_PATTERN = re.compile(r"/(n[0-9a-zA-Z]+)")

    def __init__(self, em):
        super().__init__(em)
        ret = urlparse(self.url)
        m = self.NCODE_PATTERN.match(ret.path)
        assert m is not None
        self.ncode = m.group(1)
        self.baseurl = self.BASE_URL.format(scheme=ret.scheme, host=ret.hostname)
        self.indexurl = self.INDEX_URL.format(base=self.baseurl, ncode=self.ncode)
        self.info["indexurl"] = self.indexurl

    @classmethod
    def match_url(cls, url):
        p = super().match_url(url)
        ret = urlparse(url)
        f = ret.hostname == "ncode.syosetu.com" or ret.hostname == "novel18.syosetu.com"
        if p and f and cls.NCODE_PATTERN.match(ret.path):
            return True
        else:
            return False

    def _real_fetch_info(self):
        data = self._get(self.indexurl)
        top_data = bs4(data, "html.parser")
        if top_data.select_one(".maintenance-container"):
            raise NDLE("[{klass}] Narou is under maintenance", klass=self.classname)
        if top_data.select_one(".nothing"):
            raise NDLE(
                "[{klass}] Novel not found: {detail}",
                klass=self.classname,
                detail=top_data.select_one(".nothing").text,
            )
        self.info["title"] = top_data.select_one("title").text
        author_data = top_data.select_one(".novel_writername")
        if not author_data:
            self.info["author"] = ["unknown",""]
        elif author_data.find("a"):
            self.info["author"] = [author_data.a.text, author_data.a.attrs["href"]]
        else:
            self.info["author"] = [author_data.text[4:][:-1], ""]
        index_raw = top_data.select_one(".index_box")
        if index_raw:
            self.info["num_parts"] = len(index_raw.select(".novel_sublist2"))
            self.info["type"] = "serial"
        else:
            self.info["num_parts"] = 0
            self.info["type"] = "short"

        eles = bs4(str(index_raw).replace("\n", ""), "html.parser").contents[0].contents
        c = ""
        cid = 1
        part = 1
        for ele in eles:
            if re.match(r".+chapter_title", str(ele)):
                self.info["index"].append({"type": "chapter", "id": cid, "text": ele.text})
                c = ele.text
                cid = cid + 1
            elif re.match(r".+novel_sublist2", str(ele)):
                timestamp = dtime.strptime(ele.dt.text.replace("（改）", ""), "%Y/%m/%d %H:%M")
                self.info["index"].append({"type": "episode", "part": part, "text": ele.a.text, "time": timestamp})
                self.info["epis"][part] = {
                    "subtitle": ele.a.text,
                    "url": cjoin(self.baseurl, ele.a.attrs["href"]),
                    "chap": c,
                    "time": timestamp,
                }
                part = part + 1
        self.info["desc"] = "".join([str(i) for i in top_data.select_one("#novel_ex").contents])

    def _real_fetch_novels(self):
        if self.info["type"] == "short":
            data = self._get(self.indexurl)
            top_data = bs4(data, "html.parser")
            body = top_data.select_one("#novel_honbun")
            l = [bs4(str(i), "html.parser") for i in body("p")]
            [i.p.unwrap() for i in l]
            body = [str(i) for i in l]
            self.novels.update({0: (self.info["title"], body)})
            return
        with tqdm(total=len(self._mark), file=self.bar_output, unit="parts") as pbar:
            for part in self._mark:
                res = self._get(self.info["epis"][part]["url"])
                soup = bs4(res, "html.parser")
                subtitle = soup.select_one(".novel_subtitle").text
                body = soup.select_one("#novel_honbun")

                l = [bs4(str(i), "html.parser") for i in body("p")]
                [i.p.unwrap() for i in l]
                [
                    (
                        l[i].img.attrs.update({"src": urljoin("https://", l[i].img.attrs["src"])}),
                        l[i].a.attrs.update({"href": urljoin("https://", l[i].a.attrs["href"])}),
                    )
                    for i in range(0, len(l))
                    if l[i].img
                ]
                body = [str(i) for i in l]

                self.novels.update({part: (subtitle, body)})
                pbar.update()
                time.sleep(self.delay)


class KakuyomuND(HttpNovelDownloader):
    BASE_URL = "{scheme}://kakuyomu.jp"
    INDEX_URL = "{base}/works/{ncode}"
    AUTO_THEME = "kakuyomu"

    def __init__(self, em):
        super().__init__(em)
        ret = urlparse(self.url)
        self.ncode = re.match(r"/works/([0-9]+)", ret.path).group(1)
        self.baseurl = self.BASE_URL.format(scheme=ret.scheme)
        self.indexurl = self.INDEX_URL.format(base=self.baseurl, ncode=self.ncode)

    @classmethod
    def match_url(cls, url):
        p = super().match_url(url)
        ret = urlparse(url)
        if p and ret.hostname == "kakuyomu.jp" and re.match(r"/works/([0-9]+)", ret.path):
            return True
        else:
            return False

    def _real_fetch_info(self):
        data = self._get(self.indexurl)
        top_data = bs4(data, "html.parser")
        index_raw = top_data.select_one(".widget-toc-items")
        raws = index_raw.select("li.widget-toc-episode")
        self.info["num_parts"] = len(raws)
        self.info["type"] = "serial"
        author_data = top_data.select_one("#workAuthor-activityName")
        self.info["author"] = [author_data.a.text, self.baseurl + author_data.a.attrs["href"]]
        self.info["title"] = top_data.select_one("#workTitle").text
        eles = bs4(str(index_raw).replace("\n", ""), "html.parser").contents[0].contents
        c = ""
        cid = 1
        part = 1
        for ele in eles:
            if re.match(r".+widget-toc-chapter", str(ele)):
                self.info["index"].append({"type": "chapter", "id": cid, "text": ele.text})
                c = ele.text
            elif re.match(r".+widget-toc-episode", str(ele)):
                timestamp = dtime.strptime(ele.time.get("datetime"), "%Y-%m-%dT%H:%M:%SZ").astimezone(
                    timezone("Asia/Tokyo")
                )
                self.info["index"].append({"type": "episode", "part": part, "text": ele.span.text, "time": timestamp})
                self.info["epis"][part] = {
                    "subtitle": ele.span.text,
                    "url": cjoin(self.baseurl, ele.a.attrs["href"]),
                    "chap": c,
                    "time": timestamp,
                }
                part = part + 1
        desc = top_data.select_one("#introduction")
        if desc.select_one(".ui-truncateTextButton-expandButton"):
            desc.select_one(".ui-truncateTextButton-expandButton").decompose()
            desc.span.unwrap()
        self.info["desc"] = "".join([str(i) for i in desc.contents])

    def _real_fetch_novels(self):
        with tqdm(total=len(self._mark), file=self.bar_output, unit="parts") as pbar:
            for part in self._mark:
                res = self._get(self.info["epis"][part]["url"])
                soup = bs4(res, "html.parser")
                subtitle = soup.select_one(".widget-episodeTitle").text
                body = soup.select_one(".widget-episodeBody")

                l = [bs4(str(i), "html.parser") for i in body("p")]
                [i.p.unwrap() for i in l]
                body = [str(i) for i in l]

                self.novels.update({part: (subtitle, body)})
                pbar.update()
                time.sleep(self.delay)
