#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup
from setuptools import find_packages
import os

root=os.path.abspath(os.path.dirname(__file__))

PACKAGE_NAME="novel_dl"
DESCRIPTION = 'Novel downloader'
with open(os.path.join(root,"README.md"),"r") as f:
	LONG_DESCRIPTION = f.read()

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
	long_description_content_type="text/markdown",
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
		{app}={pkg}.main:command_line
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
