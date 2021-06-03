"""Helper functions, including factory functions, for generating and
working with the data classes defined in models.py.

"""
from typing import List, Optional, Dict

from pytz import timezone
from reader import Reader

import reader
from rss_digest.config import AppConfig, ProfileConfig
from rss_digest.exceptions import FeedError
from rss_digest.feedlist import FeedCategory, FeedList
from rss_digest.models import FeedResult, CategoryResult, ConfigContext, EntryResult, ContentResult, DateTimeHelper


def content_result_from_reader(content: reader.types.Content) -> ContentResult:
    """Generate a :class:`rss_digest.models.ContentResult` object from
    a :class:`reader.Content` object.

    """
    return ContentResult(
        value=content.value,
        type=content.type,
        language=content.language
    )


def entry_result_from_reader(entry: reader.types.Entry) -> EntryResult:
    """Generate a :class:`rss_digest.models.EntryResult` object from a
    :class:`reader.Entry` object.

    """

    return EntryResult(
        title=entry.title,
        link=entry.link,
        author=entry.author,
        published_utc=entry.published,
        summary=entry.summary,
        content=[content_result_from_reader(c) for c in entry.content],
        last_updated_utc=entry.last_updated
    )


def feed_result_from_reader(feed: reader.types.Feed, category: Optional[str],
                            entries: List[EntryResult]) -> FeedResult:
    """Generate a :class:`rss_digest.models.FeedResult` object from a
    :class:`reader.Feed` object.

    """
    return FeedResult(
        entries=entries,
        category=category,
        url=feed.url,
        updated_utc=feed.updated,
        title=feed.title,
        link=feed.link,
        author=feed.author,
        last_retrieved_utc=feed.last_updated
    )


def feed_result_from_url(url: str, reader: Reader, feedlist: FeedList, entries: List[EntryResult]) -> FeedResult:
    """Create a FeedResult from a URL.

    :param url: The URL of the feed.
    :param reader: The :class:`Reader` object, in order to get entries.
    :param feedlist: The :class:`FeedList` object, in order to get the
        feed category.
    :param entries: A list of :class:`EntryResult` objects.

    """
    feed = reader.get_feed(url)
    return feed_result_from_reader(
        feed=feed,
        category=feedlist.get_feed_by_url(url).category,
        entries=entries
    )


def category_result_from_dicts(updated: Dict[str, FeedResult], errors: Dict[str, FeedResult],
                               others: Dict[str, FeedResult], category: FeedCategory) -> CategoryResult:
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

    """

    _updated = []
    _errors = []
    _others = []
    for url in category.feed_urls:
        if url in updated:
            _updated.append(updated[url])
        elif url in errors:
            _errors.append(errors[url])
        elif url in others:
            _others.append(others[url])
        else:
            raise FeedError(f'Feed URL "{url}" is present in FeedCategory but not accounted for in `updated`, `errors`'
                            f'or `others`.')
    return CategoryResult(
        category.name,
        _updated,
        _errors,
        _others
    )


def config_context_from_configs(app_config: AppConfig, profile_config: ProfileConfig) -> ConfigContext:
    """Generate a :class:`ConfigContext` object from :class:`AppConfig`
    and :class:`ProfileConfig` objects.

    """
    return ConfigContext(
        profile_config.get_main_config_value('name'),
        profile_config.get_main_config_value('max_displayed_entries'),
        profile_config.get_main_config_value('max_displayed_feeds'),
    )


def datetime_helper_from_config(profile_config: ProfileConfig) -> DateTimeHelper:
    """Generate a :class:`DateTimeHelper` object from a
    :class:`ProfileConfig` object.

    """
    return DateTimeHelper(
        profile_config.get_main_config_value('datetime_format'),
        timezone(profile_config.get_main_config_value('timezone'))
    )
