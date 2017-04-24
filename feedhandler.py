#  feedhandler.py

# TODO:
# - sort out config.
#   - each "profile" has 3 elements:
#     - profile-specific config file (ini, things like name, options
#       to override defaults (eg, template files), etc)
#     - feed list (txt, one url per line, eventually move to OPML)
#     - state file (json, last updated, etc)
#   - general config includes ini file and template files
#     - goes in .config/rss-digest
#   - profile-specific conf dir will be .config/rss-digest/profiles/{profile}/
# - handle non-firstrun html (relying on state file)
# - do email.py
# - use jinja2 for template

from datetime import datetime
from time import struct_time, strftime, gmtime
from os.path import join
from copy import deepcopy
import json

import feedparser

class HTTPError(BaseException): pass

class FeedList:
    
    """This class represents a list of feeds.  The individual feeds are
    objects returned by feedparser.parse.  It contains methods to load
    the feeds from file, load a list of URLs and fetch the feeds, update
    the feeds in the list, and save the list back to file.
    """ 
    
    # - load existing data from file
    # - fetch new feeds
    # - filter new feeds using old feeds
    # - save filtered feeds to file
    # - generate html from filtered feeds
    # - send email
        
    def __init__(self, config, name):
        
        self.config = config
        self.name = name
        self.new_feeds = None
    
    def get_feeds(self, from_file=False):
        if from_file:
            self.feeds = self.config.data
        else:
            feeds = []
            with open(self.config.list_file) as f:
                for line in f:
                    feeds.append(feedparser.parse(line.strip()))
            self.feeds = feeds
    
    def update_config(self):
        update_time = datetime.now().timetuple()
        self.config.set_last_updated(update_time)
        for url in self.feed_urls:
            self.config.set_last_updated(update_time, url)
        # finish
    
    def load_feeds(self):
        # Load feeds from file
        with open(self.config.data_file) as f:
            self.feeds = json.load(f)
    
    def update_feeds(self):
        # TODO: Currently we rely on feedlist and feeddata being the 
        # same length and in the same order.  This won't work if the
        # list of feeds is changed.  We need to either do this more
        # flexible so that it doesn't rely on strict alignment, or else
        # control access to feedlist such that requisite changes are
        # always made to feeddata.  This may be easiest.
        new_feeds = []
        for u, f in zip(self.config.feedlist, self.config.feeddata):
            new_feeds.append(self.get_new(u, f))
        self.feeds = new_feeds
    
    @property
    def non_empty_feeds(self):
        return [f for f in self.feeds if f['entries']]
        
    @property
    def empty_feeds(self):
        return [f for f in self.feeds if not f['entries']]
    
    # Load and save state and feed data
    
    def save(self):
        self.config.save_data(self.feeds)
        self.config.save_state()
    
    def load(self):
        self.config.load_data()
        self.config.load_state()        
    
    def filter_old(self, new_feed, updated_parsed):
        # updated_parsed is when the OLD feed was last updated
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
        new_feed = feedparser.parse(url, etag=etag, modified=modified)
        
        # Handle errors (there are many more; eventually we should beef
        # this up and maybe move it to a different function)
        if new_feed.get('bozo', 0):
            # Feed not well formed
            raise new_feed['bozo_exception']
        elif new_feed['status'] >= 400 and new_feed['status'] <= 599:
            # HTTP error (TODO: split into temporary and permanent)
            raise HTTPError(new_feed['status'])
        elif (new_feed['status'] == 304) or (not new_feed['entries']):
            # not modified or feed is empty
            new_feed = deepcopy(feed)
            new_feed['entries'] = []
        else:
            self.filter_old(new_feed, feed['updated_parsed'])
        # TODO: Should the below be localtime instead of gmtime?
        self.config.set_last_updated(gmtime(), new=True, url=url)
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
        

def main(args):
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
