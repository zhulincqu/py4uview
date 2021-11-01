#! usr/bin/env python

# Required modules
from os import path
from codecs import open # use a consistent encoding 'utf-8'

# setuptools over Distutils
from setuptools import setup

try:
    # pip >= 10
    from pip.internal.req import parse_requirements
except ImportError:
    # pip <= 9.0.3
    from pip.req import parse_requirements

current = path.abspath(path.dirname(__file__)) 

setup(
    
    )
