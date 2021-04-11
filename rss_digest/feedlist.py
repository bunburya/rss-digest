#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import logging
import os

from collections import OrderedDict
from dataclasses import dataclass, field, replace
from datetime import datetime
from email.utils import parsedate_to_datetime, format_datetime
from typing import Optional, List, Generator, Tuple, OrderedDict as OrderedDictType, Any, Union

from rss_digest.exceptions import FeedNotFoundError, BadOPMLError, CategoryExistsError
from rss_digest.profile import Profile

try:
    from lxml.etree import ElementTree, SubElement, Element, parse, tostring

    has_lxml = True
except ImportError:
    logging.warning('lxml not installed.  Using Python\'s standard ElementTree library.  '
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

    name: Optional[str] = None
    feeds: List[Feed] = field(default_factory=list)

    def add_feed(self, feed: Feed, index: Optional[int] = None):
        if index is None:
            self.feeds.append(feed)
        else:
            self.feeds.insert(index, feed)

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
        self.feeds = list(filter(feed.__eq__, self.feeds))
        return len(self.feeds) - num_feeds

    def copy(self) -> FeedCategory:
        """Return a deepcopy of this instance."""
        return FeedCategory(
            name=self.name,
            feeds=[replace(f) for f in self.feeds]
        )

    @classmethod
    def _flatten_category(cls, elem: Element) -> List[Feed]:
        """Recursively parse a `category` outline element and return a
        flattened list of Feed instances based on the ultimate `rss`
        outlines.
        """

        feeds = []
        for child in elem:
            outline_type = child.get('type')
            if outline_type == 'category':
                feeds.extend(cls._flatten_category(child))
            elif outline_type == 'rss':
                feeds.append(Feed.from_opml(child))
            else:
                logging.warning(f'Found outline element of unrecognised type "{outline_type}". Ignoring.')
        return feeds

    @classmethod
    def from_opml(cls, elem: Element) -> FeedCategory:
        category_name = elem.get('text')
        feeds = cls._flatten_category(elem)
        return FeedCategory(category_name, feeds)

    def __iter__(self):
        return iter(self.feeds)


@dataclass
class FeedList:
    """A representation of a list of feeds (optionally sorted into categories)."""

    feeds: OrderedDictType[Optional[str], FeedCategory]
    title: Optional[str] = None
    date_modified: Optional[datetime] = None
    opml_file: Optional[str] = None

    def add_category(self, name: str, overwrite: bool = False):
        if name in self.feeds and not overwrite:
            raise CategoryExistsError(f'Category with name "{name}" already exists.')
        self.feeds[name] = FeedCategory(name)

    def remove_category(self, name: str):
        self.feeds.pop(name)

    def add_feed(self, feed_name: str, xml_url: str, category: Optional[str] = None):
        if not category in self.feeds:
            self.add_category(category)
        self.feeds[category].add_feed(Feed(feed_name, xml_url, category))

    def remove_feeds(self, feed_title: Optional[str] = WILDCARD, feed_url: Optional[str] = WILDCARD,
                    category: Optional[str] = WILDCARD) -> int:
        """Remove all feeds matching the given title, URL and category.

        :param feed_title: Title of feed to remove.
        :param feed_url: URL of feed to remove.
        :param category: Category of feed to remove.
        :return: The total number of feeds removed.

        """
        query = FeedSearch(feed_title, feed_url, category)
        logging.debug(f'Deleting feeds matching {query}')
        empty_categories = []
        if category is not WILDCARD:
            to_search = [category]
        else:
            to_search = self.feeds
        removed = 0
        for category in to_search:
            removed += self.feeds[category].remove_feeds(query)
            if not self.feeds[category]:
                empty_categories.append(category)
        logging.debug(f'Removed {removed} feeds.')
        for category in empty_categories:
            logging.debug(f'Category "{category}" is empty; removing.')
            self.remove_category(category)

        return removed

    @property
    def category_names(self) -> List[str]:
        return list(self.feeds.keys())

    def categories(self) -> List[FeedCategory]:
        return list(self.feeds.values())

    def copy(self) -> FeedList:
        """Return a deepcopy of this instance."""
        return FeedList(
            feeds=OrderedDict((name, self.feeds[name].copy()) for name in self.feeds),
            title=self.title,
            date_modified=None,
            opml_file=self.opml_file
        )

    def __iter__(self):
        """Iterate through a flattened list of :class:`Feed` objects."""
        for category in self.feeds:
            for feed in self.feeds[category]:
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

        for category_name in self.feeds:
            if category_name is None:
                for feed in self.feeds[category_name]:
                    body.append(feed.to_opml())
            else:
                body.append(self.feeds[category_name].to_opml())

        return opml

    def to_opml_file(self, fpath: Optional[str] = None):
        etree = ElementTree(self.to_opml())
        etree.write(fpath or self.opml_file)


def from_opml(elem: Element, **kwargs) -> FeedList:
    """Generate a :class:`FeedList` instance from an XML ``opml`` element.

    :param elem: An :class:`Element` of type ``opml``.
    :param kwargs: Other keyword arguments to provide to the
        :class:`FeedList` constructor.
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
        outline_type = child.get('type') or 'category'  # Assume element is category element if no type specified
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
            logging.warning(f'Found outline element of unrecognised type "{outline_type}". Ignoring.')

    return FeedList(feeds=feeds, title=title, date_modified=date_modified, **kwargs)

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
        logging.info(f'Loaded feed list from OPML file {fpath}.')
        return feedlist
    # Python's standard ElementTree throws a FileNotFoundError
    # here; lxml throws an OSError.
    except (FileNotFoundError, OSError):
        logging.info(f'OPML file not found at "{fpath}"; new file will be created on save.')
