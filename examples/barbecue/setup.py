#!/usr/bin/env python

"""
setup.py script

Data file is included by "MANIFEST.in", see:
http://peak.telecommunity.com/DevCenter/setuptools#including-data-files

See also http://guide.python-distribute.org/creation.html
"""

import os
import glob

from setuptools import setup, find_packages

setup(name='barbecue',
      version='0.1b1',
      author='James C. Stroud',
      author_email='jstroud@mbi.ucla.edu',
      description='Utilities for cooking barbecue.',
      url='http://phyles.bravais.net/barbecue',
      classifiers =[
              'Programming Language :: Python :: 2',
         ],
      install_requires=["distribute", "phyles >= 0.2"],
      license='LICENSE.txt',
      long_description=open('README.rst').read(),
      packages=find_packages(),
      include_package_data=True,
      package_data={'': [os.path.join('*', '*.yml')]},
      scripts=glob.glob(os.path.join('bin', '*')))
