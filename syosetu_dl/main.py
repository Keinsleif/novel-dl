#!/usr/bin/python3

import time,re,sys,os,shutil,argparse,configparser,urllib.parse
from datetime import datetime as dtime
from pytz import timezone
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup as bs4
from jinja2 import Environment, FileSystemLoader

#==DEFINE-variable==
CONFIG_DIR=os.path.abspath(os.path.dirname(__file__))+"/"
THEMES=os.listdir(CONFIG_DIR+"themes/")

#==DEFINE-function==
def raise_error(e,exit=True):
	print(e,file=sys.stderr)
	if exit:
		sys.exit(1)

def get_data(url):
	headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0"}
	cookie={'over18': 'yes'}
	data=requests.get(url=url,headers=headers,cookies=cookie)
	if int(data.status_code/100)==5:
		raise_error("Network Error (5xx)")
	elif int(data.status_code/100)==4:
		raise_error("The novel not found")
	return data.content

def main():
	#==DEFINE-parser.argument==
	parser=argparse.ArgumentParser()
	parser.add_argument('arg',help="default:url")
	parser.add_argument('-d',"--dir",default="",help="set output directory")
	parser.add_argument('-r',"--renew",action='store_true',help="force to update all files")
	parser.add_argument('-a',"--axel",action='store_true',help="turn on axceleration mode")
	parser.add_argument('-e',"--episode",default="",help="set download episode")
	parser.add_argument('-s',"--short",action='store_true',help="generate novel like short story (with -e option)")
	parser.add_argument('-m',"--media",default="",help="generate html only one media type")
	parser.add_argument('-t',"--theme",default="default",help="set novel's theme")
	#parser.add_argument('-o',"--output",default="",help="set download filename (with single novel or -se option)")
	args=parser.parse_args()

	#==CHECK-args==
	if args.short and not args.episode:
		raise_error('The -s,--short argument requires -e,--episode')
	if not args.theme in THEMES:
		raise_error('Invalid theme name')


	#==SETUP-themes==
	THEME_DIR=CONFIG_DIR+"themes/"+args.theme+"/"
	config_ini = configparser.ConfigParser()
	env=Environment(loader=FileSystemLoader(THEME_DIR,encoding='utf8'))
	static_files=[THEME_DIR+"static/"+i for i in os.listdir(THEME_DIR+"static/")]
	if not config_ini.read(THEME_DIR+"config.ini", encoding='utf-8'):
		config_ini={"Main": {}}

	MEDIAS=[""]
	if config_ini['Main'].get('medias'):
		MEDIAS=eval(config_ini['Main'].get('medias'))
	if not args.media in MEDIAS:
		MEDIAS.remove('')
		raise_error('Invalid media type\nAvailable medias in this theme: ('+' '.join(MEDIAS)+')')
	if args.media:
		htmls={"base":"base_"+args.media+".html","index":"index_"+args.media+".html","single":"single_"+args.media+".html"}
	else:
		htmls={"base":"base.html","index":"index.html","single":"single.html"}

	if config_ini['Main'].get('parent'):
		parent_dir=CONFIG_DIR+"themes/"+config_ini['Main'].get('parent')
		penv=Environment(loader=FileSystemLoader(parent_dir,encoding='utf8'))
		for file in htmls:
			if os.path.isfile(THEME_DIR+htmls[file]):
				htmls[file]=env.get_template(htmls[file])
			else:
				htmls[file]=penv.get_template(htmls[file])
		static_files=static_files+[parent_dir+"/static/"+i for i in os.listdir(parent_dir+"/static")]
	else:
		htmls={i:env.get_template(htmls[i]) for i in htmls}


	#==CHECK-url==
	ret=urllib.parse.urlparse(args.arg)
	base_url="https://"+ret.hostname+"/"
	if re.match(r'.*syosetu.com',ret.hostname):
		type="narou"
		ncode=re.match(r'/(n[0-9a-zA-Z]+)',ret.path).group(1)
	elif re.match(r'.*kakuyomu.jp',ret.hostname):
		type="kakuyomu"
		ncode=re.match(r'/works/([0-9]+)',ret.path).group(1)
	else:
		print("That url is not supported")
		sys.exit()
	if args.axel:
		lazy=0
	else:
		lazy=1

	#==GET-index_data==
	if type=="narou":
		info_res = get_data(base_url+ncode)
		top_data = bs4(info_res,"html.parser")
		index_raw=top_data.select_one(".index_box")
		if index_raw:
			raws=index_raw.select(".novel_sublist2")
			num_parts=len(raws)
		else:
			num_parts=1
			if not args.dir:
				ndir=""
		title=top_data.select_one("title").text

	elif type=="kakuyomu":
		info_res = get_data(base_url+"works/"+ncode)
		top_data = bs4(info_res,"html.parser")
		index_raw=top_data.select_one(".widget-toc-items")
		raws=index_raw.select("li.widget-toc-episode")
		num_parts = len(raws)
		title=top_data.select_one("#workTitle").text

	if args.episode:
		if not re.match(r'^\d*$',args.episode):
			raise_error("Incorrect Episode number")
		elif int(args.episode)>num_parts or int(args.episode)<0:
			args.episode=""

	#==GET-dest_data==
	#==PREPARE-dest==
	novels=[]
	if num_parts==1 or args.episode:
		if args.dir:
			ndir=os.path.abspath(args.dir)+"/"
			if not os.path.isdir(ndir):
				os.mkdir(ndir)
		else:
			ndir=""
	else:
		if args.dir:
			ndir=os.path.abspath(args.dir)+"/"
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
	if num_parts==1 or args.short:
		with tqdm(total=1) as pbar:
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

			if type=="narou":
				if args.short:
					data=get_data(base_url+ncode+"/"+args.episode)
					soup=bs4(data,"html.parser")
					body=soup.select_one("#novel_honbun")
					subtitle=soup.select_one(".novel_subtitle").text
				else:
					body=top_data.select_one("#novel_honbun")
				l=[bs4(str(i),"html.parser") for i in body("p")]
				[i.p.unwrap() for i in l]
				body=[str(i) for i in l]

			elif type=="kakuyomu":
				if args.short:
					try:
						url=base_url+raws[int(args.episode)].a['href'].replace("/","",1)
					except IndexError:
						raise_error("Incorrect episode number")
				else:
					url=base_url+raws[0].find('a')['href'].replace("/","",1)
				res = get_data(url=url)
				soup = bs4(res,"html.parser")
				subtitle=soup.select_one(".widget-episodeTitle").text
				body=soup.select_one(".widget-episodeBody")
				l=[bs4(str(i),"html.parser") for i in body("p")]
				[i.p.unwrap() for i in l]
				body=[str(i) for i in l]


			if args.short:
				title=subtitle
			contents=htmls['single'].render(title=title,contents=body,style=style,script=script,lines=len(body))
			with open(ndir+re.sub(r'[\\/:*?"<>|]+','',title+".html").replace(" ",""), "w", encoding="utf-8") as f:
				f.write(contents)
			pbar.update()
		print("total 1 part successfully downloaded")
		sys.exit()

	#==GEN-index_data==
	index=[]
	epis=[]
	eles=bs4(str(index_raw).replace("\n",""),"html.parser").contents[0].contents
	part=1
	c=""
	if type=="narou":
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

	elif type=="kakuyomu":
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

	if not args.episode:
		contents=htmls['index'].render(title=title,desc=desc,index=index,total=num_parts)
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
	if args.episode:
		num_parts=1
	#==GEN-episodes==
	with tqdm(total=num_parts) as pbar:
		pbar.set_description("Downloading ")
		for part in range(1, num_parts+1):
			if args.episode:
				part=int(args.episode)

			if str(part) in novels and not args.renew:
				pbar.set_description("Skipped     ")
				pbar.update()
				continue

			if type=="narou":
				res = get_data(base_url+ncode+"/{:d}/".format(part))
				soup = bs4(res,"html.parser")
				subtitle=soup.select_one(".novel_subtitle").text
				body=soup.select_one("#novel_honbun")

			elif type=="kakuyomu":
				res = get_data(base_url+raws[part-1].find('a')['href'].replace("/","",1))
				soup = bs4(res,"html.parser")
				subtitle=soup.select_one(".widget-episodeTitle").text
				body=soup.select_one(".widget-episodeBody")

			l=[bs4(str(i),"html.parser") for i in body("p")]
			[i.p.unwrap() for i in l]
			body=[str(i) for i in l]

			contents=htmls['base'].render(title=title,subtitle=subtitle,part=part,total=total,contents=body,lines=len(body),index=index,epis=epis)

			with open(ndir+str(part)+".html", "w", encoding="utf-8") as f:
					f.write(contents)
			time.sleep(lazy)
			pbar.update()
	print("total {:d} part successfully downloaded".format(num_parts))

if __name__=="__main__":
	main()
