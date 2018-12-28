#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  html_generator.py

import logging

from os.path import join, exists
from time import strftime
from datetime import datetime

from jinja2 import Environment, FunctionLoader, select_autoescape
from jinja2.exceptions import TemplateNotFound

class HTMLGenerator:
    
    def __init__(self, profile):

        self.profile = profile
        self.global_conf = profile.app.config
        self.user_template_dir = profile.template_dir
        self.fallback_template_dir = self.global_conf.template_dir
        self.jinja_env = Environment(
            loader=FunctionLoader(self.get_template),
            autoescape=select_autoescape(['html']))
        #self.template = self.jinja_env.get_template('email.html')
    
    def get_template(self, name):
        """Return the template file in the user's template folder,
        reverting to the standard one as a default.
        This function is passed to the Jinja2 Environment Loader.
        """
        logging.info('Loading template "{}".'.format(name))
        user_fpath = join(self.user_template_dir, name)
        fallback_fpath = join(self.fallback_template_dir, name)
        if exists(user_fpath):
            fpath = user_fpath
            logging.info('Loading user-specific template at %s.', fpath)
        else:
            fpath = fallback_fpath
            logging.info('No user-specific template found.  '
                            'Using fallback at %s.', fpath)
        try:
            with open(fpath) as f:
                return f.read()
        except FileNotFoundError:
            logging.critical('Failed to load template at %s.', fpath)
            return None

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
        """Generate HTML for email (or, conceivably, output in some other
        form, eg, non-HTML email, HTML for a webpage, etc)."""
        # TODO:  Have this function take profile as an arg, rather than
        # initialising class with profile, so that one instance can be
        # used to generate the output for multiple profiles.
        
        # NOTE:  feedlist here is a FeedObjectList, not a FeedList
        
        logging.info('Generating output.')
        
        gen_date = datetime.now().strftime(self.profile.get_conf('date_format'))
        gen_time = datetime.now().strftime(self.profile.get_conf('time_format'))
        
        current_datetime = strftime(self.profile.get_conf('datetime_format'))
        last_update = self.profile.get_last_updated()
        logging.info('Current time %s.  Last update was at %s.', current_datetime, last_update)
        if last_update is not None:
            last_update = strftime(self.profile.get_conf('date_format'),
                            self.profile.get_last_updated())
        
        empty_feeds = feedlist.empty_feeds
        empty_feed_titles = '; '.join(f['feed']['title'] for f in empty_feeds)
        failures = feedlist.failures.keys()
        if failures:
            logging.warn('Failed to load %d feeds.', len(failures))

        output_context_data = {
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
            'categorised': self.profile.get_conf('categorised', 'bool'),
            #finish
            }
           
        template_name = self.profile.get_conf('template')
        template = self.jinja_env.get_template(template_name)
        email_html = template.render(**output_context_data)
        return email_html
