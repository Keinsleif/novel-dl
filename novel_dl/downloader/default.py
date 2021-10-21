import time, re, sys, json, os
import urllib.parse
from datetime import datetime as dtime
from pytz import timezone
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup as bs4
from tqdm import tqdm
from ..utils import *


class NovelDownloader(object):
    HEADER = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0"}
    COOKIE = {}

    def __init__(self, url, delay=1, params=None,bar_output=sys.stdout):
        self.status = ["INIT"]
        self.bar_output=bar_output
        self._markers = ["dl", "skip"]
        self.url = url
        self.delay = delay
        self.params = params
        self.session = requests.Session()
        self.set_headers(self.HEADER)
        self.set_cookies(self.COOKIE)
        retries = Retry(total=3, backoff_factor=1)
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        self.session.mount("http://", HTTPAdapter(max_retries=retries))
        self.info = {"title": "", "desc": "", "author": [], "type": "", "num_parts": 0, "index": [], "epis": {}}
        self._mark = []
        self.novels = {}

    def __del__(self):
        self.close()

    def initialize(self):
        self.info = {"title": "", "desc": "", "author": "", "type": "", "num_parts": 0, "index": [], "epis": {}}

    def close(self):
        self.session.close()

    def set_cookies(self, cookies):
        self.session.cookies.update(cookies)

    def get_cookies(self):
        return self.session.cookies

    def set_headers(self, headers):
        self.session.headers.update(headers)

    def get_headers(self):
        return self.session.headers

    def get(self, url, params=None):
        if not params:
            params = self.params
        result = self.session.get(url, params=params)
        return result

    def mark_part(self, com, part):
        if not "INFO" in self.status:
            self.extract_info()
        if part>0 and part<=self.info["num_parts"]:
            if com == "skip" and part in self._mark:
                self._mark.remove(part)
            elif com == "unskip" and not part in self._mark:
                self._mark.append(part)

    def mark_all(self,com):
        if not "INFO" in self.status:
            self.extract_info()
        if com == "skip":
            self._mark.clear()
        elif com == "unskip":
            self._mark = list(range(1,self.info["num_parts"]+1))

    def match_url(url):
        pass

    def extract_info(self):
        try:
            self.initialize()
            self._real_extract_info()
        except KeyboardInterrupt:
            raise_error("Operation canceled by user")
        except requests.exceptions.ConnectionError as e:
            raise_error("Network Error")
        self.status.append("INFO")
        self._mark = list(range(1, self.info["num_parts"]+1))

    def extract_novels(self):
        if not "INFO" in self.status:
            result = self.extract_info()
            if result == -1:
                return -1
        try:
            self._real_extract_novels()
        except KeyboardInterrupt:
            raise_error("Operation was canceled by user",id=1)
        except requests.exceptions.ConnectionError as e:
            raise_error("Network Error",id=1)
        self.status.append("NOVELS")

    def _real_extract_info(self):
        pass

    def _real_extract_novels(self):
        pass

    def gen_db(self,db_data={}):
        db = {"url": self.indexurl, "title": self.info["title"], "num_parts": self.info["num_parts"], "author": self.info["author"], "epis": {}}
        if db_data:
            db["epis"]={int(i):j for i,j in db_data["epis"].items()}
        db["epis"].update({i:self.info["epis"][i]["time"].isoformat() for i in self.novels})
        return db


