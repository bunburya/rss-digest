#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# config.py
import os
from json import dump, load
from os import mkdir
from os.path import exists, expanduser, join
from configparser import ConfigParser, ExtendedInterpolation
from typing import Optional

import appdirs

# Few helper functions

def load_json(fpath, empty_type=dict):
    try:
        with open(fpath) as f:
            return load(f)
    except FileNotFoundError:
        return empty_type()
    
def save_json(data, fpath):
    with open(fpath, 'w') as f:
        dump(data, f, indent=4)

class Config:
    
    """A class to control and store global configuration settings."""

    def __init__(self, config_dir: Optional[str] = None, data_dir: Optional[str] = None):

        # General config directory
        self.config_dir = config_dir or appdirs.user_config_dir('rss-digest')
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

        # Directory to store each profile-specific configuration files
        self.profile_config_dir = os.path.join(self.config_dir, 'profiles')
        if not os.path.exists(self.profile_config_dir):
            os.makedirs(self.profile_config_dir)

        # Directory to store profile-specific output templates
        self.templates_dir = os.path.join(self.config_dir, 'templates')
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)

        # Database of existing profiles
        self.profiles_db = os.path.join(self.config_dir, 'profiles.db')

        # General directory for storing application data/state
        self.data_dir = data_dir or appdirs.user_data_dir('rss-digest')
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        # Directory to store profile-specific state
        self.profile_data_dir = os.path.join(self.data_dir, 'profiles')
        if not os.path.exists(self.profile_data_dir):
            os.makedirs(self.profile_data_dir)



    # email_data is data required to *send* the email to the user
    # (as distinct from the recipient email address, which will be
    # specified in the relevant profile config ini file).
    
    @property
    def email_data_file(self):
        return join(self.conf_dir, 'email.json')
    
    def load_email_data(self):
        self.email_data = load_json(self.email_data_file)
    
    def save_email_data(self, data):
        self.email_data = data
        save_json(data, self.email_data_file)

class UserConfig:

    """A class to control and store user-specific configuration settings."""

    def __init__(self, profile):
        self.profile = profile
        self.conf_dir = self.profile.conf_dir
        if profile.is_new:
            self.config = self.get_config()
            self.config['profile']['email'] = self.profile.email
        else:
            self.config = self.load_config()
    
    def get_config(self):
        """Create a ConfigParser instance and provide it with default
        (required) values.
        
        NOTE:  We specify `email` as none (empty string).  For normal
        usage, this will need to be overwritten with an email address.
        We could, however, allow for some fallback action when no email
        address is present, such as outputting the HTML content to
        stdout."""
        
        conf_parser = ConfigParser(interpolation=ExtendedInterpolation())

        conf_parser.read_dict(
            # TODO:  Save this to another file, defaults.json or something
            {'profile': {
                'user_name': self.profile.name,
                'email': '',
                'dir_path': self.profile.config_dir,
                'date_format': '%A %d %B %Y',
                'time_format': '%H:%M',
                'datetime_format': '${date_format} at ${time_format}',
                'use_categories': 'false',
                'template': 'email.html'
            }})
        return conf_parser
    
    def load_config(self, conf_file=None):
        if (conf_file is None) or (not conf_file):
            conf_file = join(self.profile.config_dir, 'rss-digest.ini')
        config = self.get_config()
        try:
            with open(conf_file, 'r') as f:
                config.read_file(f)
        except FileNotFoundError:
            # if there is no config file, that's okay, because we've
            # already loaded sane defaults for all required options
            pass
        return config
    
    def save_config(self, conf_file=None):
        if (conf_file is None) or (not conf_file):
            conf_file = join(self.profile.config_dir, 'rss-digest.ini')
        with open(conf_file, 'w') as f:
            self.config.write(f)
    
    def get(self, key, val_type=None):
        if val_type == 'bool':
            return self.config.getboolean('profile', key, fallback=None)
        else:
            return self.config.get('profile', key, fallback=None)

