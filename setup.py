#!/usr/bin/env python

from setuptools import setup

# TODO: follow some examples here?
# https://github.com/garywiz/chaperone/blob/master/setup.py

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