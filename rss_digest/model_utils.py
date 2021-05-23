"""Helper functions, including factory functions, for generating and
working with the data classes defined in models.py.

"""
from typing import List, Optional, Dict

from reader import Reader

import reader
from rss_digest.config import AppConfig, ProfileConfig
from rss_digest.feedlist import FeedCategory, FeedList
from rss_digest.models import FeedResult, CategoryResult, ConfigContext, EntryResult, ContentResult


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
        published=entry.published,
        summary=entry.summary,
        content=[content_result_from_reader(c) for c in entry.content],
        last_updated=entry.last_updated
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
        updated=feed.updated,
        title=feed.title,
        link=feed.link,
        author=feed.author,
        last_retrieved=feed.last_updated
    )

def feed_result_from_url(url: str, reader: Reader, feedlist: FeedList, entries: List[EntryResult]) -> FeedResult:
    """Create a FeedResult from a URL.

    :param url: The URL of the feed.
    :param reader: The :class:`Reader` object, in order to get entries.
    :param feedlist: The :class:`FeedList` object, in order to get the
        feed category.

    """
    feed = reader.get_feed(url)
    return feed_result_from_reader(
        feed=feed,
        category=feedlist.get_feed_by_url(url).category,
        entries=entries
    )

def category_result_from_dict(url_dict: Dict[str, FeedResult], category: FeedCategory) -> CategoryResult:
    """Generate a :class:`rss_digest.models.CategoryResult` object.

    :param url_dict: A dict mapping feed URLs to :class:`FeedResult`
        objects.
    :param category: A :class:`FeedCategory` object for the relevant
        category. This is needed in order to get the right order for
        the feeds.

    """

    feeds = []
    for url in category.feed_urls:
        if url in url_dict:
            feeds.append(url_dict[url])
    return CategoryResult(
        category.name,
        feeds
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
