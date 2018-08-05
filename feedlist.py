#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from xml.etree.ElementTree import ElementTree, SubElement, Element, parse, tostring

class FeedURLList:
    
    def __init__(self, fpath=None):
        self.categories = {}
        if fpath:
            self.from_opml_file(fpath)
        
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
        self.title = head.find('title').text
        body = opml.find('body')
        for outline in body:
            attr = outline.attrib
            f = {k: attr[k] for k in attr}
            _type = f.pop('type')
            xmlUrl = f.pop('xmlUrl')
            category = f.pop('category', None)
            # In at least one OPML file, I've seen a title attribute where
            # a text attribute should be, so if there's no title attribute,
            # we copy the text attribute over
            if 'text' in f:
                text = f.pop('text')
            elif 'title' in f:
                text = f['title']
            self.append_feed(_type, text, xmlUrl, **f)
            
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
        cat = f.get('category')
        f['category'] = cat
        if not 'title' in f:
            f['title'] = text
        self.feeds.insert(i, f)
        if cat in self.categories:
            self.categories[cat].append(f)
        else:
            self.categories[cat] = [f]
    
    def append_feed(self, *args, **kwargs):
        """Append a new feed to the end of the list.  Takes all the same
        args as insert_feed, except the first one (index)."""
        self.insert_feed(-1, *args, **kwargs)
    
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
    
    def get_categories(self):
        for c in self.categories:
            yield c
    
    def __iter__(self):
        self._i = -1
        return self
    
    def __next__(self):
        self._i += 1
        return self.feeds[self._i]
