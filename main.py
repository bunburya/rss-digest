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

from config import Profile

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
    
    def get_profile(self, name):
        if name in self.get_profiles():
            return Profile(name, self)
        else:
            raise ValueError('No profile {}.'.format(name))
    
    def new_profile(self, name):
        profile = Profile(name, self, is_new=True)
        # TODO:  Also need email, password (hidden), maybe others?
        return profile

class CLInterface:
    """A very simple CLI for adding profiles and feeds."""
    
    def __init__(self, app):
        self.app = app
        
    def add_feed(self, profile=None):
        if profile is None:
            profile = input('Which profile? ').strip()
            if profile not in self.app.get_profiles():
                print('Invalid profile.  Enter existing profile name or create new profile.')
                return
        p = self.app.get_profile(profile)
        save_and_quit = False
        while not save_and_quit:
            title = input('Enter feed title: ')
            url = input('Enter feed URL: ')
            category = input('Enter category (blank for no category): ') or None
            p.add_feed(title, url, posn=-1, save=False, category=category)
            again = input('Add another? (y/N) ')
            if not again.lower().startswith('y'):
                save_and_quit = True
            p.save_data()
            p.save_list()

    def add_profile(self):
        name = input('Enter profile name: ')
        profile = self.app.new_profile(name)
        self.add_feed(profile.name)
    
    def eval_cmd(self):
        print('Commands (none of these take arguments; you will be prompted for input after entering the commands):')
        print('add_profile:  Add a new profile.')
        print('add_feed:  Add a feed to a profile.')
        print('exit:  Exit the app.')
        cmd = input('Enter command: ').lower().split()[0]
        if cmd == 'add_profile':
            self.add_profile()
        elif cmd == 'add_feed':
            self.add_feed()
        elif cmd == 'exit':
            raise SystemExit
        else:
            print('Sorry, command {} not recognised.'.format(cmd))
    
    def repl(self):
        while True:
            self.eval_cmd()
        
if __name__ == '__main__':
    app = RSSDigest()
    cli = CLInterface(app)
    cli.repl()
