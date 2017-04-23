#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# config.py

from json import dump, load
from os import mkdir
from os.path import exists, expanduser, join

# change later
DEFAULT_CONFIG_FILE = '/home/alan/bin/rss-digest/rss-digest.ini'

class Config:
    
    user_name = 'Alan'
    dir_path = '/home/alan/bin/rss-digest/test'
    date_format = '%A %d %B %Y'
    time_format = '%H:%M'
    datetime_format = '{} at {}'.format(date_format, time_format)
    
    def __init__(self, name):
        self.name = name
        self.conf_dir = self.get_conf_dir()
        self.profile_dir = self.get_profile_dir()
        self.load_list()
    
    def get_conf_dir(self):
        # Get the root config directory in which all the config files
        # are found.  Eventually use XDG to do this properly.
        conf_dir = expanduser('~/.config/rss-digest')
        if not exists(conf_dir):
            mkdir(conf_dir)
        return conf_dir
    
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
            # No state file so probably first run.
            return {}
    
    def _save_json(self, data, fpath):
        with open(fpath, 'w') as f:
            dump(data, f)
    
    @property
    def state_file(self):
        return join(self.profile_dir, 'state.json')

    def load_state(self):
        self.state = self._load_json(self.state_file)
        # If there is no state, assume this is the first run.
        self.first_run = not self.state

    def save_state(self):
        self._save_json(self.state, self.state_file)
    
    @property
    def data_file(self):
        return join(self.profile_dir, 'data.json')
    
    def load_data(self):
        self.feeddata = self._load_json(self.data_file)

    def save_data(self, data):
        self.feeddata = data
        self._save_json(self.feeddata, self.data_file)
    
    @property
    def list_file(self):
        return join(self.profile_dir, 'list.txt')
    
    def load_list(self):
        with open(self.list_file) as f:
            self.feedlist = [line.strip() for line in f]
    
    def save_list(self):
        with open(self.list_file, 'w') as f:
            f.writelines('\n'.join(self.feedlist))

    def get_last_updated(self, url=None):
        # if url is None, this returns the last update of the feedlist
        # as a whole (same goes for setter function below)
        updated_dict = self.state.get('last_updated', {})
        if url is None and None not in updated_dict:
            # If we haven't set a specific value for the feedlist as a
            # whole, just return the most recent URL-specific value
            try:
                return max(updated_dict.values())
            except ValueError:
                return None
        else:
            return updated_dict.get(url)
    
    def set_last_updated(self, last_updated, url=None):
        if 'last_updated' not in self.state:
            self.state['last_updated'] = {}
        self.state['last_updated'][url] = last_updated
