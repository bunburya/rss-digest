#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  test.py

import html_generator, feedhandler, config

def test():
    
    c = config.Config('test')
    f = feedhandler.FeedList(c, 'test')
    f.get_feeds()
    h = html_generator.HTMLGenerator(c)
    html = h.generate_html(f)
    return html

if __name__ == '__main__':
    print(test())
