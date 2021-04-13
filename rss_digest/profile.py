from __future__ import annotations

import logging
import os
import shutil

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from reader import Reader, make_reader, FeedExistsError as reader_FeedExistsError, ParseError
from rss_digest.config import ProfileConfig
from rss_digest.exceptions import FeedExistsError, FeedError
from rss_digest.feedlist import FeedList, from_opml_file, WILDCARD


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
        """Return a ``reader.Reader`` object for the profile.

        NOTE: This does not automatically sync the reader with the OPML
        file. Use the ``sync_reader`` method for that.

        """
        if self._reader is None:
            self._reader = make_reader(self.config.feeds_db_file)
        return self._reader

    @property
    def last_updated(self) -> datetime:
        """Return the date and time at which a profile's feeds were
        last updated (ie, fetched), in UTC.

        """
        with open(self.config.last_updated_file) as f:
            return datetime.fromisoformat(f.read())

    @last_updated.setter
    def last_updated(self, dt: datetime):
        with open(self.config.last_updated_file, 'w') as f:
            f.write(dt.isoformat())

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