#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import os
import shutil
from json import dump, load
from typing import Optional
from importlib_resources import files

import appdirs

from rss_digest.exceptions import BadInstallationError

logger = logging.getLogger(__name__)

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

    def __init__(self, config_dir: Optional[str] = None, data_dir: Optional[str] = None, copy_config: bool = False):

        # General config directory
        self.config_dir = config_dir or appdirs.user_config_dir('rss-digest')
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

        # Config file containing default values that will be used for all profiles unless overridden in a
        # profile-specific config file
        self.default_config_file = os.path.join(self.config_dir, 'config.toml')

        # Directory to store profile-specific configuration files
        self.profile_config_dir = os.path.join(self.config_dir, 'profiles')
        if not os.path.exists(self.profile_config_dir):
            os.makedirs(self.profile_config_dir)

        # Directory to store profile-specific output templates
        self.templates_dir = os.path.join(self.config_dir, 'templates')
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)

        # General directory for storing application data/state
        self.data_dir = data_dir or appdirs.user_data_dir('rss-digest')
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        # Directory to store profile-specific state
        self.profile_data_dir = os.path.join(self.data_dir, 'profiles')
        if not os.path.exists(self.profile_data_dir):
            os.makedirs(self.profile_data_dir)

        self.dirs = (self.config_dir, self.profile_config_dir, self.templates_dir, self.data_dir, self.profile_data_dir)

        self.mkdirs()

        if copy_config:
            self.copy_installed_configs()

    # email_data is data required to *send* the email to the user
    # (as distinct from the recipient email address, which will be
    # specified in the relevant profile config ini file).
    
    def mkdirs(self):
        for d in self.dirs:
            if not os.path.exists(d):
                os.makedirs(d)

    def rmdirs(self):
        for d in self.dirs:
            if os.path.exists:
                shutil.rmtree(d)

    def copy_installed_configs(self):
        logger.info('Copying installed configuration files.')
        install_site = files('rss_digest.data')
        logger.info(f'Looking in {install_site}')
        conf_fpath = install_site.joinpath('config.toml')
        template_dir = install_site.joinpath('templates')
        try:
            shutil.copy(conf_fpath, self.config_dir)
            for t in os.listdir(template_dir):
                shutil.copy(os.path.join(template_dir, t), self.templates_dir)
        except FileNotFoundError:
            raise BadInstallationError(f'Could not find installed configuration files.')
