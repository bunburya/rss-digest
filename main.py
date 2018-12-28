#!/usr/bin/env python
# -*- coding: utf-8 -*-

# TODO:

# - Develop main.py.  Main functionality:
#   - new profile
#   - add / remove feed from profile
#   - run for profile (with / without email)
# - Interface for creating profiles, editing feeds etc.
# - Categories

import logging
from os import mkdir, listdir
from os.path import exists, expanduser, join
from getpass import getpass

from config import GlobalConfig, Profile

logging.basicConfig(level=logging.INFO)

class RSSDigest:
    """This is the main class, that will be invoked from the command
    line to start everything.  Eventually will take command line
    arguments to specify exactly what action is needed.""" 
    
    def __init__(self):
        self.config = GlobalConfig(self)
        self.profiles_dir = self.get_profiles_dir()
    
    def get_profiles_dir(self):
        profiles_dir = join(self.config.conf_dir, 'profiles')
        if not exists(profiles_dir):
            mkdir(profiles_dir)
        return profiles_dir

    def get_profiles(self):
        return listdir(self.profiles_dir)
    
    def get_profile(self, name):
        if name in self.get_profiles():
            return Profile(self, name)
        else:
            raise ValueError('No profile {}.'.format(name))
    
    def new_profile(self, name, email):
        profile = Profile(self, name, email, is_new=True)
        return profile

class CLInterface:
    """A very simple CLI for adding profiles and feeds."""
    
    def __init__(self, app):
        self.app = app
        if not exists(self.app.config.email_data_file):
            print('No email.json file found.  Add details of how RSS Digest is to send emails.')
            self.set_email_data()
        self.repl()
       
    def force_input(self, prompt=None, msg=None, cmd=input):
        response = False
        while not response:
            response = cmd(prompt)
            if (not response) and msg:
                print(msg)
        return response
       
    def set_email_data(self):
        data = {}
        author = input('Who should emails from RSS Digest appear as coming from '
                        '(default is "RSSDigest")? ') or 'RSSDigest'
        email = self.force_input('Email address from which emails are sent:',
                            'An email address is required. ')
        smtp_server = self.force_input('SMTP server: ',
                            'An SMTP server is required.')
        smtp_port = input('SMTP port (default is 587): ') or 587
        username = input('Email username (default is the email address): ') or email
        password = self.force_input('Email password (this is stored as plaintext): ',
                                'Your password is required.', getpass)
        data = {
            'author': author,
            'email': email,
            'smtp_server': smtp_server,
            'smtp_port': smtp_port,
            'username': username,
            'password': password
            }
        self.app.config.save_email_data(data)
        
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
        name = email = None
        while not (name and email):
            name = input('Enter profile name: ')
            email = input('Enter email address: ')
            print('EMAIL:', email)
            if not (name and email):
                print('You need to enter both a name and an email.')
        profile = self.app.new_profile(name, email)
        print('Profile {} added.  Now add some feeds.'.format(name))
        self.add_feed(profile.name)
    
    def eval_cmd(self):
        print('Commands (none of these take arguments; you will be prompted for input after entering the commands):')
        print('add_profile:  Add a new profile.')
        print('add_feed:  Add a feed to a profile.')
        print('exit:  Exit the app.')
        try:
            cmd = input('Enter command: ').lower().split()[0]
        except IndexError:
            # empty input; do nothing
            return
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
