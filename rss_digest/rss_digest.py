#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import logging
import shutil
import os
from typing import List, Optional

from reader import FeedExistsError as reader_FeedExistsError, Reader, make_reader, ParseError
from rss_digest.config import AppConfig, ProfileConfig
from rss_digest.exceptions import ProfileExistsError, FeedExistsError, FeedError
from rss_digest.feedlist import FeedList, from_opml_file, WILDCARD


class RSSDigest:
    
    def __init__(self, config: AppConfig):
        self.config = config

    @property
    def profiles(self) -> List[str]:
        return os.listdir(self.config.profiles_config_dir)

    def profile_exists(self, name: str) -> bool:
        return os.path.exists(self.config.get_profile_config_dir(name))
    
    def add_profile(self, name: str) -> ProfileConfig:
        """Create a new profile.

        :param name: The name of the profile to create.
        :return: The new profile's ProfileConfig object.

        """
        if self.profile_exists(name):
            raise ProfileExistsError(f'Profile already exists: {name}')
        return self.config.get_profile_config(name)

    def delete_profile(self, profile_name: str):
        shutil.rmtree(self.config.get_profile_config_dir(profile_name))
        shutil.rmtree(self.config.get_profile_data_dir(profile_name))

    def get_profile_config(self, name: str) -> ProfileConfig:
        return self.config.get_profile_config(name)

    def get_profile_feedlist(self, name: str) -> FeedList:
        profile_config = self.get_profile_config(name)
        return from_opml_file(profile_config.opml_file)

    def get_profile_reader(self, name: str, sync: bool = True) -> Reader:
        profile_config = self.get_profile_config(name)
        if sync:
            return self.sync_profile_reader(name)
        else:
            return make_reader(profile_config.feeds_db_file)

    def sync_profile_reader(self, name: str) -> Reader:
        """Sync a profile's :class:`reader.Reader` to its OPML file
        (adding feeds that are in the OPML file but not the Reader,
        and deleting those that are in the Reader but not the OPML
        file).

        :param: The name of the profile whose Reader to sync.
        :return: The modified Reader object.

        """
        logging.info(f'Syncing OPML file with reader database for profile {name}.')
        feedlist = self.get_profile_feedlist(name)
        reader = self.get_profile_reader(name)
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

    def add_feed(self, profile: str, feed_url: str, feed_title: str, category: Optional[str] = None,
                 test_feed: bool = False, mark_read: bool = False, fetch_title: bool = False):
        """Add a feed to the :class:`FeedList` for ``profile``.

        :param profile: The name of the profile to add the feed to.
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

        """
        reader = self.get_profile_reader(profile)
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

        feedlist = self.get_profile_feedlist(profile)
        feedlist.add_feed(feed_title, feed_url, category)

    def delete_feeds(self, profile: str, feed_url: Optional[str] = WILDCARD, feed_title: Optional[str] = WILDCARD,
                     category: Optional[str] = WILDCARD) -> int:
        """Delete all feeds for the given profile and matching the given
        title, URL and category.

        :param profile: The profile to delete the feeds from.
        :param feed_title: Title of feed to remove.
        :param feed_url: URL of feed to remove.
        :param category: Category of feed to remove.
        :return: The total number of feeds removed.

        """
        feedlist = self.get_profile_feedlist(profile)
        return feedlist.remove_feeds(feed_title, feed_url, category)