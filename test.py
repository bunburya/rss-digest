#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  test.py

import html_generator, feedhandler, config



def test1():
    
    c = config.Config('test')
    f = feedhandler.FeedList(c, 'test')
    f.get_feeds()
    f.save()
    h = html_generator.HTMLGenerator(c)
    html = h.generate_html(f)
    return html

def test2():
    
    c = config.Config('test')
    f = feedhandler.FeedList(c, 'test')
    f.load()
    f.update_feeds()
    h = html_generator.HTMLGenerator(c)
    html = h.generate_html(f)
    #f.save()
    return html

if __name__ == '__main__':
    print(test2())
