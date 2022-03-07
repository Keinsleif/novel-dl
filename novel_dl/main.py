from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateNotFound
import time, re, sys, os, shutil, argparse, json, urllib.parse
import pickle
from datetime import datetime
from .downloader import *
from .utils import *

root = os.path.abspath(os.path.dirname(__file__))+"/"
THEMES=["auto"]+os.listdir(root+"themes/")

def main(args,bar=False):
    if bar:
        bar_output=sys.stdout
    else:
        bar_output=open(os.devnull,"w")

    if not args["theme"] in THEMES:
        raise_error('Invalid theme name `'+args["theme"]+'`')

    if args["axel"]:
        delay=0.1
    else:
        delay=1

    nd_klass = get_downloader(args["url"])
    if nd_klass:
        nd = nd_klass(args["url"],delay=delay,bar_output=bar_output)
    else:
        raise_error("URL is not supported")

    nd.extract_info()

    if args["episode"]:
        if not re.match(r'^\d*$',args["episode"]) or int(args["episode"])>nd.info["num_parts"] or int(args["episode"])<0:
            raise_error("Incorrect episode number `"+args["episode"]+"`")
        nd.mark_all("skip")
        nd.mark_part("unskip",int(args["episode"]))
        args["episode"]=int(args["episode"])

    try:
        args["name"] = args["name"].format("",ncode=nd.ncode,title=re.sub(r'[\\|/|:|?|.|"|<|>|\|]', '', nd.info["title"]))
    except KeyError:
        raise_error("Incorrect format template")
    now=datetime.now()
    args["name"] = now.strftime(args["name"])
    db_data = {}

    if nd.info["num_parts"] == 0 or args["episode"]:
        if args["dir"]:
            ndir=os.path.abspath(args["dir"])+"/"
        else:
            ndir=os.getcwd()+"/"
    else:
        if args["dir"]:
            ndir=os.path.abspath(args["dir"])+"/"+args["name"]+"/"
        else:
            ndir=os.getcwd()+"/"+args["name"]+"/"
        if os.path.isfile(ndir+"static/db.json") and not args["renew"]:
            with open(ndir+"static/db.json","r") as f:
                db_data = json.load(f)
            nd.mark_all("skip")
            if nd.info["num_parts"] > db_data["num_parts"]:
                nd.mark_part("unskip",db_data["num_parts"])
            for i in nd.info["epis"].keys():
                if not str(i) in db_data["epis"]:
                    nd.mark_part("unskip",i)
                elif nd.info["epis"][i]["time"] > datetime.fromisoformat(db_data["epis"][str(i)]):
                    nd.mark_part("unskip",i)

    try:
        nd.extract_novels()
    except NovelDLException as e:
        if e.return_id() == 1:
            e.console_message()
        else:
            raise e

	# Load themes
    if args["theme"]=="auto":
        args["theme"] = nd.auto_theme
    THEME_DIR=root+"themes/"+args["theme"]+"/"
    conf_file=os.path.join(THEME_DIR,"config.json")
    conf = {}
    if os.path.isfile(conf_file):
        with open(conf_file,"r") as f:
            conf = json.load(f)
    MEDIAS=[""]
    if conf.get("medias"):
        MEDIAS=conf["medias"]
    if not args["media"] in MEDIAS:
        MEDIAS.remove("")
        raise_error("Invalid media type\nAvailable medias in this theme: ({})".format(" ".join(MEDIAS)))
    if args["media"]:
        htmls={"base":"base_{}.html".format(args["media"]),"index":"index_{}.html".format(args["media"]),"single":"single_{}.html".format(args["media"])}
    else:
        htmls={"base":"base.html","index":"index.html","single":"single.html"}

    if conf.get('parent'):
        env_paths=[THEME_DIR,os.path.join(root,"themes",conf['parent'])]
        lstatic = os.listdir(THEME_DIR+"static/")
        static_files = [THEME_DIR+"static/"+i for i in lstatic]+[os.path.join(env_paths[1],"static",i) for i in os.listdir(os.path.join(env_paths[1],"static")) if not i in lstatic]
    else:
        env_paths=THEME_DIR
        static_files = [os.path.join(THEME_DIR,"static",i) for i in os.listdir(os.path.join(THEME_DIR,"static"))]
    env=Environment(loader=FileSystemLoader(env_paths,encoding='utf8'))
    try:
        htmls={i:env.get_template(htmls[i]) for i in htmls}
    except TemplateNotFound as e:
        raise_error("Cannot load theme file: "+e.name)

    # Create directory
    if not os.path.isdir(ndir):
        os.makedirs(ndir)

    if nd.info["type"] == "short" or args["episode"]:
        style={}
        script={}
        for file in static_files:
            base,ext=os.path.splitext(file)
            if ext==".css":
                with open(file,"r",encoding="utf-8") as f:
                    style[os.path.basename(base)]=f.read()
            if ext==".js":
                with open(file,"r",encoding="utf-8") as f:
                    script[os.path.basename(base)]=f.read()

        if args["episode"]:
            contents=htmls['single'].render(title=nd.novels[args["episode"]][0],author=nd.info["author"],contents=nd.novels[args["episode"]][1],style=style,script=script,lines=len(nd.novels[args["episode"]][1]),url=args["url"])
        else:
            contents=htmls['single'].render(title=nd.info["title"],author=nd.info["author"],contents=nd.novels[0][1],style=style,script=script,lines=len(nd.novels[0][1]),url=args["url"])
        with open(ndir+args["name"]+".html", "w") as f:
            f.write(contents)
    else:
        # Gen index.html
        contents=htmls['index'].render(title=nd.info["title"],author=nd.info["author"],desc=nd.info["desc"],index=nd.info["index"],total=nd.info["num_parts"],url=nd.indexurl)
        with open(ndir+"index.html","w",encoding="utf-8") as f:
            f.write(contents)

		# Copy statics
        if not os.path.islink(ndir+"static"):
            if os.path.isdir(ndir+"static"):
                shutil.rmtree(ndir+"static")
            elif os.path.isfile(ndir+"static"):
                os.remove(ndir+"static")
            #os.symlink(THEME_DIR+"static",ndir+"static")
            os.mkdir(ndir+"static")
            for file in static_files:
                shutil.copyfile(file,ndir+"static/"+os.path.basename(file))


        with open(ndir+"static/db.json","w") as f:
            json.dump(nd.gen_db(db_data),f, ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))

        for part in nd.novels:
            contents=htmls['base'].render(title=nd.info["title"],author=nd.info["author"],subtitle=nd.novels[part][0],part=part,total=nd.info["num_parts"],contents=nd.novels[part][1],lines=len(nd.novels[part][1]),index=nd.info["index"],epis=nd.info["epis"],url=nd.info["epis"][part]["url"])
            with open(ndir+str(part)+".html", "w", encoding="utf-8") as f:
                f.write(contents)

def command_line():
    parser=argparse.ArgumentParser()
    parser.add_argument('url',help="URL")
    parser.add_argument('-d',"--dir",default="",help="set output directory")
    parser.add_argument('-n',"--name",default="{title}",help="set output directory/file name")
    parser.add_argument('-r',"--renew",action='store_true',help="force to update all files")
    parser.add_argument('-a',"--axel",action='store_true',help="turn on axceleration mode")
    parser.add_argument('-e',"--episode",default="",help="set download single episode as short novel")
    parser.add_argument('-t',"--theme",default="auto",help="set novel's theme")
    parser.add_argument('-m',"--media",default="",help="generate html supporting only one media type")
    parser.add_argument('-q',"--quiet",action='store_false',help="suppress non-messages")
    args=parser.parse_args()
    args=args.__dict__
    output=args.pop("quiet")
    try:
        main(args,bar=output)
    except NovelDLException as e:
        e.console_message()
        sys.exit(-1)
    else:
        if output:
            print("Successfully downloaded")

def args(url="",save_dir="",renew=False,axel=False,episode="",theme="auto",media=""):
    return {"url": url,"dir": save_dir,"renew": renew,"axel": axel,"episode": episode,"theme": theme,"media": media}

if __name__=="__main__":
    command_line()
