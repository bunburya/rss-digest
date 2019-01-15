#  feedhandler.py

import logging
import json
from time import struct_time, strftime, gmtime
from os.path import join
from copy import deepcopy

import feedparser

class HTTPError(Exception): pass

class FeedParseError(Exception): pass

class FeedHandler:
    
    """This class represents a list of feed objects.  The individual
    feeds are objects returned by feedparser.parse.  It contains methods
    to load the feeds from file, load a list of URLs and fetch the
    feeds, update the feeds in the list, and save the list back to file.
    
    One instance of FeedHandler is instantiated per Profile, as this
    class loads, manipulates and saves state and data that is specific
    to a Profile.
    """
    
    # NOTE:  Attributes "feeds" and "new_feeds" of an instance of this
    # class are dicts mapping URLs to feed objects.  Related methods,
    # such as non_empty_feeds, updated_feeds, etc, return a list of
    # feed objects (in the same order as they appear in feedlist). 
        
    def __init__(self, profile):
        
        self.profile = profile
        self.name = profile.name
        self.new_feeds = None
        self.failures = {}
        self.load()
    
    def get_feed(self, url, **kwargs):
        """Fetches a feed (using feedparser).  If successful, return the
        feed.  Otherwise, add the url to a list of failures and return
        None."""
        
        logging.info('Fetching feed from %s.', url)
        fail = False
        try:
            feed = feedparser.parse(url, **kwargs)
            #print(feed.link)
            #print(feed['feed']['link'])
            #if not feed.link:
            #    feed.link = url
        except BaseException as e:
            fail = True
            self.failures[url] = e
        
        if feed.get('bozo', 0):
            # Feed not well formed
            fail = True
            self.failures[url] = feed['bozo_exception']
            logging.warning('Got feed not well formed error for %s.', url)
        elif feed['status'] >= 400 and feed['status'] <= 599:
            # HTTP error (TODO: split into temporary and permanent)
            fail = True
            self.failures[url] = HTTPError(feed['status'])
            logging.warning('Got HTTP error for %s.', url)
        elif (feed['status'] == 304) or (not feed['entries']):
            # Not modified or feed is empty.  Not really a fail (so
            # don't add to self.failures), but we return nothing all the
            # same.  (TODO: Consider whether this is the correct course
            # of action.)
            fail = True
            if url in self.failures:
                # If url has been added to failures (because an exception
                # has been raised), remove it because we don't want to report
                # this as a failure.
                # NOTE: Not ideal because what if an exception was raised
                # for another reason (actually failure related)?
                # Could that happen?
                self.failures.pop(url)
            logging.info('Got empty or unmodified feed at %s.', url)
        if fail:
            return None
        else:
            return feed
    
    #def get_feeds(self, from_file=False):
    #    self.failures = {}
    #    if from_file:
    #        self.feeds = self.profile.feeddata
    #    else:
    #        self.feeds = self.profile.feedlist.feeds
    
    #def load_feeds(self):
    #    # Load feeds from file
    #    with open(self.profile.data_file) as f:
    #        self.feeds = json.load(f)
    
    def update_feeds(self):
        """Updates self.feeds to contain only the entries that have been
        posted since the relevant feed was last updated.
        
        Returns the feeds that failed to update, in the form of a
        dict mapping each feed URL to its error."""
        
        logging.info('Updating feeds.')
        self.failures = {}
        new_feeds = {}
        for feedlist_entry in self.profile.feedlist:
            url = feedlist_entry['xmlUrl']
            feed = self.profile.feeddata.get(url)
            new_feeds[url] = self.get_new(url, feed)
        self.feeds = new_feeds
        return self.failures
    
    @property
    def ordered_feeds(self):
        """Return the feeds in the order in which they appear in the OPML file."""
        _ordered_feeds = []
        for entry in self.profile.feedlist:
            _ordered_feeds.append(self.feeds[entry['xmlUrl']])
        return _ordered_feeds
    
    @property
    def non_empty_feeds(self):
        return [f for f in self.ordered_feeds if f['entries']]
        
    @property
    def empty_feeds(self):
        return [f for f in self.ordered_feeds if not f['entries']]
    
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
    
    def get_new(self, url, feed=None):
        """Takes a URL and an existing feed object, and returns an
        updated feed object with only the new entries since the existing
        object was last updated.
        
        If feed is None, we just return the whole new feed as there was
        no previous feed. 
        
        If we can't fetch a new feed object (either because there was an
        error in fetching or because the feed was returned empty or
        unmodified, just return the old feed but erase the entries."""

        if feed is None:
            return self.get_feed(url)

        etag = feed.get('etag')
        modified = feed.get('modified')
        new_feed = self.get_feed(url, etag=etag, modified=modified)
        if new_feed is None:
            new_feed = feed
            new_feed['entries'] = []
            # TODO: consider what other attributes of the old feed we
            # might need to update/reset.
        else:
            self.filter_old(new_feed, feed.get('updated_parsed'))
        
        # Include certain additional data specific to rss-digest,
        # such as the title of the feed as specified by the user.
        # The reason we don't do this in get_feed is to ensure that, if
        # the user has changed the name of the feed, that change is
        # reflected.
        # TODO:  This doesn't work, maybe we need to move it.
        feedlist_entry = self.profile.get_feed_by_url(url)
        new_feed['rss-digest-data'] = {
            'title': feedlist_entry['text'],
            'category': feedlist_entry.get('category')
        }
        
        # TODO: Should the below be localtime instead of gmtime?
        self.profile.set_last_updated(gmtime(), new=True, url=url)
        return new_feed
    
    def new_entries_count(self, feed):
        return len(feed['entries'])
    
    @property
    def new_entries_total(self):
        total = 0
        for f in self.feeds.values():
            total += self.new_entries_count(f)
        return total
    
    @property
    def updated_feeds(self):
        return list(filter(lambda e: len(e['entries']), self.ordered_feeds))
    
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
