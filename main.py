#!/usr/bin/env python
# -*- coding: utf-8 -*-

# TODO:

# - Develop main.py.  Main functionality:
#   - add / remove feed from profile
#   - run for profile (with / without email)
# - Interface for creating profiles, editing feeds etc.
# - Categories

import logging
from os import mkdir, listdir
from os.path import exists, expanduser, join
from shutil import rmtree
from getpass import getpass

from config import GlobalConfig, Profile
from html_generator import HTMLGenerator
from email_handler import EmailHandler

logging.basicConfig(level=logging.DEBUG)

class RSSDigest:
    """This is the main class, that will be invoked from the command
    line to start everything.  Eventually will take command line
    arguments to specify exactly what action is needed.""" 
    
    def __init__(self):
        self.config = GlobalConfig(self)
        self.html_generator = HTMLGenerator(self)
        self.email_handler = EmailHandler(self)
    
    @property
    def profiles_dir(self):
        profiles_dir = join(self.config.conf_dir, 'profiles')
        if not exists(profiles_dir):
            mkdir(profiles_dir)
        return profiles_dir

    @property
    def profiles(self):
        return listdir(self.profiles_dir)
    
    def get_profile(self, name):
        if name in self.profiles:
            return Profile(self, name)
        else:
            raise ValueError('No profile {}.'.format(name))
    
    def new_profile(self, name, email):
        profile = Profile(self, name, email, is_new=True)
        return profile
       
    def del_profile(self, name):
        rmtree(join(self.profiles_dir, name), ignore_errors=True)
    
    def email_profile(self, profile):
        """Sends an RSS Digest email for the given profile."""
        # Running order:
        # - fetch new feeds
        # - filter new feeds using old feeds (loaded from file)
        # - save filtered feeds to file
        # - generate html from filtered feeds
        # - send email
        html = self.get_output_for_profile(profile)
        self.email_handler.send_email(profile, html)
        profile.update_last_updated()
        profile.feed_handler.save()
    
    def get_output_for_profile(self, profile, save=False):
        """Fetch new entries for a profile and return the related output
        (the rendered template).
        
        Only save state and data if save=True (I expect this generally
        won't be appropriate because we only want to save when we
        successfully deliver the HTML to the user."""
        
        profile.feed_handler.update_feeds()
        html = self.html_generator.generate_html(profile)
        if save:
            profile.update_last_updated()
            profile.feed_handler.save()
        return html
    
    def email_profile_name(self, name):
        self.email_profile(self.get_profile(name))
        

class CLInterface:
    """A very simple CLI for adding profiles and feeds."""
    
    def __init__(self, app):
        self.app = app
        print('Welcome to RSS Digest.')
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
            if profile not in self.app.profiles:
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
    
    def remove_profile(self):
        name = self.force_input('Enter name of profile to remove: ',
                                'You need to enter a profile name.')
        try:
            self.app.del_profile(name)
            print('Removed profile {}.'.format(name))
        except FileNotFoundError:
            print('No profile {} to delete.'.format(name))

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
    
    def email_profile(self):
        name = self.force_input('Enter profile name: ',
                                'You need to enter a profile name.')
        try:
            self.app.email_profile_name(name)
            print('Email sent for profile {}.'.format(name))
        except ValueError:
            print('Profile {} not found.'.format(name))
    
    def print_profile_output_to_file(self):
        # Print output to a specific file - the default is just for
        # testing purposes.  Later, remove this or set a sensible default.
        default_outfile = 'output.html'
        name = self.force_input('Enter profile name: ',
                                'You need to enter a profile name.')
        outfile = input('Enter output file (default is $PWD/outfile.html):') or default_outfile
        profile = self.app.get_profile(name)
        html = self.app.get_output_for_profile(profile)
        with open(outfile, 'w') as f:
            f.write(html)
        logging.info('Output for profile %s written to file %s.', name,
                        outfile)
        profile.update_last_updated()
        profile.feed_handler.save()
    
    def test_email(self):
        name = self.force_input('Enter profile name: ',
                                'You need to enter a profile name.')
        profile = self.app.get_profile(name)
        self.app.email_handler.test_email(profile)
    
    def print_cmds(self):
        print('Commands (none of these take arguments; you will be prompted for input after entering the commands):')
        print('add_profile:  Add a new profile.')
        print('add_feed:  Add a feed to a profile.')
        print('del_profile:  Delete a profile.')
        print('email_profile:  Send an RSS digest email for a specific profile.')
        print('test_email:  Send a test email to a specific profile.')
        print('print_file:  Print the output for a specific profile to a file.')
        print('exit:  Exit the app.')
        
    def eval_cmd(self):        
        try:
            cmd = input('Enter command: ').lower().split()[0]
        except IndexError:
            # empty input; do nothing
            return
        if cmd == 'add_profile':
            self.add_profile()
        elif cmd == 'add_feed':
            self.add_feed()
        elif cmd == 'del_profile':
            self.remove_profile()
        elif cmd == 'email_profile':
            self.email_profile()
        elif cmd == 'test_email':
            self.test_email()
        elif cmd == 'print_file':
            self.print_profile_output_to_file()
        elif cmd == 'exit':
            raise SystemExit
        else:
            print('Sorry, command {} not recognised.'.format(cmd))
    
    def repl(self):
        self.print_cmds()
        while True:
            self.eval_cmd()
        
if __name__ == '__main__':
    app = RSSDigest()
    cli = CLInterface(app)
