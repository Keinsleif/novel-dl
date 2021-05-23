#!/usr/bin/python3
# -*- coding: utf-8 -*-

from setuptools import setup
from setuptools import find_packages
import os

PACKAGE_NAME="novel_dl"
DESCRIPTION = 'Novel downloader'
LONG_DESCRIPTION = "Command-line program to download novels from syosetu.com and kakuyomu.jp"

root=os.path.abspath(os.path.dirname(__file__))

version_path=os.path.join(root,PACKAGE_NAME,"__version__.py")
ns=dict()
with open(version_path,"r") as f:
	eval(compile(f.read(), version_path, 'exec'),dict(),ns)
__version__=ns['__version__']
del ns

require_path=os.path.join(root,"requirements.txt")
with open(require_path,"r") as f:
	REQUIRES=f.read().splitlines()

setup(
	name=PACKAGE_NAME,
	version=__version__,

	description=DESCRIPTION,
	long_description=LONG_DESCRIPTION,
	url="https://github.com/kazuto28/{pkg}".format(pkg=PACKAGE_NAME),
	author="Kondo Kazuto",
	author_email="mountaindull@gmail.com",
	license="MIT",

	packages=[PACKAGE_NAME],
	include_package_data=True,
	zip_safe=False,
	install_requires=REQUIRES,
	entry_points="""
		[console_scripts]
		{app}={pkg}.main:main
	""".format(app=PACKAGE_NAME.replace("_","-"),pkg=PACKAGE_NAME),

	classifiers=[
		"Environment :: Console",
		"License :: OSI Approved :: MIT License",
		"Natural Language :: Japanese",
		"Natural Language :: English",
		"Operating System :: Unix",
		"Programming Language :: Python :: 3 :: Only",
	],
)
