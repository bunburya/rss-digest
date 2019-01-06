#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from os import mkdir, listdir
from os.path import exists, expanduser, join
from shutil import rmtree
from getpass import getpass

from config import GlobalConfig, Profile
from html_generator import HTMLGenerator
from email_handler import EmailHandler

class RSSDigest:
    
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
