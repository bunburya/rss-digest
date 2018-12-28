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
    
    def __init__(self, app):
        logging.info('Initialising HTMLGenerator.')
        self.app = app
        self.global_config = app.config
        self.fallback_template_dir = self.global_config.template_dir
        self.jinja_env = Environment(
            loader=FunctionLoader(lambda n: self.get_template(profile, n)),
            autoescape=select_autoescape(['html']))
    
    def get_template(self, profile, name):
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

    #NOTE: Not sure we need any of these getter functions
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

    def generate_html(self, profile):
        """Generate HTML for email (or, conceivably, output in some other
        form, eg, non-HTML email, HTML for a webpage, etc)."""
        # TODO:  Have this function take profile as an arg, rather than
        # initialising class with profile, so that one instance can be
        # used to generate the output for multiple profiles.
        
        logging.info('Generating output for profile %s.', profile.name)
        
        feed_handler = profile.feed_handler
        
        gen_date = datetime.now().strftime(self.profile.get_conf('date_format'))
        gen_time = datetime.now().strftime(self.profile.get_conf('time_format'))
        
        current_datetime = strftime(self.profile.get_conf('datetime_format'))
        last_update = profile.get_last_updated()
        logging.info('Current time %s.  Last update was at %s.', current_datetime, last_update)
        if last_update is not None:
            last_update = strftime(profile.get_conf('date_format'),
                            profile.get_last_updated())
        
        empty_feeds = feed_handler.empty_feeds
        empty_feed_titles = '; '.join(f['feed']['title'] for f in empty_feeds)
        failures = feed_handler.failures.keys()
        if failures:
            logging.warn('Failed to load %d feeds.', len(failures))

        output_context_data = {
            'name': profile.get_conf('user_name'),
            'date': current_datetime,
            'first_run': profile.first_run,
            'feed_handler': feed_handler,
            'new_entries_count': feed_handler.new_entries_count,
            'gen_date': gen_date,
            'gen_time': gen_time,
            'new_entries_total': feed_handler.new_entries_total,
            'updated_feeds_count': len(feed_handler.updated_feeds),
            'subscribed_feeds_count': len(feed_handler.feeds),
            'new_entries_count': feed_handler.new_entries_count,
            'get_author': feed_handler.get_author,
            'get_date': lambda e: feed_handler.get_date(e,
                                profile.get_conf('datetime_format')),
            'get_feed_url': feed_handler.get_feed_url,
            'last_update': last_update,
            'empty_feeds': empty_feeds,
            'non_empty_feeds': feed_handler.non_empty_feeds,
            'empty_feed_titles': empty_feed_titles,
            'failures': feed_handler.failures,
            'len': len,
            'max_feed_posts': profile.get_conf('max_feed_posts'),
            'categorised': profile.get_conf('categorised', 'bool'),
            #finish
            }
           
        template_name = profile.get_conf('template')
        template = self.jinja_env.get_template(template_name)
        email_html = template.render(**output_context_data)
        return email_html
