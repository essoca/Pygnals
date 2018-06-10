# -*- coding: utf-8 -*-
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
          'description': 'Capturing the signals of financial markets',
          'author': 'Edgardo Solano-Carrillo',
          'url': 'URL to get it at.',
          'download_url': 'Where to download it.',
          'author_email': 'essolanoc@gmail.com',
          'version': '0.1',
          'install_requires': ['nose'],
          'packages': ['NAME'],
          'scripts': [],
          'name': 'Pygnals'
          }

setup(**config)

