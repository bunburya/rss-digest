"""Classes and functions for use in multiple unit tests."""

import os
import shutil
import unittest
from typing import Sequence

from rss_digest.config import AppConfig
from rss_digest.feedlist import FeedList

TEST_DATA_BASE = 'test_data'
TEST_DIR_BASE = os.path.join(TEST_DATA_BASE, 'run')

DEFAULT_MAIN_CONFIG = os.path.join(TEST_DATA_BASE, 'config', 'config.ini')
DEFAULT_OUTPUT_CONFIG = os.path.join(TEST_DATA_BASE, 'config', 'config.ini')

def get_test_dir(name: str) -> str:
    test_dir = os.path.join(TEST_DIR_BASE, name)
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    return test_dir

def get_test_config(name: str,
                    main_config_file: str = DEFAULT_MAIN_CONFIG,
                    output_config_file: str = DEFAULT_OUTPUT_CONFIG,
                    clean: bool = True,) -> AppConfig:
    test_dir = get_test_dir(name)
    if clean and os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    config_dir = os.path.join(test_dir, 'config')
    data_dir = os.path.join(test_dir, 'data')
    config = AppConfig(config_dir, data_dir, main_config_file, output_config_file)
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
