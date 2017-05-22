#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from xml.etree.ElementTree import ElementTree, SubElement, Element, parse, tostring

import feedparser

class FeedList:
        
    def from_opml_file(self, fpath):
        
        # xml structure:
        # - opml
        #   - head
        #     - title
        #     - date created
        #   - body
        #     - outline (title, type, xmlUrl)
        
        self.feeds = []
        et = parse(fpath)
        opml = et.getroot()
        self.version = opml.get('version')
        head = opml.find('head')
        self.title = head.find('title').text
        body = opml.find('body')
        for outline in body:
            attr = outline.attrib
            f = {k: attr[k] for k in attr}
            # In at least one OPML file, I've seen a title attribute where
            # a text attribute should be, so if there's no title attribute,
            # we copy the text attribute over
            if 'text' not in f and 'title' in f:
                f['text'] = f['title']
            self.feeds.append(f)
            
    def to_opml(self, fpath=None):
        opml = Element('opml')
        opml.set('version', self.version)
        head = SubElement(opml, 'head')
        
        title = SubElement(head, 'title')
        title.text = self.title
        body = SubElement(opml, 'body')
        for f in self.feeds:
            f_elem = SubElement(body, 'outline')
            for k in f:
                f_elem.set(k, f[k])
        if fpath is None:
            return tostring(opml)
        else:
            tree = ElementTree(opml)
            tree.write(fpath, encoding='utf-8', xml_declaration=True)
    
    def insert_feed(self, i, _type, text, xmlUrl, **other):
        """Insert a new feed at index i."""
        f = other
        f['type'] = _type
        f['text'] = text
        f['xmlUrl'] = xmlUrl
        if not 'title' in f:
            f['title'] = text
        self.feeds.insert(i, f)
    
    def append_feed(self, *args, **kwargs):
        """Append a new feed to the end of the list."""
        self.insert_feed(-1, *args, **kwargs)
    
    def remove_feed(self, i=None, title=None, url=None):
        """Remove a feed, specified by index, title OR url."""
        if i is not None:
            return self.feeds.pop(i)
        else:
            if title is not None:
                attr = 'text'
                match = title
            else:
                attr = 'xmlUrl'
                match = url
            for i, f in enumerate(self.feeds):
                if self.feeds[i][attr] == match:
                    return self.feeds.pop(i)
    
    def __iter__(self):
        self._i = -1
    
    def __next__(self):
        self._i += 1
        return self.feeds[self._i]
