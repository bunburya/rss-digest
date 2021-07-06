#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import logging
import os

from collections import OrderedDict
from copy import deepcopy
from dataclasses import dataclass, field, replace
from datetime import datetime
from email.utils import parsedate_to_datetime, format_datetime
from typing import Optional, List, OrderedDict as OrderedDictType, Any, Union, Dict

from rss_digest.exceptions import BadOPMLError, CategoryExistsError, FeedExistsError

logger = logging.getLogger(__name__)

try:
    from lxml.etree import ElementTree, SubElement, Element, parse, tostring
    has_lxml = True
except ImportError:
    logger.warning('lxml not installed.  Using Python\'s standard ElementTree library.  '
                    'Written OPML files will not have pretty formatting.')
    from xml.etree.ElementTree import ElementTree, SubElement, Element, parse, tostring
    has_lxml = False


class WildCardType:
    """A class that evaluates as True against anything."""

    def __repr__(self):
        return 'WildCard'

    def __eq__(self, other):
        return True


WILDCARD = WildCardType()


@dataclass
class FeedSearch:
    """A class for searching for Feed instances. A FeedSearch will
    evaluate as equal to a Feed if all of the FeedSearch's non-None
    values match the equivalent values of the Feed.
    """

    title: Optional[str] = WILDCARD
    xml_url: Optional[str] = WILDCARD
    category: Optional[str] = WILDCARD

    def __eq__(self, other):
        return all((
            isinstance(other, Feed),
            self.title == other.title,
            self.xml_url == other.xml_url,
            self.category == other.category
        ))


@dataclass
class Feed:
    """A representation of a single feed."""

    xml_url: str
    title: str
    category: Optional[str] = None

    def to_opml(self) -> Element:
        return Element('outline', {'type': 'rss', 'text': self.title, 'xmlUrl': self.xml_url})

    @staticmethod
    def from_opml(elem: Element, category: Optional[str] = None) -> 'Feed':
        attr = dict(elem.attrib)
        if 'text' in attr:
            title = attr.pop('text')
        elif 'title' in attr:
            title = attr['title']
        else:
            logger.warning('RSS outline element has neither "text" nor "title" attribute.')
            title = ''
        return Feed(title=title, xml_url=attr['xmlUrl'], category=category)


@dataclass
class FeedCategory:
    """A representation of a category of feeds."""

    name: Optional[str] = None
    feeds: List[Feed] = field(default_factory=list)

    @property
    def feed_urls(self) -> List[str]:
        return [f.xml_url for f in self.feeds]

    def add_feed(self, feed: Feed, index: Optional[int] = None) -> bool:
        """Add a feed to the category.

        :param feed: The :class:`Feed` object to add.
        :param index: The index at which to insert the feed. If not given, append feed to end.
        :return: Whether the feed was successfully added.

        """
        if feed.xml_url in self.feed_urls:
            logger.error(f'Could not add feed with title "{feed.title} and URL "{feed.xml_url} to category "{self.name}'
                         f' because a feed with that URL already exists.')
            return False
            #raise FeedExistsError(f'Feed with URL "{feed.xml_url}" already exists in category "{self.name}".')
        if index is None:
            self.feeds.append(feed)
        else:
            self.feeds.insert(index, feed)
        return True

    def extend(self, other: FeedCategory):
        self.feeds.extend(other.feeds)

    def to_opml(self) -> Element:
        elem = Element('outline', {'type': 'category', 'text': self.name})
        for feed in self.feeds:
            elem.append(feed.to_opml())
        return elem

    def remove_feeds(self, feed: Union[Feed, FeedSearch]) -> int:
        """Remove all feeds matching the given object.

        :param feed: The feed to remove, as a :class:`Feed` or a
            :class:`FeedSearch`. All feeds which equal the ``feed``
            object will be removed.
        :return: The number of feeds removed.

        """
        num_feeds = len(self.feeds)
        self.feeds = list(filter(lambda f: f != feed, self.feeds))
        return num_feeds - len(self.feeds)

    def copy(self) -> FeedCategory:
        """Return a deepcopy of this instance."""
        return FeedCategory(
            name=self.name,
            feeds=[replace(f) for f in self.feeds]
        )

    @classmethod
    def _flatten_category(cls, elem: Element, category: Optional[str] = None) -> List[Feed]:
        """Recursively parse a `category` outline element and return a
        flattened list of Feed instances based on the ultimate `rss`
        outlines.
        """

        feeds = []
        for child in elem:
            outline_type = child.get('type')
            if outline_type == 'category':
                feeds.extend(cls._flatten_category(child, category=category))
            elif outline_type == 'rss':
                feeds.append(Feed.from_opml(child, category=category))
            else:
                logger.warning(f'Found outline element of unrecognised type "{outline_type}". Ignoring.')
        return feeds

    @classmethod
    def from_opml(cls, elem: Element) -> FeedCategory:
        category_name = elem.get('text')
        feeds = cls._flatten_category(elem, category=category_name)
        return FeedCategory(category_name, feeds)

    def __iter__(self):
        return iter(self.feeds)

    def __len__(self) -> int:
        return len(self.feeds)

    def __bool__(self) -> bool:
        return bool(self.feeds)

