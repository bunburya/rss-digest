"""This file contains data classes which will be provided as context
when generating output.

"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class Context:
    """A data class containing information about an update, that is
    provided as context when generating output.

    """

    profile_name: str  #: The name of the profile.
    update_time_utc: datetime  #: The date and time of this update in UTC.
    update_time_local: Optional[datetime]  #: The date and time of this update in local time.
    last_update_utc: Optional[datetime]  #: The date and time of the last update in UTC, or None.
    last_update_local: Optional[datetime]  #: The date and time of the last update in local time, or None.
    updated_feeds: List[FeedResult]  #: A list of Feed objects, containing feeds with new or updated entries.
    updated_categories: List[CategoryResult]  #: A list of Category objects, containing updated feeds.
    error_feeds: List[FeedResult]  #: A list of Feed objects, representing feeds for which an error was obtained.
    config: ConfigContext  #: A ConfigContext object with some information about how output should be displayed.

    @property
    def updated_count(self) -> int:
        """The number of updated feeds."""
        return len(self.updated_feeds)

    @property
    def error_count(self) -> int:
        """The number of feeds that returned an error when updating."""
        return len(self.error_feeds)


@dataclass
class ConfigContext:
    """A data class with information about configuration options that
    are relevant to how output is displayed.

    """

    profile_user_name: Optional[str]  #: The user-defined name for the profile.
    max_entries: int  #: The maximum number of entries to display for each feed.
    max_feeds: int  #: The maximum number of feeds to display for each category.

@dataclass
class CategoryResult:
    """A data class representing a category of updated feeds."""

    name: Optional[str]  #: The name of the category, or None if this object contains feeds with no category.
    feeds: List[FeedResult]  #: A list of feeds in this category.

    @property
    def feed_count(self) -> int:
        """The number of feeds present."""
        return len(self.feeds)

@dataclass
class FeedResult:
    """A data class representing a single updated feed."""

    entries: List[EntryResult]  #: A list of Entry objects representing the feed's new entries.
    category: Optional[str]  #: The category of the feed.
    url: Optional[str]  #: The URL of the feed.
    updated: Optional[str]  #: When the feed was last updated.
    title: Optional[str]  #: The title of the feed.
    link: Optional[str]  #: The URL of a page associated with the entry.
    author: Optional[str]  #: The author of the feed.
    #user_title: Optional[str]  #: The user-defined title of the feed.
    last_retrieved: Optional[str]  #: When the feed was last retrieved.

    @property
    def entry_count(self) -> int:
        """The number of entries present."""
        return len(self.entries)


@dataclass
class EntryResult:
    """A data class representing a single new entry (new can mean that
    the entry has been updated since it was last retrieved).

    """

    title: Optional[str]  #: The title of the feed.
    link: Optional[str]  #: A URL of a page associated with the entry.
    author: Optional[str]  #: The author of the entry.
    published: Optional[datetime]  #: When the entry was originally published.
    summary: Optional[str]  #: A summary of the entry.
    content: List[ContentResult]  #: The full content of the entry.
    last_updated: Optional[datetime]  #: When the entry was last updated.

@dataclass
class ContentResult:
    """A data class representing a piece of content in an entry."""

    value: str
    type: Optional[str]
    language: Optional[str]