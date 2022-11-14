"""Classes and functions for use in multiple unit tests."""

import os
import shutil
import unittest
from typing import Sequence

import logging

from rss_digest.config import Config
from rss_digest.feeds import FeedList

logging.getLogger().setLevel(logging.DEBUG)

TEST_DATA_BASE = 'test_data'
TEST_DIR_BASE = os.path.join(TEST_DATA_BASE, 'run')

DEFAULT_CONFIG = os.path.join(TEST_DATA_BASE, 'config.toml')


def get_test_dir(name: str) -> str:
    test_dir = os.path.join(TEST_DIR_BASE, name)
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    return test_dir


def get_test_config(name: str, clean: bool = True, ) -> Config:
    test_dir = get_test_dir(name)
    if clean and os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    config_dir = os.path.join(test_dir, 'config')
    data_dir = os.path.join(test_dir, 'data')
    config = Config(config_dir, data_dir)
    shutil.copy(DEFAULT_CONFIG, config.default_config_file)
    return config


class RSSDigestTestCaseBase(unittest.TestCase):

    def assertFeedTitlesAre(self, feedlist: FeedList, feeds: Sequence):
        """Assert that the titles of the feeds in ``feedlist`` are as
         set out in ``feeds``.

         """
        feednames = [f.title for f in feedlist]
        self.assertSequenceEqual(feednames, feeds)

    def assertCategoriesAre(self, feedlist: FeedList, categories: Sequence):
        """Assert that the categories in ``feedlist`` are as set out in
        ``feeds``.

         """
        self.assertSequenceEqual(feedlist.category_names, categories)
