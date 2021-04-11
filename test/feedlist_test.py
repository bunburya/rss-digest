import dataclasses
import os
import unittest
from typing import Sequence

from rss_digest.exceptions import FeedError
from rss_digest.feedlist import FeedList, from_opml_file

OPML1 = os.path.join('test_data', 'opml', 'own_feeds.opml')
OPML2 = os.path.join('test_data', 'opml', 'InfoSec-RSS-Feeds.opml')
OPML3 = os.path.join('test_data', 'opml', 'feeds.opml')  # No categories

import logging
logging.getLogger().setLevel(logging.DEBUG)

class FeedListTestCase(unittest.TestCase):

    """Tests for FeedList."""

    @classmethod
    def setUpClass(cls):
        cls.feedlist1 = from_opml_file(OPML1)
        cls.feedlist2 = from_opml_file(OPML2)
        cls.feedlist3 = from_opml_file(OPML3)

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

    def test_01_load(self):
        """Test that the OPML files have been loaded successfully."""
        self.assertCategoriesAre(self.feedlist1, [None, 'Economics', 'Law', 'Fitness'])
        self.assertCategoriesAre(self.feedlist2, [None, 'Events', 'Security', 'News', 'Vulnerability', 'Autres',
                                                  'Tech-News', 'Must Read', 'Hacking', 'LEAK + PWN', 'Sec-Tools'])
        self.assertCategoriesAre(self.feedlist3, [None])
        self.assertFeedTitlesAre(self.feedlist1, ['Liberty Street Economics', 'Critical Macro Finance',
                                                  'Bank Underground', 'Musings on Markets', 'CLS Blue Sky Blog',
                                                  'Credit Slips', 'Above the Law', 'The Biglaw Investor',
                                                  'mapmyrun blog - Running', 'Runtastic'])

    def test_02_copy(self):
        """Test copying of FeedCategory and FeedList object."""
        copy1 = self.feedlist1.copy()
        self.assertCategoriesAre(copy1, self.feedlist1.category_names)
        self.assertFeedTitlesAre(copy1, [f.title for f in self.feedlist1])
        copy2 = self.feedlist2.copy()
        self.assertCategoriesAre(copy2, self.feedlist2.category_names)
        self.assertFeedTitlesAre(copy2, [f.title for f in self.feedlist2])
        copy3 = self.feedlist3.copy()
        self.assertCategoriesAre(copy3, self.feedlist3.category_names)
        self.assertFeedTitlesAre(copy3, [f.title for f in self.feedlist3])

    def test_03_eq(self):
        """Test basic equality of feedlists."""
        self.assertNotEqual(self.feedlist1, self.feedlist2)
        copy = self.feedlist1.copy()
        self.assertEqual(self.feedlist1, copy)
        self.assertNotEqual(self.feedlist2, self.feedlist3)
        copy = self.feedlist2.copy()
        self.assertEqual(self.feedlist2, copy)
        self.assertNotEqual(self.feedlist3, self.feedlist1)
        copy = self.feedlist3.copy()
        self.assertEqual(self.feedlist3, copy)

    def test_03_add_feed(self):
        """Test adding of feeds."""
        copy = self.feedlist1.copy()

        # Add to an existing category
        copy.add_feed('CBS Moneywatch', 'http://www.cbsnews.com/latest/rss/moneywatch', category='Economics')
        # Add to no category
        copy.add_feed('CBS Opinion', 'http://www.cbsnews.com/latest/rss/opinion')
        # Add to a new category
        copy.add_feed('CBS News', 'http://www.cbsnews.com/latest/rss/evening-news', category='News')

        self.assertCategoriesAre(copy, [None, 'Economics', 'Law', 'Fitness', 'News'])
        self.assertFeedTitlesAre(copy, ['CBS Opinion', 'Liberty Street Economics', 'Critical Macro Finance',
                                        'Bank Underground', 'Musings on Markets', 'CLS Blue Sky Blog', 'Credit Slips',
                                        'CBS Moneywatch', 'Above the Law', 'The Biglaw Investor',
                                        'mapmyrun blog - Running', 'Runtastic', 'CBS News'])


    def test_04_del_feed(self):
        """Test deletion of feeds."""
        copy = self.feedlist1.copy()
        # Remove by name
        removed = copy.remove_feeds(feed_title='Liberty Street Economics')
        self.assertEqual(removed, 1)
        # Remove by URL
        removed = copy.remove_feeds(feed_url='https://criticalfinance.org/feed/')
        self.assertEqual(removed, 1)
        # Remove entire category
        removed = copy.remove_feeds(category='Fitness')
        self.assertEqual(removed, 2)
        # Try to remove feed that's not there
        removed = copy.remove_feeds(feed_url='blah blah')
        self.assertEqual(removed, 0)
        self.assertCategoriesAre(copy, [None, 'Economics', 'Law'])
        self.assertFeedTitlesAre(copy, ['Bank Underground', 'Musings on Markets', 'CLS Blue Sky Blog', 'Credit Slips',
                                        'Above the Law', 'The Biglaw Investor'])

if __name__ == '__main__':
    unittest.main()
