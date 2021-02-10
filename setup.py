import os
import platform
import re
import sys
import warnings

# Don't force people to install setuptools unless
# we have to.
try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools

    use_setuptools()
    from setuptools import setup

from distutils.cmd import Command
from distutils.command.build_ext import build_ext
from distutils.errors import CCompilerError, DistutilsOptionError
from distutils.errors import DistutilsPlatformError, DistutilsExecError
from distutils.core import Extension

version = "0.0.0"

f = open("README.md")
try:
    try:
        readme_content = f.read()
    except:
        readme_content = ""
finally:
    f.close()

setup(
    name="jnl",
    version=version,
    description="Captain's Logs",
    long_description=readme_content,
    author="Ryan Timmons",
    author_email="ryan <at> rytim.com",
    maintainer="Ryan Timmons",
    maintainer_email="ryan <at> rytim.com",
    url="http://github.com/rtimmons/jnl",
    keywords=[],
    install_requires=[],
    license="Apache License, Version 2.0",
    python_requires=">=3.5",
    classifiers=[],
    packages=["jnl"],
    zip_safe=True,
    entry_points={"console_scripts": ["jnl = jnl.cli:main"]},
)
