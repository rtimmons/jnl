#!/usr/bin/env python

from setuptools import setup

setup(
    name='jnl',
    version='0.1',
    description='Captian\'s Logs',
    author='rtimmons',
    author_email='github/rtimmons',
    url='https://github.com/rtimmons/jnl',
    packages=['jnl'],
    scripts=['bin/jnl'],
    entry_points = {
        'console_scripts': ['jnl=jnl.jnl:main'],
    }
 )