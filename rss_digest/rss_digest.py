#!/usr/bin/env python
# -*- coding: utf-8 -*-
import shutil
from os import mkdir, listdir
from os.path import exists, join
from shutil import rmtree
from typing import List, Optional

from rss_digest.config import Config
from rss_digest.dao import ProfilesDAO
from rss_digest.feedlist import FeedList, get_profile_feedlist
from rss_digest.profile import Profile
from rss_digest.html_generator import HTMLGenerator
from rss_digest.email_senders import BasicEmailSender


class RSSDigest:
    
    def __init__(self, config: Config, profiles_dao: Optional[ProfilesDAO] = None):
        self.config = config
        self.html_generator = HTMLGenerator(self)
        self.email_sender = BasicEmailSender(config)
        self.profiles_dao = profiles_dao or ProfilesDAO(config.profiles_db)

    @property
    def profiles(self) -> List[str]:
        return self.profiles_dao.list_profiles()
    
    def add_profile(self, profile_name: str, email: str, user_name: Optional[str] = None):
        profile = Profile(self.config, profile_name, email, user_name, self.profiles_dao)
        profile.save()

    def edit_profile(self, profile_name: str, email: Optional[str] = None, user_name: Optional[str] = None):
        profile = self.get_profile(profile_name)
        if email:
            profile.email = email
        if user_name:
            profile.user_name = user_name
        profile.save()

    def delete_profile(self, profile_name: str):
        profile = self.get_profile(profile_name)
        profile.rmdirs()
        self.profiles_dao.delete_profile(profile_name)

    def add_feed(self, profile_name: str, feed_name: str, feed_url: str, category: str = None):
        #TODO
        pass

    def get_profile(self, profile_name: str) -> Profile:
        return self.profiles_dao.load_profile(profile_name)

    def get_feedlist(self, profile: Profile) -> FeedList:
        return get_profile_feedlist(profile)

    ### LEGACY CODE FOLLOWS

    def new_profile(self, name, email):
        profile = Profile(self, name, email)
        return profile
       
    def del_profile(self, name):
        rmtree(join(self.profiles_dir, name), ignore_errors=True)
    
    def email_profile(self, profile, update=True):
        """Sends an RSS Digest email for the given profile."""
        # Running order:
        # - fetch new feeds
        # - filter new feeds using old feeds (loaded from file)
        # - save filtered feeds to file
        # - generate html from filtered feeds
        # - send email
        html = self.get_output_for_profile(profile)
        self.email_sender.send_email(profile, html)
        if update:
            profile.update_last_updated()
            profile.feed_handler.save()
    
    def get_output_for_profile(self, profile, update=False):
        """Fetch new entries for a profile and return the related output
        (the rendered template).
        
        Only save state and data if save=True (I expect this generally
        won't be appropriate because we only want to save when we
        successfully deliver the HTML to the user."""
        
        profile.feed_handler.update_feeds()
        html = self.html_generator.generate_html(profile)
        if update:
            profile.update_last_updated()
            profile.feed_handler.save()
        return html
    
    def email_profile_name(self, name, update=True):
        self.email_profile(self.get_profile(name), update=update)
