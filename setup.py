#! /usr/bin/env python

from distutils.core import setup
try:
	import py2exe
	extrakws = dict(console=["bin/ncfv"])
except ImportError:
	extrakws = {}

setup(name="ncfv",
	package_dir = {'': 'lib'},
	packages = ['ncfv'],
	scripts = ['bin/ncfv'],
	data_files = [("man/man1", ["ncfv.1"])],
	options={"py2exe": {"packages": ["encodings"]}},
	version="0.1",
	author="Léon van der Kaap",
	license="GPL v2 or higher",
	url="https://github.com/Daimanta/ncfv.git",
	**extrakws
)
