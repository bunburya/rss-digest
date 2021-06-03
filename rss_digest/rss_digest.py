#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import logging
import shutil
import os
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Set

from rss_digest.config import AppConfig
from rss_digest.exceptions import ProfileExistsError, ProfileNotFoundError, FeedError
from rss_digest.feedlist import WILDCARD
from rss_digest.model_utils import config_context_from_configs, feed_result_from_reader, feed_result_from_url, \
    entry_result_from_reader, category_result_from_dicts, datetime_helper_from_config
from rss_digest.models import ConfigContext, Context
from rss_digest.output import OutputGenerator, OutputSender
from rss_digest.profile import Profile


class RSSDigest:
    """This class kind of sits in the middle and ties everything
    together, and is mainly here so that different UIs have a consistent
    interface to interact with.

    """

    def __init__(self, config: AppConfig):
        self.config = config
        self._output_generator = OutputGenerator(config)
        self._output_sender = OutputSender(config)

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
        return Profile(name, self.config.get_profile_config(name))

    def delete_profile(self, profile_name: str):
        """Permanently delete a profile, together with all associated
        configuration and state files.

        """

        shutil.rmtree(self.config.get_profile_config_dir(profile_name))
        shutil.rmtree(self.config.get_profile_data_dir(profile_name))

    def get_profile(self, name: str) -> Profile:
        if self.profile_exists(name):
            return Profile(name, self.config.get_profile_config(name))
        else:
            raise ProfileNotFoundError(f'Profile "{name}" does not exist.')

    def add_feed(self, profile_name: str, feed_url: str, feed_title: str, category: Optional[str] = None,
                 test_feed: bool = False, mark_read: bool = False, fetch_title: bool = False,
                 write: bool = True):
        """Add a feed to the :class:`FeedList`.

        :param profile_name: The name of the profile to act upon.
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
        profile = self.get_profile(profile_name)
        return profile.add_feed(feed_url, feed_title, category, test_feed, mark_read, fetch_title, write)

    def delete_feeds(self, profile_name: str, feed_url: Optional[str] = WILDCARD, feed_title: Optional[str] = WILDCARD,
                     category: Optional[str] = WILDCARD) -> int:
        """Delete all feeds for the given profile and matching the given
        title, URL and category.

        :param profile_name: The profile to delete the feeds from.
        :param feed_title: Title of feed to remove.
        :param feed_url: URL of feed to remove.
        :param category: Category of feed to remove.
        :return: The total number of feeds removed.

        """
        return self.get_profile(profile_name).delete_feeds(feed_url, feed_title, category)

    def update_feeds(self, profile_name: str) -> Tuple[Set[str], Set[str]]:
        """Update all feeds for a given profile.

        :return: A tuple of two lists, the first of which is the list
            of urls of feeds that have been updated and the second of
            which is a list of URLs of feeds for which an error was
            received when updating."""

        return self.get_profile(profile_name).update_feeds()

    def get_config_context(self, profile_name: str) -> ConfigContext:
        """Get a ConfigContext object that can be used to generate
        output.

        :param profile_name: The name of the profile whose configuration
            should be used.

        """

        return config_context_from_configs(
            self.config,
            self.get_profile(profile_name).config
        )

    def update_and_get_context(self, profile: Profile) -> Context:
        """Perform an update for the given profile, and generate a
        Context object which can be used to generate the output to be
        sent to the user.

        :param profile: The profile to be updated.

        """

        profile_config = profile.config
        app_config = self.config
        reader = profile.reader
        feedlist = profile.feedlist
        last_updated_utc = profile.last_updated
        updated, errors = self.update_feeds(profile.name)
        not_inactive = updated | errors  # URLs for all feeds that were either updated or errors (in other words, if a
                                         # URL is not in this set, we were able to fetch it but there were no updates
                                         # available).
        others = {f.xml_url for f in feedlist.feeds if f.xml_url not in not_inactive}
        updated_utc = datetime.utcnow()
        unread = profile.get_unread_entries()
        categories = []
        for cat_name in feedlist.categories:
            category = feedlist.categories[cat_name]
            updated_dict = {}
            errors_dict = {}
            others_dict = {}
            for f in category:
                url = f.xml_url
                if url in unread:
                    updated_dict[url] = feed_result_from_reader(
                        reader.get_feed(url),
                        cat_name,
                        [entry_result_from_reader(e) for e in unread[url]]
                    )
                elif url in errors:
                    errors_dict[url] = feed_result_from_url(
                        url,
                        reader,
                        feedlist,
                        []
                    )
                elif url in others:
                    others_dict[url] = feed_result_from_url(
                        url,
                        reader,
                        feedlist,
                        []
                    )
                else:
                    raise FeedError(f'Feed URL "{url}" is present in FeedCategory but not accounted for in `updated`, '
                                    f'`errors` or `others`.')
            categories.append(category_result_from_dicts(
                updated_dict,
                errors_dict,
                others_dict,
                category
            ))

        return Context(
            profile_name=profile.name,
            update_time_utc=updated_utc,
            last_update_utc=last_updated_utc,
            categories=categories,
            config=config_context_from_configs(app_config, profile_config),
            subscribed_feeds_count=len(feedlist.feeds),
            datetime_helper=datetime_helper_from_config(profile_config)
        )

    def run(self, profile_name: str, save: bool = True,
            method: Optional[str] = None, format: Optional[str] = None):
        """Get unread entries for a given profile and send in the
        appropriate way.

        :param profile_name: The name of the profile.
        :param save: If True, mark entries as read and update the
            "last_updated" value for the profile once the digest is sent.
        :param method: The method to use to send the digest.
        :param format: How the output should be formatted.

        """
        profile = self.get_profile(profile_name)
        context = self.update_and_get_context(profile)
        profile_config = profile.config
        template = format or profile_config.get_main_config_value('output_format')
        output = self._output_generator.generate(template, context)
        self._output_sender.send(output, profile_config, method)
        if save:
            profile.mark_read()
            profile.last_updated = datetime.utcnow()

