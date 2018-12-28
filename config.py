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
from feedhandler import FeedObjectList

# Few helper functions

def load_json(fpath, empty_type=dict):
    try:
        with open(fpath) as f:
            return load(f)
    except FileNotFoundError:
        return empty_type()
    
def save_json(data, fpath):
    with open(fpath, 'w') as f:
        dump(data, f)

class GlobalConfig:
    
    """A class to control and store global configuration settings."""
    
    def __init__(self, app):
        pass

    @property
    def conf_dir(self):
        # Get the root config directory in which all the config files
        # are found.  Eventually use XDG to do this properly.
        # Also move this to some global function so it's not set up
        # per profile.
        _conf_dir = expanduser('~/.config/rss-digest')
        if not exists(_conf_dir):
            mkdir(_conf_dir)
        return _conf_dir
    
    @property
    def template_dir(self):
        _template_dir = join(self.conf_dir, 'templates')
        if not exists(_template_dir):
            mkdir(_template_dir)
            # TODO: Include code to copy in default template
        return _template_dir
    
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
    # TODO:  Create a separate global configuration class.
    
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
        print(self.profile.name)
        print(self.profile.email)
        print(self.profile.profile_dir)

        conf_parser.read_dict(
            # TODO:  Save this to another file, defaults.json or something
            {'profile': {
                'user_name': self.profile.name,
                'email': '',
                'dir_path': self.profile.profile_dir,
                'date_format': '%A %d %B %Y',
                'time_format': '%H:%M',
                'datetime_format': '${date_format} at ${time_format}',
                'categorised': 'false',
                'template': 'email.html'
            }})
        return conf_parser
    
    def load_config(self, conf_file=None):
        if (conf_file is None) or (not conf_file):
            conf_file = join(self.profile.profile_dir, 'rss-digest.ini')
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
            conf_file = join(self.profile.profile_dir, 'rss-digest.ini')
        with open(conf_file, 'w') as f:
            self.config.write(f)
    
    def get(self, key, val_type=None):
        if val_type == 'bool':
            return self.config.getboolean('profile', key, fallback=None)
        else:
            return self.config.get('profile', key, fallback=None)

class Profile:
    
    def __init__(self, app, name, email=None, is_new=False):
        self.app = app
        self.name = name
        self.email = email
        self.is_new = is_new
        self.conf_dir = self.app.config.conf_dir
        self.config = UserConfig(self)
        if is_new:
            if not email:
                raise TypeError("When setting up a new profile, email is required.")
            self.config.save_config()
        else:
            self.load_list()
    self.feed_handler = FeedHandler(self)
    
    @property
    def profile_dir(self):
        """Get the directory which contains data specific to this profile.
        If that directory doesn't exist, create it."""
        base_profile_dir = join(self.conf_dir, 'profiles')
        if not exists(base_profile_dir):
            mkdir(base_profile_dir)
        _profile_dir = join(base_profile_dir, self.name)
        if not exists(_profile_dir):
            mkdir(_profile_dir)
        return _profile_dir
    
    @property
    def template_dir(self):
        """Get the director which contains templates specific to this
        profile.  If that directory doesn't exist, create it."""
        _template_dir = join(self.profile_dir, 'templates')
        if not exists(_template_dir):
            mkdir(_template_dir)
        return _template_dir
    
    # state is data related to the working of the rss-digest programme
    # itself (as opposed to data relating to feeds, etc)
    
    @property
    def state_file(self):
        return join(self.profile_dir, 'state.json')

    def load_state(self):
        self.state = load_json(self.state_file)
        self.new_state = {}
        # If there is no state, assume this is the first run.
        self.first_run = not self.state

    def save_state(self):
        if self.new_state:
            self.state = self.new_state
            self.new_state = {}
        save_json(self.state, self.state_file)
    
    # feeddata is data (entries, etc) relating to feeds that have
    # already been downloaded
    
    @property
    def data_file(self):
        return join(self.profile_dir, 'data.json')
    
    def load_data(self):
        self.feeddata = load_json(self.data_file, list)

    def save_data(self, data=None):
        if data is not None:
            self.feeddata = data
        save_json(self.feeddata, self.data_file)
    
    @property
    def list_file(self):
        return join(self.profile_dir, 'feeds.opml')
    
    def load_list(self):
        self.feedlist = FeedURLList(self.list_file)
    
    def save_list(self):
        self.feedlist.to_opml(self.list_file)

    def get_last_updated(self, url=None):
        # If url is None, this returns the last update of the feedlist
        # as a whole (same goes for setter function below)
        
        # NOTE:  We don't currently provide a way to access new_state,
        # because I think when you are checking state you will always
        # want the pre-existing state.
        
        #print(self.state)
        
        updated_dict = self.state.get('last_updated', {})
        if (url is None) and (None not in updated_dict):
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
    
    def set_last_updated(self, last_updated, url=None, new=True):
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

    def get_conf(self, key, val_type=None):
        return self.config.get(key, val_type)

    def add_feed(self, title, url, posn=-1, save=True, *args, **kwargs):
        self.load_list()
        self.load_data()
        self.feedlist.insert_feed(posn, title, 'rss', url,
            # Can't serialise None, so remove None args
            *filter(lambda a: a is not None, args),
            **{k: v for k, v in kwargs.items() if v is not None})
        self.feeddata.insert(posn, {})
        if save:
            self.save_data()
            self.save_list()
