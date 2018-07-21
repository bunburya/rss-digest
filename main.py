#!/usr/bin/env python
# -*- coding: utf-8 -*-

# TODO:

# - Develop main.py.  Main functionality:
#   - new profile
#   - add / remove feed from profile
#   - run for profile (with / without email)
# - Interface for creating profiles, editing feeds etc.

from os import mkdir
from os.path import exists, expanduser, join

class RSSDigest:
    """This is the main class, that will be invoked from the command
    line to start everything.  Eventually will take command line
    arguments to specify exactly what action is needed.""" 
    
    def __init__(self):
        self.conf_dir = self.get_conf_dir()
    
    def get_conf_dir(self):
        # Get the root config directory in which all the config files
        # are found.  Eventually use XDG to do this properly.
        # Also move this to some global function so it's not set up
        # per profile.
        conf_dir = expanduser('~/.config/rss-digest')
        if not exists(conf_dir):
            mkdir(conf_dir)
        return conf_dir