def _category_dict_factory():
    return OrderedDict(((None, FeedCategory()),))

@dataclass
class FeedList:
    """A representation of a list of feeds (optionally sorted into categories)."""

    categories: OrderedDictType[Optional[str], FeedCategory] = field(default_factory=_category_dict_factory)
    title: Optional[str] = None
    date_modified: Optional[datetime] = None
    opml_file: Optional[str] = None

    _urls: Dict[str, Feed] = field(default_factory=dict)

    def __post_init__(self):
        for c in self.categories:
            for f in self.categories[c].feeds:
                self._urls[f.xml_url] = f


    def add_category(self, name: str, overwrite: bool = False):
        if name in self.categories and not overwrite:
            raise CategoryExistsError(f'Category with name "{name}" already exists.')
        self.categories[name] = FeedCategory(name)

    def remove_category(self, name: str):
        self.categories.pop(name)

    def add_feed(self, xml_url: str, feed_name: str, category: Optional[str] = None):
        """Add a feed to the given category.

        :param xml_url: The URL to the XML describing the feed.
        :param feed_name: The name of the feed.
        :param category: The category to which to add the feed. If the
            category does not already exist, it will be created.

        """
        if not category in self.categories:
            self.add_category(category)
        self.categories[category].add_feed(Feed(xml_url, feed_name, category))

    def remove_feeds(self, feed_url: Optional[str] = WILDCARD, feed_title: Optional[str] = WILDCARD,
                     category: Optional[str] = WILDCARD) -> int:
        """Remove all feeds matching the given title, URL and category.

        :param feed_url: URL of feed to remove.
        :param feed_title: Title of feed to remove.
        :param category: Category of feed to remove.
        :return: The total number of feeds removed.

        """
        query = FeedSearch(feed_title, feed_url, category)
        logger.debug(f'Deleting feeds matching {query}')
        empty_categories = []
        if category is not WILDCARD:
            to_search = [category]
        else:
            to_search = self.categories
        removed = 0
        for category in to_search:
            #logger.debug(f'Removing matching feeds from {category}.')
            removed += self.categories[category].remove_feeds(query)
            #logger.debug(f'Size of category is not {len(self.feeds[category])}')
            if (not self.categories[category]) and (category is not None):
                logger.debug(f'Category "{category}" is empty; removing.')
                empty_categories.append(category)
        logger.debug(f'Removed {removed} feeds.')
        for category in empty_categories:
            self.remove_category(category)

        return removed

    @property
    def category_names(self) -> List[Optional[str]]:
        """Names of all categories, in order."""
        return list(self.categories.keys())

    def copy(self) -> FeedList:
        """Return a deepcopy of this instance."""
        return FeedList(
            categories=deepcopy(self.categories),
            title=self.title,
            date_modified=None,
            opml_file=self.opml_file
        )

    def __iter__(self):
        """Iterate through a flattened list of :class:`Feed` objects."""
        for category in self.categories:
            for feed in self.categories[category]:
                yield feed

    def to_opml(self) -> Element:
        """Return the FeedList represented as an ``opml`` XML element.

        :return: An :class:`Element` object representing the FeedList.

        """

        opml = Element('opml', {'version': '1.0'})
        head = Element('head')
        opml.append(head)
        body = Element('body')
        opml.append(body)

        if self.title is not None:
            title = Element('title')
            title.text = self.title
            head.append(title)
        if self.date_modified is not None:
            date_modified = Element('dateModified')
            date_modified.text = format_datetime(self.date_modified)
            head.append(date_modified)

        for category_name in self.categories:
            if category_name is None:
                for feed in self.categories[category_name]:
                    body.append(feed.to_opml())
            else:
                body.append(self.categories[category_name].to_opml())

        return opml

    def to_opml_file(self, fpath: Optional[str] = None):
        etree = ElementTree(self.to_opml())
        etree.write(fpath or self.opml_file)

    def get_feed_by_url(self, url: str) -> Feed:
        return self._urls[url]

    def sort_by_category(self, urls: List[str]) -> OrderedDict[str, List[str]]:
        """Arrange a list of URLs by category.

        :param urls: A list of URLs to sort.
        :return: An ordered mapping of category names to lists of URLs.

        """
        categories = OrderedDict()
        for url in urls:
            feed = self.get_feed_by_url(url)
            c = feed.category
            if c in categories:
                categories[c].append(url)
            else:
                categories[c] = [url]
        return categories

    @property
    def feeds(self) -> List[Feed]:
        """A list of all feeds."""
        return sum([c.feeds for c in self.categories.values()], start=[])


