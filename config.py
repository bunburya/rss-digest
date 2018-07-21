#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# config.py

from json import dump, load
from os import mkdir
from os.path import exists, expanduser, join
from time import struct_time
from collections import OrderedDict
from configparser import ConfigParser, ExtendedInterpolation

from feedlist import FeedURLList

class Config:
    
    def __init__(self, profile):
        self.profile = profile
        self.conf_dir = self.profile.conf_dir
        self.config = self.load_config()
    
    def get_conf_parser(self):
        """Create a ConfigParser instance and provide it with default
        (required) values."""
        
        conf_parser = ConfigParser(interpolation=ExtendedInterpolation())
        conf_parser.read_dict(
            {'profile': {
                'user_name': self.profile.name,
                'dir_path': self.profile.profile_dir,
                'date_format': '%A %d %B %Y',
                'time_format': '%H:%M',
                'datetime_format': '${date_format} at ${time_format}'
            }})
        return conf_parser
        
    def load_config(self, conf_file=None):
        if (conf_file is None) or (not conf_file):
            conf_file = join(self.profile.profile_dir, 'rss-digest.ini')
        conf_parser = self.get_conf_parser()
        try:
            with open(conf_file, 'r') as f:
                self.conf_parser.read_file(f)
        except FileNotFoundError:
            # if there is no config file, that's okay, because we've
            # already loaded sane defaults for all required options
            pass
        return conf_parser
    
    def save_config(self, conf_file=None):
        if (conf_file is None) or (not conf_file):
            conf_file = join(self.profile.profile_dir, 'rss-digest.ini')
        with open(self.conf_file, 'w') as f:
            self.config.write(f)
    
    def get(self, key):
        return self.config.get('profile', key, fallback=None)
    

class Profile:
    
    def __init__(self, name, app):
        self.name = name
        self.app = app
        self.conf_dir = self.app.conf_dir
        self.profile_dir = self.get_profile_dir()
        self.config = Config(self)
        self.load_list()
    
    def get_profile_dir(self):
        # Get the directory which contains data specific to this profile
        base_profile_dir = join(self.conf_dir, 'profiles')
        if not exists(base_profile_dir):
            mkdir(base_profile_dir)
        profile_dir = join(base_profile_dir, self.name)
        if not exists(profile_dir):
            mkdir(profile_dir)
        return profile_dir
    
    def _load_json(self, fpath):
        try:
            with open(fpath) as f:
                return load(f)
        except FileNotFoundError:
            return {}
    
    def _save_json(self, data, fpath):
        with open(fpath, 'w') as f:
            dump(data, f)
    
    # email_data is data required to send the email to the user
    
    @property
    def email_file(self):
        return join(self.profile_dir, 'email.json')
    
    def load_email_data(self):
        self.email_data = self._load_json(self.email_file)
    
    def save_email_data(self, data):
        self.email_data = data
        self._save_json(data, self.email_file)
    
    # state is data related to the working of the rss-digest programme
    # itself (as opposed to data relating to feeds, etc)
    
    @property
    def state_file(self):
        return join(self.profile_dir, 'state.json')

    def load_state(self):
        self.state = self._load_json(self.state_file)
        self.new_state = {}
        # If there is no state, assume this is the first run.
        self.first_run = not self.state

    def save_state(self):
        if self.new_state:
            self.state = self.new_state
            self.new_state = {}
        self._save_json(self.state, self.state_file)
    
    # feeddata is data (entries, etc) relating to feeds that have
    # already been downloaded
    
    @property
    def data_file(self):
        return join(self.profile_dir, 'data.json')
    
    def load_data(self):
        self.feeddata = self._load_json(self.data_file)

    def save_data(self, data=None):
        if data is not None:
            self.feeddata = data
        self._save_json(self.feeddata, self.data_file)
    
    @property
    def list_file(self):
        return join(self.profile_dir, 'feeds.opml')
    
    def load_list(self):
        self.feedlist = FeedURLList(self.list_file)
    
    def save_list(self):
        with open(self.list_file, 'w') as f:
            f.writelines('\n'.join(self.feedlist))

    def get_last_updated(self, url=None):
        # If url is None, this returns the last update of the feedlist
        # as a whole (same goes for setter function below)
        
        # NOTE:  We don't currently provide a way to access new_state,
        # because I think when you are checking state you will always
        # want the pre-existing state.
        
        #print(self.state)
        
        updated_dict = self.state.get('last_updated', {})
        if url is None and None not in updated_dict:
            # If we haven't set a specific value for the feedlist as a
            # whole, just return the most recent URL-specific value
            try:
                result = max(updated_dict.values())
            except ValueError:
                result = None
        else:
            result = updated_dict.get(url)
        
        if result is None:
            return result
        else:
            return struct_time(result)
    
    def set_last_updated(self, last_updated, new=True, url=None):
        # if new == True, we save to self.new_state instead of
        # self.state.  new_state is then copied to state when saving.
        # This is to allow us to access the old last_updated value when
        # generating HTML.  True is the default value because I think
        # you will always want to save to the buffer.
        
        if new:
            state = self.new_state
        else:
            state = self.state
        if 'last_updated' not in state:
            state['last_updated'] = {}
        state['last_updated'][url] = last_updated

    def get_conf(self, key):
        return self.config.get(key)
