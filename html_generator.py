#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  html_generator.py

from os.path import join
from time import strftime
from datetime import datetime

from jinja2 import Environment, FileSystemLoader, select_autoescape

class HTMLGenerator:
    
    def __init__(self, profile):

        self.profile = profile
        self.template_dir = join(profile.conf_dir, 'templates')
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(['html']))
        self.template = self.jinja_env.get_template('email.html')
    
    def get_template(self, name):
        """Return the template file in the user's template folder,
        reverting to the standard one as a default.
        """
        if self.templates[name] is None:
            fpath = join(self.template_dir, '{}.html'.format(name))
            with open(fpath) as f:
                self.templates[name] = f.read()
        return self.templates[name]
    
    @property
    def email_template_firstrun(self):
        return self.get_template('email_firstrun')
    
    @property
    def email_template(self):
        return self.get_template('email')
    
    @property
    def feed_template(self):
        return self.get_template('feed')
    
    @property
    def entry_template(self):
        return self.get_template('entry')

    def generate_html(self, feedlist):
        #NOTE:  feedlist here is a FeedObjectList, not a FeedList
        
        gen_date = datetime.now().strftime(self.profile.get_conf('date_format'))
        gen_time = datetime.now().strftime(self.profile.get_conf('time_format'))
        
        current_datetime = strftime(self.profile.get_conf('datetime_format'))
        last_update = self.profile.get_last_updated()
        if last_update is not None:
            last_update = strftime(self.profile.get_conf('date_format'),
                            self.profile.get_last_updated())
        
        empty_feeds = feedlist.empty_feeds
        empty_feed_titles = '; '.join(f['feed']['title'] for f in empty_feeds)
        failures = feedlist.failures.keys()

        email_data = {
            'name': self.profile.get_conf('user_name'),
            'date': current_datetime,
            'first_run': self.profile.first_run,
            'feedlist': feedlist,
            'new_entries_count': feedlist.new_entries_count,
            'gen_date': gen_date,
            'gen_time': gen_time,
            'new_entries_total': feedlist.new_entries_total,
            'updated_feeds_count': len(feedlist.updated_feeds),
            'subscribed_feeds_count': len(feedlist.feeds),
            'new_entries_count': feedlist.new_entries_count,
            'get_author': feedlist.get_author,
            'get_date': lambda e: feedlist.get_date(e,
                self.profile.get_conf('datetime_format')),
            'get_feed_url': feedlist.get_feed_url,
            'last_update': last_update,
            'empty_feeds': empty_feeds,
            'non_empty_feeds': feedlist.non_empty_feeds,
            'empty_feed_titles': empty_feed_titles,
            'failures': feedlist.failures,
            'len': len,
            'max_feed_posts': self.profile.get_conf('max_feed_posts'),
            'categorised': self.profile.get_conf('categorised', 'bool')
            #finish
            }
            
        # TODO:  Change this to work with user-specific templates
        # (see method "email_template" above)
        email_html = self.template.render(**email_data)
        return email_html
