#  feedhandler.py

from datetime import datetime
from time import struct_time, strftime, gmtime
from os.path import join
from copy import deepcopy
import json

import feedparser

class HTTPError(BaseException): pass

class FeedParseError(BaseException): pass

class FeedObjectList:
    
    """This class represents a list of feed objects.  The individual
    feeds are objects returned by feedparser.parse.  It contains methods
    to load the feeds from file, load a list of URLs and fetch the
    feeds, update the feeds in the list, and save the list back to file.
    """ 
    
    # - load existing data from file
    # - fetch new feeds
    # - filter new feeds using old feeds
    # - save filtered feeds to file
    # - generate html from filtered feeds
    # - send email
        
    def __init__(self, profile):
        
        self.profile = profile
        self.name = profile.name
        self.new_feeds = None
        self.failures = {}
    
    def get_feed(self, url, **kwargs):
        fail = False
        try:
            feed = feedparser.parse(url, **kwargs)
            #print(feed.link)
            print(feed['feed']['link'])
            #if not feed.link:
            #    feed.link = url
        except BaseException as e:
            fail = True
            self.failures[url] = e
        
        if feed.get('bozo', 0):
            # Feed not well formed
            fail = True
            self.failures[url] = feed['bozo_exception']
        elif feed['status'] >= 400 and feed['status'] <= 599:
            # HTTP error (TODO: split into temporary and permanent)
            fail = True
            self.failures[url] = HTTPError(feed['status'])
        elif (feed['status'] == 304) or (not feed['entries']):
            # Not modified or feed is empty.  Not really a fail, but
            # we return nothing all the same.
            fail = True
        
        return feed if not fail else None
    
    def get_feeds(self, from_file=False):
        self.failures = {}
        if from_file:
            self.feeds = self.profile.feeddata
        else:
            self.feeds = self.profile.feedlist.feeds
    
    def update_profile(self):
        update_time = datetime.now().timetuple()
        self.profile.set_last_updated(update_time)
        for f in self.profile.feedlist:
            self.profile.set_last_updated(update_time, f['xmlUrl'])
        # finish
    
    def load_feeds(self):
        # Load feeds from file
        with open(self.profile.data_file) as f:
            self.feeds = json.load(f)
    
    def update_feeds(self):
        # TODO: Currently we rely on feedlist and feeddata being the 
        # same length and in the same order.  This won't work if the
        # list of feeds is changed.  We need to either do this more
        # flexibly so that it doesn't rely on strict alignment, or else
        # control access to feedlist such that requisite changes are
        # always made to feeddata.  This may be easiest.
        self.failures = {}
        new_feeds = []
        for u, f in zip(self.profile.feedlist, self.profile.feeddata):
            new_feeds.append(self.get_new(u['xmlUrl'], f))
        self.feeds = new_feeds
    
    @property
    def non_empty_feeds(self):
        return [f for f in self.feeds if f['entries']]
        
    @property
    def empty_feeds(self):
        return [f for f in self.feeds if not f['entries']]
    
    # Load and save state and feed data
    
    def save(self):
        self.profile.save_data(self.feeds)
        self.profile.save_state()
    
    def load(self):
        self.profile.load_data()
        self.profile.load_state()        
    
    def filter_old(self, new_feed, updated_parsed):
        # updated_parsed is when the OLD feed was last updated
        if updated_parsed is None:
            # If there is no updated_parse, feed is probably new
            # so there is nothing to be done.
            return new_feed
        entries = []
        for e in new_feed['entries']:
            updated = self.get_date(e)
            if updated > struct_time(updated_parsed):
                entries.append(e)
        new_feed['entries'] = entries
        return new_feed # returning new_feed, but change is also made
                        # in place
    
    def get_new(self, url, feed):
        """Takes a URL and an existing feed object, and returns an
        updated feed object with only the new entries since the existing
        object was last updated
        """
        etag = feed.get('etag')
        modified = feed.get('modified')
        new_feed = self.get_feed(url, etag=etag, modified=modified)
        if new_feed is None:
            new_feed = feed
            new_feed['entries'] = []
        else:
            self.filter_old(new_feed, feed.get('updated_parsed'))
            # TODO: Should the below be localtime instead of gmtime?
        self.profile.set_last_updated(gmtime(), new=True, url=url)
        return new_feed
    
    def new_entries_count(self, feed):
        return len(feed['entries'])
    
    @property
    def new_entries_total(self):
        total = 0
        for f in self.feeds:
            total += self.new_entries_count(f)
        return total
    
    @property
    def updated_feeds(self):
        return list(filter(lambda e: len(e['entries']), self.feeds))
    
    def get_author(self, entry):
        # Helper function to get the author of a feed in a convenient
        # way.  Should really be in the Entry class but we use
        # feedparser's standard entry class so we just stick it here.
        
        # If "author" is present, use it.
        # If it's not but "authors" is and there is only one
        # author specified, use that.  If there are multiple
        # authors specified, just say "multiple".
        # If you can't get the author from "author" or "authors"
        # just say "unknown".
        author = entry.get('author')
        if author is None:
            authors = entry.get('authors')
            if authors is None:
                author = 'unknown'
            elif len(authors) > 1:
                author = 'multiple'
            else:
                author = authors[0].get('name', 'unknown')
        return author
    
    def get_date(self, entry, fmt=None):
        date_struct = struct_time(
            entry.get('updated_parsed', entry.published_parsed))
        if fmt is not None:
            return strftime(fmt, date_struct)
        else:
            return date_struct

    def get_feed_url(self, feed):
        return feed.feed['link'] or feed.feed['links'][0].href
