from typing import Union

from reader import Entry
from rss_digest.feeds import FeedList, Feed, FeedCategory

"""Classes for storing :class:`Entry` objects, so that they can easily be retrieved from the relevant category and/or
feed url.

"""


class FeedEntries:
    """A class representing a collection of entries for a particular feed."""

    def __init__(self, feed: Feed):
        self.feed = feed
        self.entries: list[Entry] = []

    def add_entry(self, entry: Entry):
        self.entries.append(entry)


class FeedCategoryEntries:
    """A class to contain entries for feeds of a particular category."""

    def __init__(self, category: FeedCategory):
        self.category = category
        self.by_feed_url = {f.xml_url: FeedEntries(f) for f in category}

    def add_entry(self, entry: Entry):
        url = entry.feed_url
        self.by_feed_url[url].add_entry(entry)

    def get_entries(self, feed_or_url: Union[Feed, str]) -> list[Entry]:
        if isinstance(feed_or_url, Feed):
            url = feed_or_url.xml_url
        else:
            url = feed_or_url
        return self.by_feed_url[url]


class Entries:

    def __init__(self, feedlist: FeedList):
        self.feedlist = feedlist
        self.by_category: dict[str, FeedCategoryEntries] = {}
        self.url_to_category_name: dict[str, str] = {}
        for fc in feedlist.categories:
            self.by_category[fc.name] = FeedCategoryEntries(fc)
            for f in fc:
                self.url_to_category_name[f.xml_url] = fc.name

    def add_entry(self, entry: Entry):
        url = entry.feed_url
        cat_name = self.url_to_category_name[url]
        self.by_category[cat_name].add_entry(entry)