class NarouND(NovelDownloader):
    COOKIE = {'over18': 'yes'}

    def __init__(self, url, delay=1, params=None, bar_output=sys.stdout):
        self.auto_theme = "narou"
        super().__init__(url, delay, params,bar_output=bar_output)
        ret = urllib.parse.urlparse(url)
        self.ncode = re.match(r'/(n[0-9a-zA-Z]+)', ret.path).group(1)
        self.baseurl = "https://{}".format(ret.hostname)
        self.indexurl = self.baseurl+"/"+self.ncode

    def match_url(url):
        ret = urllib.parse.urlparse(url)
        if ret.hostname == "ncode.syosetu.com" or ret.hostname == "novel18.syosetu.com":
            return True
        else:
            return False

    def _real_extract_info(self):
        data = self.get(self.indexurl)
        top_data = bs4(data.content, "html.parser")
        if top_data.select_one(".maintenance-container"):
            raise_error("Narou is under maintenance")
        self.info["title"] = top_data.select_one("title").text
        author_data = top_data.select_one(".novel_writername")
        if author_data.a:
            self.info["author"] = [author_data.a.text,author_data.a.attrs["href"]]
        else:
            self.info["author"] = [author_data.text[4:][:-1],""]
        index_raw = top_data.select_one(".index_box")
        if index_raw:
            self.info["num_parts"] = len(index_raw.select(".novel_sublist2"))
            self.info["type"] = "serial"
        else:
            self.info["num_parts"] = 0
            self.info["type"] = "short"
            body = top_data.select_one("#novel_honbun")
            l = [bs4(str(i), "html.parser") for i in body("p")]
            [i.p.unwrap() for i in l]
            body = [str(i) for i in l]
            self.novels.update({0:(self.info["title"], body)})
            self.status.append("NOVELS")
            return

        eles = bs4(str(index_raw).replace("\n", ""),"html.parser").contents[0].contents
        c = ""
        cid = 1
        part = 1
        for ele in eles:
            if re.match(r'.+chapter_title', str(ele)):
                self.info["index"].append({"type": "chapter", "id":cid, "text": ele.text})
                c = ele.text
                cid = cid+1
            elif re.match(r'.+novel_sublist2', str(ele)):
                timestamp = dtime.strptime(ele.dt.text.replace("（改）", ""), "%Y/%m/%d %H:%M")
                self.info["index"].append({"type": "episode", "part": part, "text": ele.a.text,"time": timestamp})
                self.info["epis"][part]={"subtitle": ele.a.text, "url": self.baseurl+ele.a.attrs['href'], "chap": c, "time": timestamp}
                part = part+1
        self.info["desc"] = "".join([str(i) for i in top_data.select_one("#novel_ex").contents])

    def _real_extract_novels(self):
        if self.info["num_parts"] == 0:
            return
        with tqdm(total=len(self._mark),file=self.bar_output,unit="parts") as pbar:
            pbar.set_description("Downloading ")
            for part in self._mark:
                res = self.get(self.info["epis"][part]["url"])
                soup = bs4(res.content, "html.parser")
                subtitle = soup.select_one(".novel_subtitle").text
                body = soup.select_one("#novel_honbun")

                l = [bs4(str(i), "html.parser") for i in body("p")]
                [i.p.unwrap() for i in l]
                body = [str(i) for i in l]

                self.novels.update({part:(subtitle, body)})
                pbar.update()
                time.sleep(self.delay)


class KakuyomuND(NovelDownloader):
    def __init__(self,url,delay=1,params=None, bar_output=sys.stdout):
        self.auto_theme = "kakuyomu"
        super().__init__(url,delay,params,bar_output=bar_output)
        ret = urllib.parse.urlparse(url)
        self.ncode = re.match(r'/works/([0-9]+)',ret.path).group(1)
        self.baseurl = "https://{}".format(ret.hostname)
        self.indexurl = self.baseurl+"/works/"+self.ncode

    def match_url(url):
        ret = urllib.parse.urlparse(url)
        if ret.hostname == "kakuyomu.jp":
            return True
        else:
            return False

    def _real_extract_info(self):
        data = self.get(self.indexurl)
        top_data = bs4(data.content, "html.parser")
        index_raw=top_data.select_one(".widget-toc-items")
        raws=index_raw.select("li.widget-toc-episode")
        self.info["num_parts"] = len(raws)
        self.info["type"] = "serial"
        author_data = top_data.select_one("#workAuthor-activityName")
        self.info["author"] = [author_data.a.text,self.baseurl+author_data.a.attrs["href"]]
        self.info["title"] = top_data.select_one("#workTitle").text
        eles = bs4(str(index_raw).replace("\n",""),"html.parser").contents[0].contents
        c = ""
        cid = 1
        part = 1
        for ele in eles:
            if re.match(r'.+widget-toc-chapter',str(ele)):
                self.info["index"].append({"type": "chapter", "id": cid, "text": ele.text})
                c = ele.text
            elif re.match(r'.+widget-toc-episode',str(ele)):
                timestamp=dtime.strptime(ele.a.time.get('datetime'),"%Y-%m-%dT%H:%M:%SZ").astimezone(timezone('Asia/Tokyo'))
                self.info["index"].append({"type": "episode", "part": part, "text": ele.span.text, "time": timestamp})
                self.info["epis"][part]={"subtitle": ele.span.text, "url": self.baseurl+ele.a.attrs["href"], "chap": c, "time": timestamp}
                part=part+1
        desc=top_data.select_one("#introduction")
        if desc.select_one(".ui-truncateTextButton-expandButton"):
            desc.select_one(".ui-truncateTextButton-expandButton").decompose()
            desc.span.unwrap()
        self.info["desc"]="".join([str(i) for i in desc.contents])

    def _real_extract_novels(self):
        with tqdm(total=len(self._mark),file=self.bar_output,unit="parts") as pbar:
            pbar.set_description("Downloading ")
            for part in self._mark:
                res = self.get(self.info["epis"][part]["url"])
                soup = bs4(res.content, "html.parser")
                subtitle=soup.select_one(".widget-episodeTitle").text
                body=soup.select_one(".widget-episodeBody")

                l=[bs4(str(i),"html.parser") for i in body("p")]
                [i.p.unwrap() for i in l]
                body=[str(i) for i in l]

                self.novels.update({part:(subtitle, body)})
                pbar.update()
                time.sleep(self.delay)
