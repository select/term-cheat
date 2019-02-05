#!/usr/bin/env python

from distutils.core import setup

setup(name='TermCheat',
      version='0.1.4',
      description='Collect and find termial commands.',
      author='@select@github.com',
      author_email='falko@webpgr.com',
      url='https://github.com/select/term-cheat',
      packages=['termcheat'],
      package_data={'termcheat': ['*.yaml']},
      # entry_points={
      #     'console_scripts': ['term-cheat-app = termcheat.lib:run']
      # },
      # scripts=["bin/term-cheat-app"],
      install_requires=['urwid', 'fuzzywuzzy', 'pyyaml', 'appdirs', 'python-Levenshtein']
      )
