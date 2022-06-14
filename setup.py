#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup
from setuptools import find_packages
import os

root=os.path.abspath(os.path.dirname(__file__))

PACKAGE_NAME="novel_dl"
info_path=os.path.join(root,PACKAGE_NAME,"info.py")
ns=dict()
with open(info_path,"r") as f:
	eval(compile(f.read(), info_path, 'exec'),dict(),ns)
__version__=ns['__version__']

with open(os.path.join(root,"README.md"),"r") as f:
	LONG_DESCRIPTION = f.read()

require_path=os.path.join(root,"requirements.txt")
with open(require_path,"r") as f:
	REQUIRES=f.read().splitlines()

setup(
	name=PACKAGE_NAME,
	version=__version__,

	description=ns['__description__'],
	long_description=LONG_DESCRIPTION,
	long_description_content_type="text/markdown",
	url="https://github.com/kazuto28/{pkg}".format(pkg=ns['__appname__'].lower()),
	author=ns['__author__'],
	author_email=ns['__contact__'],
	license=ns['__license__'],

	packages=[PACKAGE_NAME],
	include_package_data=True,
	zip_safe=False,
	install_requires=REQUIRES,
	entry_points="""
		[console_scripts]
		{app}={pkg}.main:command_line
	""".format(app=ns['__appname__'].lower(),pkg=PACKAGE_NAME),

	classifiers=[
		"Environment :: Console",
		"License :: OSI Approved :: MIT License",
		"Natural Language :: Japanese",
		"Natural Language :: English",
		"Operating System :: Unix",
		"Programming Language :: Python :: 3 :: Only",
	],
)
