#!/usr/bin/env python
# -*- coding: utf-8 -*-

# TODO:

# - Develop main.py.  Main functionality:
#   - new profile
#   - add / remove feed from profile
#   - run for profile (with / without email)
# - Interface for creating profiles, editing feeds etc.
# - Categories

from os import mkdir, listdir
from os.path import exists, expanduser, join

class RSSDigest:
    """This is the main class, that will be invoked from the command
    line to start everything.  Eventually will take command line
    arguments to specify exactly what action is needed.""" 
    
    def __init__(self):
        self.conf_dir = self.get_conf_dir()
        self.profiles_dir = self.get_profiles_dir()
    
    def get_conf_dir(self):
        # Get the root config directory in which all the config files
        # are found.  Eventually use XDG to do this properly.
        # Also move this to some global function so it's not set up
        # per profile.
        conf_dir = expanduser('~/.config/rss-digest')
        if not exists(conf_dir):
            mkdir(conf_dir)
        return conf_dir
    
    def get_profiles_dir(self):
        profiles_dir = join(self.conf_dir, 'profiles')
        if not exists(profiles_dir):
            mkdir(profiles_dir)
        return profiles_dir

    def get_profiles(self):
        return listdir(self.profiles_dir)

    def new_profile(self, name):
        profile = Profile(name, self, is_new=True)

class CLInterface:
    """A very simple CLI for adding profiles and feeds."""
    
    def __init__(self, app):
        self.app = app
        
    def add_feed(self, profile=None):
        if profile is None:
            profile = input('Which profile?').strip()
            if profile not in self.app.get_profiles():
                print('Invalid profile.  Enter existing profile name or create new profile.')
                return
        p = self.app.get_profile(profile)
        save_and_quit = False
        while not save_and_quit:
            title = input('Enter feed title:')
            url = input('Enter feed URL:')
            category = input('Enter category (blank for no category):') or None
            p.add_feed(title, url, posn=-1, save=False, category=category)
            again = input('Add another? (y/N)')
            if not again.lower().startswith('y'):
                save_and_quit = True
            p.save_data()
            p.save_list()
