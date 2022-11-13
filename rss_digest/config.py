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

from rss_digest.profile import Profile


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

        # Config file containing default values that will be used for all profiles unless overridden in a
        # profile-specific config file
        self.default_config_file = os.path.join(self.config_dir, 'config.ini')

        # Directory to store profile-specific configuration files
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
        return join(self.config_dir, 'email.json')
    
    def load_email_data(self):
        self.email_data = load_json(self.email_data_file)
    
    def save_email_data(self, data):
        self.email_data = data
        save_json(data, self.email_data_file)
