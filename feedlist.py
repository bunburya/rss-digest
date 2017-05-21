#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from xml.etree import ElementTree, Element

class NotRSSError(BaseException): pass

class FeedList:
    
    def __init__(self, fpath):
        self.from_opml_file(fpath)
        
    def from_opml_file(self, fpath):
        
        # xml structure:
        # - opml
        #   - head
        #     - title
        #     - date created
        #   - body
        #     - outline (title, type, xmlUrl)
        
        self.feeds = []
        et = ElementTree.parse(fpath)
        opml = et.getroot()
        head = opml.find('head')
        self.title = head.find('title').text
        body = opml.find('title')
        for outline in body:
            self.feeds(self.parse_outline(outline))
            
    def parse_outline(self, outline):
        """Parse an outline element, recursively handling outline
        elements that contain other outline elements, to return a list
        of outlines (or list of lists of outlines, etc)."""
        if outline['type'] == 'rss':
            attribs = outline.attrib
            f = {   'title': attribs.get('text') or attribs.get('title'),
                    'type': attribs['type'],
                    'url': attribs['xmlUrl']
                }
            return f
        else:
            children = []
            for child in outline:
                children.append(self.parse_outline(child))
        
