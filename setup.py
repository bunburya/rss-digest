#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages

with open('README.md') as f:
    long_description = f.read()

scripts = ['rss-digest']

setup(
    name='rss-digest',
    version='1.0',
    packages=find_packages(),
    scripts=scripts,
    install_requires=['reader', 'jinja2', 'appdirs', 'lxml', 'lxml-stubs', 'pytest', 'requests', 'sphinx', 'pytz',],
    package_data={},
    author='bunburya',
    author_email='dev@bunburya.eu',
    description='Generate digests of subscribed RSS and Atom feeds.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords='rss atom digest email feed',
    url='https://github.com/bunburya/rss-digest',
    classifiers=[
        "Programming Language :: Python :: 3",
        'License :: OSI Approved :: MIT License'
    ]
)
