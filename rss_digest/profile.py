from __future__ import annotations

import logging
import shutil

from dataclasses import dataclass
from datetime import datetime, timezone, tzinfo
from typing import Optional, List, Tuple, Dict

import pytz
from reader import Reader, make_reader, FeedExistsError as reader_FeedExistsError, ParseError, ReaderError, UpdatedFeed, \
    Entry
from rss_digest.config import ProfileConfig
from rss_digest.exceptions import FeedExistsError, FeedError
from rss_digest.feedlist import FeedList, from_opml_file, WILDCARD
from rss_digest.model_utils import entry_result_from_reader, feed_result_from_reader, category_result_from_dict
from rss_digest.models import CategoryResult, FeedResult


@dataclass
class Profile:
    name: str
    config: ProfileConfig

    def __post_init__(self):
        self._reader = None
        self._feedlist = None

    @property
    def feedlist(self) -> FeedList:
        if self._feedlist is None:
            self._feedlist = from_opml_file(self.config.opml_file)
        return self._feedlist

    @property
    def reader(self) -> Reader:
        """Return a :class:`reader.Reader` object for the profile.

        NOTE: This does not automatically sync the reader with the OPML
        file. Use the ``sync_reader`` method for that.

        """
        if self._reader is None:
            self._reader = make_reader(self.config.feeds_db_file)
        return self._reader

    @property
    def last_updated(self) -> Optional[datetime]:
        """Return the date and time at which a profile's feeds were
        last updated (ie, fetched), in UTC. If no updated has been
        performed, return None.

        """
        try:
            with open(self.config.last_updated_file) as f:
                dt = datetime.fromisoformat(f.read())
            if dt.tzinfo is None:
                dt = dt.astimezone(timezone.utc)
            return dt
        except FileNotFoundError:
            return None

    @last_updated.setter
    def last_updated(self, dt: datetime):
        with open(self.config.last_updated_file, 'w') as f:
            f.write(dt.astimezone(timezone.utc).isoformat())

    @property
    def local_timezone(self) -> tzinfo:
        return pytz.timezone(self.config.get_main_config_value('timezone'))

    def sync_reader(self) -> Reader:
        """Sync the profile's :class:`reader.Reader` to its OPML file
        (adding feeds that are in the OPML file but not the Reader,
        and deleting those that are in the Reader but not the OPML
        file).

        :param: The name of the profile whose Reader to sync.
        :return: The modified Reader object.

        """
        logging.info(f'Syncing OPML file with reader database for profile {self.name}.')
        feedlist = self.feedlist
        reader = self.reader
        opml_urls = {f.xml_url for f in feedlist}
        reader_urls = {f.url for f in reader.get_feeds()}
        removed = 0
        added = 0
        for url in reader_urls:
            if url not in opml_urls:
                reader.remove_feed(url)
                removed += 1
        for url in opml_urls:
            if url not in reader_urls:
                reader.add_feed(url)
                added += 1
        logging.debug(f'Removed {removed} feeds and added {added} feeds.')
        return reader

    def add_feed(self, feed_url: str, feed_title: str, category: Optional[str] = None,
                 test_feed: bool = False, mark_read: bool = False, fetch_title: bool = False,
                 write: bool = True):
        """Add a feed to the :class:`FeedList`.

        :param feed_url: The URL of the feed.
        :param feed_title: The title of the feed.
        :param category: The category to which the feed belongs.
        :param test_feed: If True, request the feed's URL to ensure
            it is valid.
        :param mark_read: If True, update the feed and mark all existing
            entries as read immediately, so that the next time we
            generate a digest only subsequently added entries will be
            listed.
        :param fetch_title: If True, request the feed URL and set the
            title from the response. Overrides ``feed_title``.
        :param write: If True, write the FeedList to the profile's OPML
            file upon adding the feed.

        """
        reader = self.reader
        try:
            reader.add_feed(feed_url)
        except reader_FeedExistsError:
            raise FeedExistsError(f'Feed with URL already exists: {feed_url}')

        if test_feed or mark_read or fetch_title:
            try:
                reader.update_feed(feed_url)
            except ParseError:
                raise FeedError(f'Error fetching or parsing feed at URL: {feed_url}')
            if mark_read:
                for entry in reader.get_entries(feed=feed_url):
                    reader.mark_as_read(entry)
            if fetch_title:
                feed_title = reader.get_feed(feed_url).title or feed_title

        feedlist = self.feedlist
        feedlist.add_feed(feed_url, feed_title, category)
        if write:
            feedlist.to_opml_file(self.config.opml_file)

    def delete_feeds(self, feed_url: Optional[str] = WILDCARD, feed_title: Optional[str] = WILDCARD,
                     category: Optional[str] = WILDCARD) -> int:
        """Delete all feeds for the given profile and matching the given
        title, URL and category.

        :param profile: The profile to delete the feeds from.
        :param feed_url: URL of feed to remove.
        :param feed_title: Title of feed to remove.
        :param category: Category of feed to remove.
        :return: The total number of feeds removed.

        """
        feedlist = self.feedlist
        return feedlist.remove_feeds(feed_title, feed_url, category)

    def set_opml_file(self, fpath: str, sync: bool = True):
        """Set the OPML file for the profile, replacing the existing one
        if it exists.

        :param fpath: The path to the new OPML file.
        :param sync: If True, automatically reload the profile's
            :class:`FeedList` object and sync the profile's ``reader``
            with it.

        """
        shutil.copy(fpath, self.config.opml_file)
        self._feedlist = None
        if sync:
            self.sync_reader()

    def update_feeds(self) -> Tuple[List[str], List[str]]:
        """Update all feeds for this profile.

        :return: A tuple of two lists, the first of which is the list
            of urls of feeds that have been updated and the second of
            which is a list of URLs of feeds for which an error was
            received when updating.

        """

        updated_urls = []
        error_urls = []
        self.sync_reader()
        for (url, value) in self.reader.update_feeds_iter():
            if isinstance(value, UpdatedFeed):
                logging.info(f'Got updated feed for {url}')
                updated_urls.append(url)
            elif isinstance(value, ReaderError):
                logging.error(f'Got error when updating {url}')
                error_urls.append(url)
        self.last_updated = datetime.utcnow()
        return updated_urls, error_urls

    def get_unread_entries(self, mark_read: bool = False) -> Dict[str, List[Entry]]:
        """Get all unread entries for this profile.

        :param mark_read: Whether to mark each entry as read.
        :return: A dict mapping feed URLs to lists of unread entries.

        """
        reader = self.reader
        entry_list = reader.get_entries(read=False)
        entries = {}
        for e in entry_list:
            url = e.feed_url
            if url in entries:
                entries[url].append(e)
            else:
                entries[url] = [e]
            if mark_read:
                reader.mark_as_read(e)
        return entries

    def mark_read(self, entries: Optional[List[Entry]] = None):
        """Mark entries as read.

        :param entries: List of entries to mark as read. If not provided,
            all unread entries will be marked as read.

        """

        if entries is None:
            entries = self.reader.get_entries(read=False)
        for e in entries:
            self.reader.mark_as_read(e)

    def get_category_results(self, mark_read: bool) -> List[CategoryResult]:
        """Get new entries, and use them to build a list of
        :class:`CategoryResult` objects that can be used to generate
        the output.

        :param mark_read: Whether to mark all new entries as read as we
            retrieve them. We probably don't normally don't want to do
            this, as it's better to wait until we have successfully
            generated (and preferably sent) the output.
        :return: A list of :class:`CategoryResult` objects, each of
            which corresponds to a user-defined category (or no
            category) and contains updated feeds belonging to that
            category.

        """

        unread = self.get_unread_entries(mark_read)
        # A dict mapping category names to dicts. Each key dict is a mapping of feed URLs to FeedResult objects.
        category_feed_results: Dict[str, Dict[str, FeedResult]] = {}
        for url in unread:
            entries = [entry_result_from_reader(e) for e in unread[url]]
            reader_feed = self.reader.get_feed(url)
            category = self.feedlist.get_feed_by_url(url).category
            if category in category_feed_results:
                category_feed_results[category][url] = feed_result_from_reader(reader_feed, category, entries)
            else:
                category_feed_results[category] = {url: feed_result_from_reader(reader_feed, category, entries)}
        category_results = []
        for c in self.feedlist.categories:
            if c in category_feed_results:
                category_results.append(category_result_from_dict(
                    category_feed_results[c],
                    self.feedlist.categories[c]
                ))
        return category_results


