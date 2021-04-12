#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import logging
import shutil
import os
from typing import List, Optional

from rss_digest.config import AppConfig
from rss_digest.exceptions import ProfileExistsError, ProfileNotFoundError
from rss_digest.feedlist import WILDCARD
from rss_digest.profile import Profile


class RSSDigest:

    """This class kind of sits in the middle and ties everything
    together, and is mainly here so that different UIs have a consistent
    interface to interact with.

    """
    
    def __init__(self, config: AppConfig):
        self.config = config

    @property
    def profiles(self) -> List[str]:
        return os.listdir(self.config.profiles_config_dir)

    def profile_exists(self, name: str) -> bool:
        return os.path.exists(self.config.get_profile_config_dir(name))
    
    def add_profile(self, name: str) -> Profile:
        """Create a new profile.

        :param name: The name of the profile to create.
        :return: The new profile's :class:`Profile` object.

        """
        if self.profile_exists(name):
            raise ProfileExistsError(f'Profile already exists: {name}')
        return Profile(self.config.get_profile_config(name))

    def delete_profile(self, profile_name: str):
        shutil.rmtree(self.config.get_profile_config_dir(profile_name))
        shutil.rmtree(self.config.get_profile_data_dir(profile_name))

    def get_profile(self, name: str) -> Profile:
        if self.profile_exists(name):
            return Profile(name, self.config.get_profile_config(name))
        else:
            raise ProfileNotFoundError(f'Profile "{name}" does not exist.')

    def add_feed(self, profile: str, feed_url: str, feed_title: str, category: Optional[str] = None,
                 test_feed: bool = False, mark_read: bool = False, fetch_title: bool = False,
                 write: bool = True):
        """Add a feed to the :class:`FeedList`.

        :param profile: The name of the profile to act upon.
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
        return self.get_profile(profile).add_feed(feed_url, feed_title, category, test_feed, mark_read, fetch_title,
                                                  write)

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
        return self.get_profile(profile).delete_feeds(feed_url, feed_title, category)

