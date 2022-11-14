#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from datetime import datetime
from typing import List, Optional

from reader import make_reader

from rss_digest.config import Config
from rss_digest.exceptions import ProfileExistsError, FeedError, ProfileNotFoundError
from rss_digest.feeds import WILDCARD
from rss_digest.output import OutputGenerator, SendmailOutputSender
from rss_digest.output_context import ConfigContext, Context, FeedResult, EntryResult, CategoryResult, DateTimeHelper
from rss_digest.profile import Profile

class RSSDigest:

    def __init__(self, config: Config):
        self.config = config
        self._profile_cache: dict[str, Profile] = {}
        self._output_generator = OutputGenerator(config)
        self._output_sender = SendmailOutputSender(config)

    @property
    def profiles(self) -> List[str]:
        return os.listdir(self.config.profile_config_dir)

    def profile_exists(self, name: str) -> bool:
        return os.path.exists(os.path.join(self.config.profile_config_dir, name))

    def add_profile(self, name: str) -> Profile:
        """Create a new profile.

        :param name: The name of the profile to create.
        :return: The new profile's :class:`Profile` object.

        """
        if self.profile_exists(name):
            raise ProfileExistsError(f'Profile already exists: {name}')
        return Profile(self.config, name)


    def delete_profile(self, profile_name: str):
        """Permanently delete a profile, together with all associated configuration and state files."""
        if self.profile_exists(profile_name):
            profile = self.get_profile(profile_name)
            profile.rmdirs()
        else:
            raise ProfileNotFoundError(f'Profile "{profile_name}" does not exist.')

    def get_profile(self, profile_name: str) -> Profile:
        if profile_name in self._profile_cache:
            profile = self._profile_cache[profile_name]
        else:
            profile = Profile(self.config, profile_name)
            self._profile_cache[profile_name] = profile
        return profile

    def add_feed(self, profile_name: str, feed_url: str, feed_title: str, category: Optional[str] = None,
                 test_feed: bool = False, mark_read: bool = False, fetch_title: bool = False,
                 write: bool = True):
        """Add a feed to the :class:`FeedList`.

        :param profile_name: The name of the profile to act upon.
        :param feed_url: The URL of the feed.
        :param feed_title: The title of the feed.
        :param category: The category to which the feed belongs.
        :param test_feed: If True, request the feed's URL to ensure it is valid.
        :param mark_read: If True, update the feed and mark all existing entries as read immediately, so that the next
            time we generate a digest only subsequently added entries will be listed.
        :param fetch_title: If True, request the feed URL and set the title from the response. Overrides ``feed_title``.
        :param write: If True, write the FeedList to the profile's OPML file upon adding the feed.

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

    def update_feeds(self, profile_name: str) -> tuple[set[str], set[str]]:
        """Update all feeds for a given profile.

        :return: A tuple of two sets, the first of which contains urls of feeds that have been updated and the
        second of which is a list of URLs of feeds for which an error was received when updating."""

        return self.get_profile(profile_name).update_feeds()

    def get_config_context(self, profile_name: str) -> ConfigContext:
        """Get a ConfigContext object that can be used to generate
        output.

        :param profile_name: The name of the profile whose configuration
            should be used.

        """

        return ConfigContext.from_profile(self.get_profile(profile_name))

    def update_and_get_context(self, profile: Profile) -> Context:
        """Perform an update for the given profile, and generate a
        Context object which can be used to generate the output to be
        sent to the user.

        :param profile: The profile to be updated.

        """

        with make_reader(profile.reader_db_file) as reader:
            feedlist = profile.feedlist
            last_updated_utc = profile.last_updated
            updated, errors = self.update_feeds(profile.name)
            not_inactive = updated | errors     # URLs for all feeds that were either updated or errors (in other words,
                                                # if a URL is not in this set, we were able to fetch it but there were
                                                # no updates available).
            others = {f.xml_url for f in feedlist.feeds if f.xml_url not in not_inactive}
            updated_utc = datetime.utcnow()
            unread = profile.get_unread_entries()
            categories = []
            for cat_name in feedlist.category_dict:
                category = feedlist.category_dict[cat_name]
                updated_dict = {}
                errors_dict = {}
                others_dict = {}
                for f in category:
                    url = f.xml_url
                    if url in unread:
                        updated_dict[url] = FeedResult.from_reader(
                            reader.get_feed(url),
                            [EntryResult.from_reader(e) for e in unread[url]],
                            cat_name,
                            profile
                        )
                    elif url in errors:
                        errors_dict[url] = FeedResult.from_url(
                            url,
                            reader,
                            cat_name,
                            [],
                            profile
                        )
                    elif url in others:
                        others_dict[url] = FeedResult.from_url(
                            url,
                            reader,
                            cat_name,
                            [],
                            profile
                        )
                    else:
                        raise FeedError(
                            f'Feed URL "{url}" is present in FeedCategory but not accounted for in `updated`, '
                            f'`errors` or `others`.')
                categories.append(CategoryResult.from_dicts(
                    updated_dict,
                    errors_dict,
                    others_dict,
                    category,
                    profile
                ))

            return Context(
                profile_name=profile.name,
                update_time_utc=updated_utc,
                last_update_utc=last_updated_utc,
                categories=categories,
                config=ConfigContext.from_profile(profile),
                subscribed_feeds_count=len(feedlist.feeds),
                datetime_helper=DateTimeHelper.from_profile(profile)
            )

    def run(self, profile_name: str, save: bool = True, template: Optional[str] = None):
        """Get unread entries for a given profile and send in the
        appropriate way.

        :param profile_name: The name of the profile.
        :param save: If True, mark entries as read and update the "last_updated" value for the profile once the digest
            is sent.
        :param template: Name of template file for generating output.

        """
        profile = self.get_profile(profile_name)
        profile.sync_reader()
        context = self.update_and_get_context(profile)
        # print(context)
        template = template or profile.config['template']
        output = self._output_generator.generate(template, context)
        self._output_sender.send(output, profile)
        if save:
            profile.mark_read()
            profile.last_updated = datetime.utcnow()

    ### LEGACY CODE FOLLOWS

    # def new_profile(self, name, email):
    #     profile = Profile(self, name, email)
    #     return profile
    #
    # def del_profile(self, name):
    #     rmtree(join(self.profiles_dir, name), ignore_errors=True)
    #
    # def email_profile(self, profile, update=True):
    #     """Sends an RSS Digest email for the given profile."""
    #     # Running order:
    #     # - fetch new feeds
    #     # - filter new feeds using old feeds (loaded from file)
    #     # - save filtered feeds to file
    #     # - generate html from filtered feeds
    #     # - send email
    #     html = self.get_output_for_profile(profile)
    #     self.email_sender.send_email(profile, html)
    #     if update:
    #         profile.update_last_updated()
    #         profile.feed_handler.save()
    #
    # def get_output_for_profile(self, profile, update=False):
    #     """Fetch new entries for a profile and return the related output
    #     (the rendered template).
    #
    #     Only save state and data if save=True (I expect this generally
    #     won't be appropriate because we only want to save when we
    #     successfully deliver the HTML to the user."""
    #
    #     profile.feed_handler.update_feeds()
    #     html = self.html_generator.generate_html(profile)
    #     if update:
    #         profile.update_last_updated()
    #         profile.feed_handler.save()
    #     return html
    #
    # def email_profile_name(self, name, update=True):
    #     self.email_profile(self.get_profile(name), update=update)
