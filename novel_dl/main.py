#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time,re,sys,os,shutil,argparse,configparser,urllib.parse
from datetime import datetime as dtime
from pytz import timezone
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup as bs4
from jinja2 import Environment, FileSystemLoader

#==DEFINE-variable==
CONFIG_DIR=os.path.abspath(os.path.dirname(__file__))+"/"
THEMES=os.listdir(CONFIG_DIR+"themes/")+["auto"]


class NovelDLException(Exception):
	def console_message(self):
		print("novel-dl: ",end="",file=sys.stderr)
		print(*self.args,file=sys.stderr)

def raise_error(e,exit=True):
	raise NovelDLException(e)

def get_data(url):
	headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0"}
	cookie={'over18': 'yes'}
	data=requests.get(url=url,headers=headers,cookies=cookie)
	if int(data.status_code/100)==5:
		raise_error("network error (5xx)")
	elif int(data.status_code/100)==4:
		raise_error("novel not found")
	return data.content


def main(args,bar=False):
	if bar:
		bar_output=None
	else:
		bar_output=open(os.devnull,"w")

	#==CHECK-args==
	if args["short"] and not args["episode"]:
		raise_error("invalid option -- 's'\nThe -s,--short argument requires -e,--episode")
	if not args["theme"] in THEMES:
		raise_error('invalid theme name `'+args["theme"]+'`')

	#==CHECK-url==
	ret=urllib.parse.urlparse(args["url"])
	if not ret.hostname:
		raise_error("invalid argument 'url'")
	base_url="https://"+ret.hostname+"/"
	if re.match(r'.*syosetu.com',ret.hostname):
		site="narou"
		ncode=re.match(r'/(n[0-9a-zA-Z]+)',ret.path).group(1)
	elif re.match(r'.*kakuyomu.jp',ret.hostname):
		site="kakuyomu"
		ncode=re.match(r'/works/([0-9]+)',ret.path).group(1)
	else:
		raise_error("url is not supported")
	if args["axel"]:
		delay=0
	else:
		delay=1

	#==SETUP-themes==
	if args["theme"]=="auto":
		if site=="narou":
			args["theme"]="narou"
		elif site=="kakuyomu":
			args["theme"]="kakuyomu"
	THEME_DIR=CONFIG_DIR+"themes/"+args["theme"]+"/"
	config_ini = configparser.ConfigParser()
	static_files=[THEME_DIR+"static/"+i for i in os.listdir(THEME_DIR+"static/")]
	if not config_ini.read(THEME_DIR+"config.ini", encoding='utf-8') and not 'Main' in config_ini.sections():
		config_ini={"Main": {}}
	conf=dict(config_ini.items("Main"))
	MEDIAS=[""]
	if conf.get('medias'):
		MEDIAS=eval(conf['medias'])
	if not args["media"] in MEDIAS:
		MEDIAS.remove('')
		raise_error('invalid media type\nAvailable medias in this theme: ('+' '.join(MEDIAS)+')')
	if args["media"]:
		htmls={"base":"base_"+args["media"]+".html","index":"index_"+args["media"]+".html","single":"single_"+args["media"]+".html"}
	else:
		htmls={"base":"base.html","index":"index.html","single":"single.html"}

	env=Environment(loader=FileSystemLoader(THEME_DIR,encoding='utf8'))
	if conf.get('parent'):
		parent_dir=CONFIG_DIR+"themes/"+conf['parent']
		penv=Environment(loader=FileSystemLoader(parent_dir,encoding='utf8'))
		for file in htmls:
			if os.path.isfile(THEME_DIR+htmls[file]):
				htmls[file]=env.get_template(htmls[file])
			elif os.path.isfile(parent_dir+htmls[file]):
				htmls[file]=penv.get_template(htmls[file])
			else:
				raise_error("cannot load theme file: "+htmls[file])
		static_files=static_files+[parent_dir+"/static/"+i for i in os.listdir(parent_dir+"/static")]
	else:
		htmls={i:env.get_template(htmls[i]) for i in htmls}

	#==GET-index_data==
	if site=="narou":
		index_url=base_url+ncode
		info_res = get_data(index_url)
		top_data = bs4(info_res,"html.parser")
		index_raw=top_data.select_one(".index_box")
		if index_raw:
			raws=index_raw.select(".novel_sublist2")
			num_parts=len(raws)
		else:
			num_parts=1
			if not args["dir"]:
				ndir=""
		title=top_data.select_one("title").text

	elif site=="kakuyomu":
		index_url=base_url+"works/"+ncode
		info_res = get_data(index_url)
		top_data = bs4(info_res,"html.parser")
		index_raw=top_data.select_one(".widget-toc-items")
		raws=index_raw.select("li.widget-toc-episode")
		num_parts = len(raws)
		title=top_data.select_one("#workTitle").text

	if args["episode"]:
		if not re.match(r'^\d*$',args["episode"]):
			raise_error("incorrect episode number `"+args["episode"]+"`")
		elif int(args["episode"])>num_parts or int(args["episode"])<0:
			args["episode"]=""

	#==GET-dest_data==
	#==PREPARE-dest==
	novels=[]
	if num_parts==1 or args["episode"]:
		if args["dir"]:
			ndir=os.path.abspath(args["dir"])+"/"
			if not os.path.isdir(ndir):
				os.mkdir(ndir)
		else:
			ndir=""
	else:
		if args["dir"]:
			ndir=os.path.abspath(args["dir"])+"/"
			if not os.path.isdir(ndir):
				os.mkdir(ndir)
			else:
				files=os.listdir(ndir)
				for file in files:
					base,ext=os.path.splitext(file)
					if ext=='.html':
						novels.append(base)
		else:
			ndir=os.getcwd()+"/"+ncode+"/"
			if not os.path.isdir(ndir):
				os.mkdir(ndir)
			else:
				files=os.listdir(ndir)
				for file in files:
					base,ext=os.path.splitext(file)
					if ext=='.html':
						novels.append(base)

	#==PROCESS-GEN-single_html==
	if num_parts==1 or args["short"]:
		with tqdm(total=1,file=bar_output) as pbar:
			pbar.set_description("Downloading ")
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

			if site=="narou":
				if args["short"]:
					url=base_url+ncode+"/"+args["episode"]
					data=get_data(url)
					soup=bs4(data,"html.parser")
					body=soup.select_one("#novel_honbun")
					subtitle=soup.select_one(".novel_subtitle").text
				else:
					url=index_url
					body=top_data.select_one("#novel_honbun")
				l=[bs4(str(i),"html.parser") for i in body("p")]
				[i.p.unwrap() for i in l]
				body=[str(i) for i in l]

			elif site=="kakuyomu":
				if args["short"]:
					try:
						url=base_url+raws[int(args["episode"])].a['href'].replace("/","",1)
					except IndexError:
						raise_error("incorrect episode number `"+args["episode"]+"`")
				else:
					url=base_url+raws[0].find('a')['href'].replace("/","",1)
				res = get_data(url=url)
				soup = bs4(res,"html.parser")
				subtitle=soup.select_one(".widget-episodeTitle").text
				body=soup.select_one(".widget-episodeBody")
				l=[bs4(str(i),"html.parser") for i in body("p")]
				[i.p.unwrap() for i in l]
				body=[str(i) for i in l]

			if args["short"]:
				title=subtitle
			contents=htmls['single'].render(title=title,contents=body,style=style,script=script,lines=len(body),site=site,url=url)
			with open(ndir+re.sub(r'[\\/:*?"<>|]+','',title+".html").replace(" ",""), "w", encoding="utf-8") as f:
				f.write(contents)
			pbar.update()
		if bar:
			print("total 1 part successfully downloaded")
		return
	#==GEN-index_data==
	index=[]
	epis=[]
	eles=bs4(str(index_raw).replace("\n",""),"html.parser").contents[0].contents
	part=1
	c=""
	if site=="narou":
		for ele in eles:
			if re.match(r'.+chapter_title',str(ele)):
				index.append({'type': 1,'text': ele.text})
				c=ele.text
			elif re.match(r'.+novel_sublist2',str(ele)):
				timestamp=dtime.strptime(ele.dt.text.replace("（改）",""),"%Y/%m/%d %H:%M")
				index.append({'type': 2,'text': ele.a.text,'part': part,'time': timestamp})
				epis.append({'title':ele.a.text,'chap':c})
				part=part+1
		desc="".join([str(i) for i in top_data.select_one("#novel_ex").contents])

	elif site=="kakuyomu":
		for ele in eles:
			if re.match(r'.+widget-toc-chapter',str(ele)):
				index.append({'type': 1,'text': ele.text})
				c=ele.text
			elif re.match(r'.+widget-toc-episode',str(ele)):
				timestamp=dtime.strptime(ele.a.time.get('datetime'),"%Y-%m-%dT%H:%M:%SZ").astimezone(timezone('Asia/Tokyo'))
				index.append({'type': 2,'text': ele.span.text, 'part': part, 'time': timestamp})
				epis.append({'title':ele.span.text,'chap':c})
				part=part+1
		desc=top_data.select_one("#introduction")
		if desc.select_one(".ui-truncateTextButton-expandButton"):
			desc.select_one(".ui-truncateTextButton-expandButton").decompose()
			desc.span.unwrap()
		desc="".join([str(i) for i in desc.contents])

	if not args["episode"]:
		contents=htmls['index'].render(title=title,desc=desc,index=index,total=num_parts,site=site,url=index_url)
		with open(ndir+"index.html","w",encoding="utf-8") as f:
				f.write(contents)

		#==COPY-statics==
		if not os.path.islink(ndir+"static"):
			if os.path.isdir(ndir+"static"):
				shutil.rmtree(ndir+"static")
			elif os.path.isfile(ndir+"static"):
				os.remove(ndir+"static")
			#os.symlink(THEME_DIR+"static",ndir+"static")
			os.mkdir(ndir+"static")
			for file in static_files:
				shutil.copyfile(file,ndir+"static/"+os.path.basename(file))


	total=num_parts
	if args["episode"]:
		num_parts=1
	#==GEN-episodes==
	with tqdm(total=num_parts,file=bar_output) as pbar:
		pbar.set_description("Downloading ")
		for part in range(1, num_parts+1):
			if args["episode"]:
				part=int(args["episode"])

			if str(part) in novels and not args["renew"]:
				pbar.set_description("Skipped     ")
				pbar.update()
				continue

			if site=="narou":
				url=base_url+ncode+"/{:d}/".format(part)
				res = get_data(url)
				soup = bs4(res,"html.parser")
				subtitle=soup.select_one(".novel_subtitle").text
				body=soup.select_one("#novel_honbun")

			elif site=="kakuyomu":
				url=base_url+raws[part-1].find('a')['href'].replace("/","",1)
				res = get_data(url)
				soup = bs4(res,"html.parser")
				subtitle=soup.select_one(".widget-episodeTitle").text
				body=soup.select_one(".widget-episodeBody")

			l=[bs4(str(i),"html.parser") for i in body("p")]
			[i.p.unwrap() for i in l]
			body=[str(i) for i in l]

			contents=htmls['base'].render(title=title,subtitle=subtitle,part=part,total=total,contents=body,lines=len(body),index=index,epis=epis,site=site,url=url)

			with open(ndir+str(part)+".html", "w", encoding="utf-8") as f:
					f.write(contents)
			time.sleep(delay)
			pbar.update()
	if bar:
		print("total {:d} part successfully downloaded".format(num_parts))


def command_line():
	parser=argparse.ArgumentParser()
	parser.add_argument('url',help="URL")
	parser.add_argument('-d',"--dir",default="",help="set output directory")
	parser.add_argument('-r',"--renew",action='store_true',help="force to update all files")
	parser.add_argument('-a',"--axel",action='store_true',help="turn on axceleration mode")
	parser.add_argument('-e',"--episode",default="",help="set download episode")
	parser.add_argument('-s',"--short",action='store_true',help="generate novel like short story (with -e option)")
	parser.add_argument('-t',"--theme",default="auto",help="set novel's theme")
	parser.add_argument('-m',"--media",default="",help="generate html only one media type")
	parser.add_argument('-q',"--quiet",action='store_false',help="suppress non-messages")
	args=parser.parse_args()
	args=args.__dict__
	bar=args.pop("quiet")
	try:
		main(args,bar=bar)
	except NovelDLException as e:
		e.console_message()

def args(url="",save_dir="",renew=False,axel=False,episode="",short=False,theme="auto",media=""):
	return {"url": url,"dir": save_dir,"renew": renew,"axel": axel,"episode": episode,"short": short,"theme": theme,"media": media}

if __name__=="__main__":
	command_line()
