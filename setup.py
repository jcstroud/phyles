#!/usr/bin/env python

import os

from setuptools import setup, find_packages

import configobj

info = configobj.ConfigObj('PackageInfo.cfg')


setup(name = info['PACKAGE'],
      version = info['RELEASE'],
      author = info['AUTHOR'],
      author_email = info['EMAIL'],
      url = info['URL'],
      description = info['DESCRIPTION'],
      license = info['LICENSE'],
      long_description = open('README.rst').read(),
      packages = [info['PACKAGE']],
      requires = ['distribute', 'pyyaml', 'OrderedDict'],
      # test_suite = info['PACKAGE'] + '.tests.test_suite',
      classifiers = [
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7', ],
      )
