"""This file contains data classes which will be provided as context
when generating output.

"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, tzinfo
from typing import Optional, List

import reader
from pytz import timezone
from reader import Reader

from rss_digest.exceptions import FeedNotFoundError
from rss_digest.feeds import FeedCategory
from rss_digest.profile import Profile

try:
    from functools import cached_property
except ImportError:
    # cached_property is not available (probably because Python < 3.8).
    # Just use normal property decorator. Performance will be slightly worse.
    cached_property = property


@dataclass
class ConfigContext:
    """A data class with information about configuration options that
    are relevant to how output is displayed.

    """

    user_name: Optional[str]  #: The user-defined name for the profile.
    max_visible_entries: int  #: The maximum number of entries to display for each feed.
    max_visible_feeds: int  #: The maximum number of feeds to display for each category.
    helpers: object = field(default_factory=object)  #: A module containing user-defined "helper" Python objects.

    @classmethod
    def from_profile(cls, profile: Profile) -> ConfigContext:
        """Generate a :class:`ConfigContext` object from a :class:`Profile` object.

        """
        config = profile.config
        return ConfigContext(
            config.get('name'),
            config.get('max_displayed_entries'),
            config.get('max_displayed_feeds'),
        )


@dataclass
class ContentResult:
    """A data class representing a piece of content in an entry."""

    value: str  #: The actual content.
    # value_plaintext: Optional[str]  #: The content, as plaintext (ie, with HTML removed).
    type: Optional[str]  #: The type of the content.
    language: Optional[str]  #: The language of the content.

    @classmethod
    def from_reader(cls, content: reader.types.Content) -> ContentResult:
        """Generate a :class:`ContentResult` object from
        a :class:`reader.Content` object.

        """
        return cls(
            value=content.value,
            type=content.type,
            language=content.language
        )


@dataclass
class EntryResult:
    """A data class representing a single new entry (new can mean that
    the entry has been updated since it was last retrieved).

    """

    title: Optional[str]  #: The title of the feed.
    link: Optional[str]  #: A URL of a page associated with the entry.
    author: Optional[str]  #: The author of the entry.
    published_utc: Optional[datetime]  #: When the entry was originally published, in UTC.
    summary: Optional[str]  #: A summary of the entry.
    content: List[ContentResult]  #: The full content of the entry.
    last_updated_utc: Optional[datetime]  #: When the entry was last updated, in UTC.

    @classmethod
    def from_reader(cls, entry: reader.types.Entry) -> EntryResult:
        """Generate a :class:`rss_digest.models.EntryResult` object from a
        :class:`reader.Entry` object.

        """

        return EntryResult(
            title=entry.title,
            link=entry.link,
            author=entry.author,
            published_utc=entry.published,
            summary=entry.summary,
            content=[ContentResult.from_reader(c) for c in entry.content],
            last_updated_utc=entry.last_updated
        )


@dataclass
class CategoryResult:
    """A data class representing a category of updated feeds."""

    name: Optional[str]  #: The name of the category, or None if this object contains feeds with no category.
    visible_updated_feeds: List[FeedResult]  #: Updated feeds in this category to display to the user.
    all_updated_feeds: List[FeedResult]  #: All updated feeds in this category.
    error_feeds: List[FeedResult]  #: Feeds in this category that returned an error when trying to update.
    other_feeds: List[FeedResult]  #: Feeds in this category that don't belong to updated_feeds or error_feeds.

    @cached_property
    def all_updated_feeds_count(self) -> int:
        """The number of all updated feeds."""
        return len(self.all_updated_feeds)

    @cached_property
    def visible_updated_feeds_count(self) -> int:
        """The number of updated feeds that should be shown to the user."""
        return len(self.visible_updated_feeds)

    @cached_property
    def invisible_updated_feeds_count(self) -> int:
        """The number of updated feeds that should not be shown to the
        user, by virtue of being over the user-specified limit of feeds
        to display.

        """
        return self.all_updated_feeds_count - self.visible_updated_feeds_count

    @cached_property
    def error_feeds_count(self) -> int:
        """The number of feeds that returned an error when trying to update them."""
        return len(self.error_feeds)

    @cached_property
    def other_feeds_count(self) -> int:
        """The number of feeds that were not updated and did not return an error."""
        return len(self.other_feeds)

    @classmethod
    def from_dicts(cls, updated: dict[str, FeedResult], errors: dict[str, FeedResult],
                   others: dict[str, FeedResult], category: FeedCategory,
                   profile: Profile) -> CategoryResult:
        """Generate a :class:`rss_digest.models.CategoryResult` object.

        :param updated: A dict mapping feed URLs to :class:`FeedResult`
            objects for feeds that have been updated.
        :param errors: A dict mapping feed URLs to :class:`FeedResult`
            objects for feeds that returned an error when trying to update
            them.
        :param others: A dict mapping feed URLs to :class:`FeedResult`
            objects for other feeds.
        :param category: A :class:`FeedCategory` object for the relevant
            category. This is needed in order to get the right order for
            the feeds.
        :param profile: A :class:`Profile` object to get certain relevant
            configuration options.

        """

        config = profile.config

        _updated = []
        _errors = []
        _others = []
        for f in category.feeds:
            url = f.xml_url
            if url in updated:
                _updated.append(updated[url])
            elif url in errors:
                _errors.append(errors[url])
            elif url in others:
                _others.append(others[url])
            else:
                raise FeedNotFoundError(f'Feed URL "{url}" is present in FeedCategory but not accounted for in '
                                        '`updated`, `errors` or `others`.')
        if category.name is not None:
            _name = category.name
        else:
            _name = config['uncategorized_name']

        _visible = _updated[:config['max_displayed_feeds']]

        return CategoryResult(
            name=_name,
            visible_updated_feeds=_visible,
            all_updated_feeds=_updated,
            error_feeds=_errors,
            other_feeds=_others
        )


@dataclass
class FeedResult:
    """A data class representing a single updated feed."""

    all_new_entries: List[EntryResult]  #: A list of Entry objects representing all new/updated entries.
    visible_new_entries: List[EntryResult]  #: A list of new/updated Entry objects to display.
    category: Optional[str]  #: The category of the feed.
    url: Optional[str]  #: The URL of the feed.
    updated_utc: Optional[datetime]  #: When the feed was last updated, or None.
    title: Optional[str]  #: The title of the feed.
    link: Optional[str]  #: The URL of a page associated with the entry.
    author: Optional[str]  #: The author of the feed.
    # user_title: Optional[str]  #: The user-defined title of the feed.
    last_retrieved_utc: Optional[datetime]  #: When the feed was last retrieved, or None.

    @cached_property
    def visible_new_entries_count(self) -> int:
        """The number of new or updated entries to display to the user."""
        return len(self.visible_new_entries)

    @cached_property
    def all_new_entries_count(self) -> int:
        """The number of all new or updated entries."""
        return len(self.all_new_entries)

    @cached_property
    def invisible_new_entries_count(self) -> int:
        """The number of new or updated entries that should not be shown
        to the user as they exceed the specified maximum number of
        entries to display.

        """
        return self.all_new_entries_count - self.visible_new_entries_count

    @classmethod
    def from_reader(cls, feed: reader.types.Feed, entries: List[EntryResult], category: Optional[str],
                    profile: Profile) -> FeedResult:
        """Generate a :class:`FeedResult` object from a :class:`reader.Feed` object.

        """

        return FeedResult(
            visible_new_entries=entries[:profile.config['max_displayed_entries']],
            all_new_entries=entries,
            category=category,
            url=feed.url,
            updated_utc=feed.updated,
            title=feed.title,
            link=feed.link,
            author=feed.author,
            last_retrieved_utc=feed.last_updated
        )

    @classmethod
    def from_url(cls, url: str, reader: Reader, category: str, entries: List[EntryResult],
                 profile: Profile) -> FeedResult:
        """Create a FeedResult from a URL.

        :param url: The URL of the feed.
        :param reader: The :class:`Reader` object, in order to get entries.
        :param category: The feed category.
        :param entries: A list of :class:`EntryResult` objects.
        :param profile: A :class:`Profile` object in order to get
            certain user preferences.

        """
        feed = reader.get_feed(url)
        return FeedResult.from_reader(
            feed=feed,
            entries=entries,
            category=category,
            profile=profile
        )


@dataclass
class DateTimeHelper:
    """A data class to store user preferences regarding handling of
    dates and times, and some helper functions to convert and format
    datetime objects.

    """

    format: str  #: The desired format for displaying datetime objects, as a string compatible with datetime.strftime.
    local_timezone: tzinfo  #: The user's preferred local timezone.

    def local(self, dt: Optional[datetime]) -> Optional[datetime]:
        """Convert a :class:`datetime` object to the user's local
        timezone.

        """
        return dt.astimezone(self.local_timezone) if dt is not None else None

    def formatted(self, dt: Optional[datetime]) -> Optional[str]:
        """Format a :class:`datetime` object as a string."""
        return dt.strftime(self.format) if dt is not None else None

    def local_formatted(self, dt: datetime) -> str:
        """Convert a :class:`datetime` object to the user's local
        timezone and format as a string.

        """
        return self.formatted(self.local(dt))

    @classmethod
    def from_profile(cls, profile: Profile) -> DateTimeHelper:
        """Generate a :class:`DateTimeHelper` object from a :class:`Profile` object.

        """
        config = profile.config
        return DateTimeHelper(
            config.get('datetime_format'),
            timezone(config['timezone'])
        )

@dataclass
class Context:
    """A data class containing information about an update, that is
    provided as context when generating output.

    """

    profile_name: str  #: The name of the profile.
    update_time_utc: datetime  #: The date and time of this update in UTC.
    last_update_utc: Optional[datetime]  #: The date and time of the last update in UTC, or None.
    categories: List[CategoryResult]  #: A list of CategoryResult objects.
    config: ConfigContext  #: A ConfigContext object with some information about how output should be displayed.
    subscribed_feeds_count: int  #: How many feeds, in total, the profile is subscribed to.
    datetime_helper: DateTimeHelper  #: A helper function for displaying and converting dates and times.

    @cached_property
    def all_updated_feeds(self) -> List[FeedResult]:
        """All feeds which were updated."""
        feeds = []
        for c in self.categories:
            for f in c.all_updated_feeds:
                feeds.append(f)
        return feeds

    @cached_property
    def updated_feeds_count(self) -> int:
        """The number of updated feeds."""
        return len(self.all_updated_feeds)

    @cached_property
    def updated_categories(self) -> List[CategoryResult]:
        """A list of CategoryResult objects which contain at least one
        updated feed.

        """
        return list(filter(lambda c: c.all_updated_feeds, self.categories))

    @cached_property
    def updated_categories_count(self) -> int:
        """The number of categories containing at least one updated
        feed.

        """
        count = 0
        for c in self.categories:
            if c.all_updated_feeds:
                count += 1
        return count

    @cached_property
    def updated_entries_count(self) -> int:
        """The total number of new or updated entries."""
        return sum(f.all_new_entries_count for f in self.all_updated_feeds)

    @cached_property
    def error_feeds(self) -> List[FeedResult]:
        """All feeds for which errors were encountered when trying to
        update.

        """
        feeds = []
        for c in self.categories:
            for f in c.error_feeds:
                feeds.append(f)
        return feeds

    @cached_property
    def error_feeds_count(self) -> int:
        """The number of feeds that returned an error when updating."""
        return len(self.error_feeds)

    @cached_property
    def other_feeds(self) -> List[FeedResult]:
        """All feeds which were successfully fetched but for which there
        are no updates.

        """
        feeds = []
        for c in self.categories:
            for f in c.other_feeds:
                feeds.append(f)
        return feeds

    @cached_property
    def other_feeds_count(self) -> int:
        """The number of feeds that were successfully fetched but have
        not been updated.

        """
        return len(self.other_feeds)

    @cached_property
    def other_feeds_titles(self) -> List[str]:
        """The titles of other feeds, as a list of strings."""
        return [f.title for f in self.other_feeds]

    @cached_property
    def has_categories(self) -> bool:
        """Whether at least one of the updated feeds belongs to a
        category.

        """
        c = self.updated_categories
        return (len(c) > 1) or (c and c[0].name is not None)

    def local_format(self, dt: datetime) -> str:
        """A "shortcut" to DateTimeHelper.local_formatted, to save
        typing (as we're likely to use that function a lot in
        templates).

        """
        return self.datetime_helper.local_formatted(dt)
