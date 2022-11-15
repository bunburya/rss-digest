#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import logging

from collections import OrderedDict
from dataclasses import dataclass, field, replace
from datetime import datetime
from email.utils import parsedate_to_datetime, format_datetime
from typing import Optional, List, Union

from rss_digest.exceptions import BadOPMLError, CategoryExistsError

try:
    from lxml.etree import ElementTree, SubElement, Element, parse, tostring

    has_lxml = True
except ImportError:
    logging.warning('lxml not installed.  Using Python\'s standard ElementTree library.  '
                    'Written OPML files will not have pretty formatting.')
    from xml.etree.ElementTree import ElementTree, SubElement, Element, parse, tostring

    has_lxml = False

logger = logging.getLogger(__name__)


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

    name: Optional[str] = WILDCARD
    xml_url: Optional[str] = WILDCARD
    category: Optional[str] = WILDCARD

    def __eq__(self, other):
        return all((
            isinstance(other, Feed),
            self.name == other.title,
            self.xml_url == other.xml_url,
            self.category == other.category
        ))


@dataclass
class Feed:
    """A representation of a single feed."""

    title: str
    xml_url: str
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
            logging.warning('RSS outline element has neither "text" nor "title" attribute.')
            title = ''
        return Feed(title=title, xml_url=attr['xmlUrl'], category=category)


@dataclass
class FeedCategory:
    """A representation of a category of feeds."""

    name: Optional[str]
    feeds: List[Feed] = field(default_factory=list)

    def add_feed(self, feed: Feed, index: Optional[int] = None):
        if index is None:
            self.feeds.append(feed)
        else:
            self.feeds.insert(index, feed)

    def remove_feeds(self, feed: Union[Feed, FeedSearch]) -> int:
        """Remove all feeds matching the given object.

        :param feed: The feed to remove, as a :class:`Feed` or a :class:`FeedSearch`. All feeds which equal the
            ``feed`` object will be removed.
        :return: The number of feeds removed.

        """
        num_feeds = len(self.feeds)
        self.feeds = list(filter(lambda f: f != feed, self.feeds))
        return num_feeds - len(self.feeds)

    def extend(self, other: FeedCategory):
        self.feeds.extend(other.feeds)

    def to_opml(self) -> Element:
        elem = Element('outline', {'type': 'category', 'text': self.name})
        for feed in self.feeds:
            elem.append(feed.to_opml())
        return elem

    def copy(self) -> FeedCategory:
        """Return a deepcopy of this instance."""
        return FeedCategory(
            name=self.name,
            feeds=[replace(f) for f in self.feeds]
        )

    @classmethod
    def _flatten_category_elem(cls, elem: Element) -> List[Feed]:
        """Recursively parse a `category` outline element and return a
        flattened list of Feed instances based on the ultimate `rss`
        outlines.
        """

        feeds = []
        for child in elem:
            outline_type = child.get('type')
            if outline_type == 'category':
                feeds.extend(cls._flatten_category_elem(child))
            elif outline_type == 'rss':
                feeds.append(Feed.from_opml(child))
            else:
                logging.warning(f'Found outline element of unrecognised type "{outline_type}". Ignoring.')
        return feeds

    @classmethod
    def from_opml(cls, elem: Element) -> FeedCategory:
        category_name = elem.get('text')
        feeds = cls._flatten_category_elem(elem)
        return FeedCategory(category_name, feeds)

    def __iter__(self):
        return iter(self.feeds)


