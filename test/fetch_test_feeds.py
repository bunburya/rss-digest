#!/usr/bin/env python3

"""Fetch all feeds from an OPML list and same them to a given directory
as XML files.

The idea is to do this regularly, to build up a collection of RSS
content over time to assist us with testing rss-digest.

"""
import logging
import os
from datetime import datetime

logging.getLogger().setLevel(logging.INFO)

import requests
from rss_digest.feeds import parse_opml_file, FeedList

def main(content_dir: str, *opml_files: str):
    now_utc = datetime.utcnow()
    today_dir = os.path.join(content_dir, now_utc.strftime('%Y-%m-%d'))
    if not os.path.exists(today_dir):
        os.makedirs(today_dir)
    log_dir = os.path.join(content_dir, 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file = os.path.join(log_dir, now_utc.strftime('%Y-%m-%d.log'))

    #logging.basicConfig(filename=log_file)
    logging.info(f'Fetching RSS feeds at {now_utc:%H:%M:%S UTC on %Y-%m-%d}.')

    for opml_file in opml_files:
        logging.info(f'Checking OPML file {opml_file}')
        feedlist = parse_opml_file(opml_file)
        for feed in feedlist:
            rss_file = os.path.join(today_dir, feed.name.replace('/', '__slash__').replace('.', '__dot__')+'.xml')
            try:
                r = requests.get(feed.xml_url)
                r.raise_for_status()
                logging.info(f'Got RSS for {feed.name} from {feed.xml_url}')
                with open(rss_file, 'w') as f:
                    f.write(r.text)
                    logging.info(f'Saved RSS to {rss_file}')
            except Exception as e:
                logging.error(f'Error fetching RSS for {feed.name}')
                logging.error(e, exc_info=True)

    end_utc = datetime.utcnow()
    logging.info(f'Finished fetching RSS feeds at {end_utc: %H:%M:%S UTC}')

if __name__ == '__main__':
    from sys import argv
    main(*argv[1:])
