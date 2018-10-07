#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  test.py

import main, html_generator, feedhandler, feedlist, config, email_handler

app = main.RSSDigest()

def test_run1():
    
    c = config.Profile('test', app)
    f = feedhandler.FeedObjectList(c, 'test')
    f.get_feeds()
    f.save()
    h = html_generator.HTMLGenerator(c)
    html = h.generate_html(f)
    return html

def test_run2():
    
    c = config.Profile(app, 'test')
    f = feedhandler.FeedObjectList(c)
    f.load()
    f.update_feeds()
    h = html_generator.HTMLGenerator(c)
    html = h.generate_html(f)
    #f.save()
    return html

def test_add(name, url):
    c = config.Profile(app, 'test')
    c.load_data()
    c.load_list()
    f = feedhandler.FeedURLList(c)
    f.add_url(url)
    c.save_data()
    c.save_list()
    return c.feedlist

def test_remove(name, url):
    c = config.Profile(app, 'test')
    c.load_data()
    c.load_list()
    f = feedhandler.FeedURLList(c)
    f.remove_url(url)
    c.save_data()
    c.save_list()
    return c.feedlist

def test_email(profile):
    
    c = config.Profile(app, profile)
    f = feedhandler.FeedObjectList(c)
    f.load()
    f.update_feeds()
    h = html_generator.HTMLGenerator(c)
    html = h.generate_html(f)
    e = email_handler.EmailHandler(c)
    e.send_email(html)

if __name__ == '__main__':
    from sys import argv
    cmd = argv[1]
    if cmd == 'run':
        print(test_run2())
    elif cmd == 'add':
        name = argv[2]
        url = argv[3]
        print(test_add(name, url))
    elif cmd == 'remove':
        name = argv[2]
        url = argv[3]
        print(test_remove(name, url))
    elif cmd == 'email':
        profile = argv[2]
        test_email(profile)
