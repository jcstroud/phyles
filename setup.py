#!/usr/bin/env python

import os

from setuptools import setup, find_packages

import configobj

info = configobj.ConfigObj('PackageInfo.cfg')


setup(name = info['PACKAGE'],
      version = "%(MAJOR)s.%(MINOR)s.%(MICRO)s%(TAG)s" % info,
      author = info['AUTHOR'],
      author_email = info['EMAIL'],
      url = info['URL'],
      description = info['DESCRIPTION'],
      license = info['LICENSE'],
      long_description = open('README.rst').read(),
      packages = find_packages(),
      package_data = {'':[os.path.join('*', '*.yml'),
                          os.path.join('*', '*.zip')]},
      include_package_data=True,
      install_requires = ['distribute', 'pyyaml',
                          'OrderedDict', 'configobj'],
      # test_suite = info['PACKAGE'] + '.tests.test_suite',
      classifiers = [
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7', ],
      entry_points = {
        'console_scripts' : [
            'phyles-pack-skeleton = phyles._phyles:_pack_skeleton',
            'phyles-quickstart = phyles._phyles:_quickstart']}
      )
