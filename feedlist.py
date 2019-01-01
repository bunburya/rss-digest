#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

from collections import OrderedDict

try:
    from lxml.etree import ElementTree, SubElement, Element, parse, tostring
    has_lxml = True
except ImportError:
    logging.warning('lxml not installed.  Using Python\'s standard ElementTree library.  '
                    'Written OPML files will not have pretty formatting.')
    from xml.etree.ElementTree import ElementTree, SubElement, Element, parse, tostring
    has_lxml = False

class FeedURLList:
    
    # How we maintain feeds and categories is as follows:
    # - self.feeds is a flat list of feeds.
    # - self.categories is an OrderedDict mapping each category name
    #   to a list of feeds under that category.
    # - When parsing from an OPML file, each feed is added to self.feeds.
    #   If that feed is found within a category, it is given a 'category'
    #   attribute, and is also added to the relevant entry in
    #   self.categories.
    # - When saving to an OPML file, we check if each feed belongs to a
    #   category.  If so, we create an outline element for that category
    #   (if one doesn't already exist) and then add the outline element
    #   for the feed to that category element.
    
    def __init__(self, fpath=None):
        self.categories = OrderedDict()
        if fpath:
            try:
                self.from_opml_file(fpath)
                logging.info('Loaded feedlist from OPML file %s.', fpath)

            # Python's standard ElementTree throws a FileNotFoundError
            # here; lxml throws an OSError.
            except (FileNotFoundError, OSError):
                logging.info('OPML file not found at %s; creating.', fpath)
                self.create_opml_file(fpath)
    
    def _parse_rss_outline_elem(self, elem, category=None):
        attr = elem.attrib
        f = {k: attr[k] for k in attr}
        _type = f.pop('type')
        xmlUrl = f.pop('xmlUrl')
        # In at least one OPML file, I've seen a title attribute where
        # a text attribute should be, so if there's no title attribute,
        # we copy the text attribute over
        if 'text' in f:
            text = f.pop('text')
        elif 'title' in f:
            text = f['title']
        feed = self.append_feed(_type, text, xmlUrl, category=category, **f)
        if category is not None:
            if category in self.categories:
                self.categories[category].append(feed)
            else:
                self.categories[category] = [feed]
        return feed
    
    def _parse_outline_elem(self, elem, category=None):
        tag = elem.tag
        if tag != 'outline':
            logging.warning('Found element of type %s.  Skipping.', tag)
            return
        attr = elem.attrib
        if category is None:
            if attr['type'] == 'category':
                # We are in a top-level category.
                self.categories[attr['text']] = []
                for outline in elem:
                    self._parse_outline_elem(outline, attr['text'])
            elif attr['type'] == 'rss':
                # We are in a top-level RSS feed (no category).
                self._parse_rss_outline_elem(elem)
            else:
                # We are in a top-level outline element that is not of
                # type 'rss' or 'category'.
                logging.warning('Found outline element with type %s. Skipping.',
                                attr['type'])
        else:
            if attr['type'] == 'category':
                # We are in a category inside another category. We ignore
                # nested categories, so add any RSS feeds in this sub-
                # category under the parent category.
                logging.warning('Found category %s inside category %s.  '
                    'Ignoring nested category.', attr['text'], category)
                for outline in elem:
                    self._parse_rss_outline_elem(outline, category=category)
            elif attr['type'] == 'rss':
                # We are in an RSS feed inside a category.
                self._parse_rss_outline_elem(elem, category=category)
            else:
                # We are in an outline element within a category that is
                # not of type 'rss' or 'category'.
                logging.warning('Found outline element with type %s. Skipping.',
                                attr['type'])

    def from_opml_file(self, fpath):
        
        # xml structure:
        # - opml
        #   - head
        #     - title
        #     - date created
        #   - body
        #     - outline (title, type, xmlUrl, category)
                
        self.feeds = []
        et = parse(fpath)
        opml = et.getroot()
        self.version = opml.get('version')
        head = opml.find('head')
        try:
            self.title = head.find('title').text
        except AttributeError:
            pass
        body = opml.find('body')
        for outline in body:
            self._parse_outline_elem(outline)
            
    def to_opml(self, fpath=None):
        opml = Element('opml')
        opml.set('version', self.version)
        head = SubElement(opml, 'head')
        try:
            if self.title:
                title = SubElement(head, 'title')
                title.text = self.title
        except AttributeError:
            pass
        body = SubElement(opml, 'body')
        category_elems = {}
        for c in self.categories:
            c_elem = SubElement(body, 'outline')
            c_elem.set('type', 'category')
            c_elem.set('text', c)
            category_elems[c] = c_elem
        #print(self.feeds)
        for f in self.feeds:
            category = f.pop('category', None)
            if category:
                parent_elem = category_elems[category]
            else:
                parent_elem = body
            f_elem = SubElement(parent_elem, 'outline')
            for k in f:
                f_elem.set(k, f[k])
        if fpath is None:
            return tostring(opml)
        else:
            tree = ElementTree(opml)
            if has_lxml:
                tree.write(fpath, encoding='utf-8',
                    xml_declaration=True, pretty_print=True)
            else:
                tree.write(fpath, encoding='utf-8', xml_declaration=True)
    
    def create_opml_file(self, fpath=None, name=None):
        # TODO: move template to another file
        self.feeds = []
        self.version = '2.0'
        if name:
            self.title = 'RSSDigest feed list for profile {}'.format(name)
        else:
            self.title = None
        self.to_opml(fpath)
    
    def insert_feed(self, i, _type, text, xmlUrl, **other):
        """Insert a new feed at index i."""
        f = other
        f['type'] = _type
        f['text'] = text
        f['xmlUrl'] = xmlUrl
        cat = f.get('category')
        if not 'title' in f:
            f['title'] = text
        self.feeds.insert(i, f)
        if cat is not None:
            if cat in self.categories:
                self.categories[cat].append(f)
            else:
                self.categories[cat] = [f]
        return f
    
    def append_feed(self, *args, **kwargs):
        """Append a new feed to the end of the list.  Takes all the same
        args as insert_feed, except the first one (index)."""
        return self.insert_feed(-1, *args, **kwargs)
    
    def remove_feed(self, i=None, title=None, url=None):
        """Remove a feed, specified by index, title OR url."""
        removed = None
        if i is not None:
            removed = self.feeds.pop(i)
        else:
            if title is not None:
                attr = 'text'
                match = title
            else:
                attr = 'xmlUrl'
                match = url
            for i, f in enumerate(self.feeds):
                if f[attr] == match:
                    removed = self.feeds.pop(i)
                    break
        if removed is not None:
            cat = removed['category']
            if removed in self.categories[cat]:
                self.categories[cat].remove(removed)
                if not self.categories[cat]:
                    self.categories.pop(cat)
    
    def get_categories(self):
        for c in self.categories:
            yield c
    
    def __iter__(self):
        self._i = -1
        return self
    
    def __next__(self):
        self._i += 1
        try:
            return self.feeds[self._i]
        except IndexError:
            raise StopIteration