def from_opml(elem: Element, **kwargs) -> FeedList:
    """Generate a :class:`FeedList` instance from an XML ``opml`` element.

    :param elem: An :class:`Element` of type ``opml``.
    :param kwargs: Other keyword arguments to provide to the
        :class:`FeedList` constructor.
    :return: A :class:`FeedList` object of the relevant feeds.

    """

    categories = OrderedDict()
    categories[None] = FeedCategory(None)

    head = elem.find('head')
    if head is not None:
        title_elem = head.find('title')
        if title_elem is not None:
            title = title_elem.text
        else:
            title = None
        date_mod_elem = head.find('dateModified')
        if date_mod_elem is not None:
            date_modified = parsedate_to_datetime(date_mod_elem.text)
        else:
            date_modified = None
    else:
        title = None
        date_modified = None

    body = elem.find('body')
    if body is None:
        raise BadOPMLError('OPML has no `body` element.')

    for child in body:
        outline_type = child.get('type') or 'category'  # Assume element is category element if no type specified
        if outline_type == 'category':
            category = FeedCategory.from_opml(child)
            name = category.name
            if name in categories:
                categories[name].extend(category)
            else:
                categories[name] = category
        elif outline_type == 'rss':
            to_add = Feed.from_opml(child)
            categories[None].add_feed(to_add)
        else:
            logger.warning(f'Found outline element of unrecognised type "{outline_type}". Ignoring.')

    return FeedList(categories=categories, title=title, date_modified=date_modified, **kwargs)

def from_opml_file(fpath: str) -> FeedList:
    """Create a :class:`FeedList` object from an OPML file. If the
    file does not exist, return an empty FeedList object.

    :param fpath: Path to the OPML file.
    :return: A FeedList object containing the feeds in the OPML file,
        or an empty FeedList if the OPML file does not exist.

    """

    try:
        tree = parse(fpath)
        feedlist = from_opml(tree.getroot(), opml_file=fpath)
        logger.info(f'Loaded feed list from OPML file {fpath}.')
        return feedlist
    # Python's standard ElementTree throws a FileNotFoundError
    # here; lxml throws an OSError.
    except (FileNotFoundError, OSError):
        logger.info(f'OPML file not found at "{fpath}"; new file will be created on save.')
        return FeedList()