@dataclass
class FeedList:
    """A representation of a list of feeds (sorted into categories).

    :param category_dict: An ordered dict mapping category names to :class:`FeedCategory` objects. None is used as a key
        for uncategorised feeds. Where a feed list does not use categories, `feeds` will have a single FeedCategory
        object, with None as the key.
    :param title: The title of the feed list (optional).
    :param date_modified: The date on which the feed list was last modified (optional).
    :param url_to_feed: A dict mapping each feed's URL to the relevant :class:`Feed` object.
    """

    category_dict: OrderedDict[Optional[str], FeedCategory] = field(default_factory=OrderedDict)
    title: Optional[str] = None
    date_modified: Optional[datetime] = None
    url_to_feed: dict[str, Feed] = field(default_factory=dict)

    def __post_init__(self):
        # Move None category to end
        if None in self.category_dict:
            no_category = self.category_dict.pop(None)
            self.category_dict[None] = no_category

    def has_category(self, category: str) -> bool:
        """Check if this feed list has a category of the given name."""
        return category in self.category_dict.keys()

    def add_category(self, name: str, overwrite: bool = False):
        if name in self.category_dict and not overwrite:
            raise CategoryExistsError(f'Category with name "{name}" already exists.')
        self.category_dict[name] = FeedCategory(name)

    def remove_category(self, name: str):
        self.category_dict.pop(name)

    def add_feed(self, feed_name: str, xml_url: str, category: Optional[str] = None):
        """Add a feed to the given category.

        :param feed_name: The name of the feed.
        :param xml_url: The URL to the XML describing the feed.
        :param category: The category to which to add the feed. If the category does not already exist, it will be
            created.

        """
        if category not in self.category_dict:
            self.add_category(category)
        self.category_dict[category].add_feed(Feed(feed_name, xml_url, category))

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
            to_search = self.category_names
        removed = 0
        for category in to_search:
            # logger.debug(f'Removing matching feeds from {category}.')
            removed += self.category_dict[category].remove_feeds(query)
            # logger.debug(f'Size of category is not {len(self.feeds[category])}')
            if (not self.category_dict[category]) and (category is not None):
                logger.debug(f'Category "{category}" is empty; removing.')
                empty_categories.append(category)
        logger.debug(f'Removed {removed} feeds.')
        for category in empty_categories:
            self.remove_category(category)

        return removed

    @property
    def category_names(self) -> List[str]:
        return list(self.category_dict.keys())

    @property
    def categories(self) -> List[FeedCategory]:
        # return list(self.category_dict.values())
        return [self.category_dict[k] for k in self.category_dict]

    def __iter__(self):
        """Iterate through a flattened list of :class:`Feed` objects."""
        for cat in self.category_dict:
            for feed in self.category_dict[cat]:
                yield feed

    def to_opml(self) -> 'Element':
        """Return the FeedList represented as an ``opml`` XML element.

        :return: An :class:`Element` object representing the FeedList."""

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

        for category_name in self.category_dict:
            if category_name is None:
                for feed in self.category_dict[category_name]:
                    body.append(feed.to_opml())
            else:
                body.append(self.category_dict[category_name].to_opml())

        return opml

    def to_opml_file(self, fpath: str):
        etree = ElementTree(self.to_opml())
        if has_lxml:
            etree.write(fpath, pretty_print=True)
        else:
            etree.write(fpath)

    def get_feed_by_url(self, url: str) -> Feed:
        return self.url_to_feed[url]

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
        return sum([c.feeds for c in self.category_dict.values()], start=[])


def parse_opml_elem(elem: Element) -> FeedList:
    """Generate a :class:`FeedList` instance from an XML ``opml`` element.

    :param elem: An :class:`Element` of type ``opml``.
    :return: A :class:`FeedList` object of the relevant feeds.

    """

    feeds = OrderedDict()
    feeds[None] = FeedCategory(None)

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
        outline_type = child.get('type') or 'category'  # Assume element is category element is no type specified
        if outline_type == 'category':
            category = FeedCategory.from_opml(child)
            name = category.name
            if name in feeds:
                feeds[name].extend(category)
            else:
                feeds[name] = category
        elif outline_type == 'rss':
            feeds[None].add_feed(Feed.from_opml(child))
        else:
            logger.warning(f'Found outline element of unrecognised type "{outline_type}". Ignoring.')

    return FeedList(category_dict=feeds, title=title, date_modified=date_modified)


def parse_opml_file(fpath: str) -> FeedList:
    """Parse the OPML file located at `fpath` and return a :class:`FeedList` object.

    :param fpath: The path to the OPML file to parse.
    :return: A :class:`FeedList` object containing the relevant feeds.
    :raises FileNotFoundError: The OPML file cannot be found.
    :raises BadOPMLError: The given file is not an OPML or contains invalid OPML.

    """
    try:
        tree = parse(fpath)
        feedlist = parse_opml_elem(tree.getroot())
        logger.info(f'Loaded feed list from OPML file {fpath}.')
        return feedlist
    # Python's standard ElementTree throws a FileNotFoundError
    # here; lxml throws an OSError.
    except (FileNotFoundError, OSError):
        msg = f'OPML file not found at "{fpath}".'
        logger.info(msg)
        raise FileNotFoundError(msg)
