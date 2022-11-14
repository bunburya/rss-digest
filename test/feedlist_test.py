import dataclasses
import os
import unittest
from typing import Sequence

from rss_digest.feeds import FeedList, parse_opml_file

OPML1 = os.path.join('test_data', 'opml', 'tt-rss_2022-11-08.opml')
OPML1_copy = os.path.join('test_data', 'opml', 'tt-rss_2022-11-08_copy.opml')
OPML1_notcopy = os.path.join('test_data', 'opml', 'tt-rss_2022-11-08_notacopy.opml')


class FeedListTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.feedlist1 = parse_opml_file(OPML1)
        cls.feedlist2 = parse_opml_file(OPML1_copy)
        cls.feedlist3 = parse_opml_file(OPML1_notcopy)

    def assertFeedsAre(self, feedlist: FeedList, feeds: Sequence):
        feednames = [f.name for f in feedlist]
        self.assertSequenceEqual(feednames, feeds)

    def assertCategoriesAre(self, feedlist: FeedList, categories: Sequence):
        self.assertSequenceEqual(feedlist.category_names, categories)

    def test_01_load(self):
        """Test that the OPML files have been loaded successfully."""
        self.assertCategoriesAre(self.feedlist1, [None, 'Art', 'Economics & Law'])
        self.assertFeedsAre(self.feedlist1,
                            ['Bartosz Ciechanowski', 'The Pudding', 'Wait But Why', 'Gwern.net Newsletter',
                             'Maggie Appleton', 'Apollo Magazine', 'Books | The Guardian', 'Bank Underground',
                             'CLS Blue Sky Blog', 'Credit Slips', 'Critical Macro Finance', 'Liberty Street Economics',
                             'Musings on Markets', 'Above the Law'])

    def test_02_eq(self):
        """Test basic equality of feeds."""
        self.assertEqual(self.feedlist1, self.feedlist2)
        copy = dataclasses.replace(self.feedlist1)
        self.assertEqual(self.feedlist1, copy)
        self.assertNotEqual(self.feedlist1, self.feedlist3)

    def test_03_add_feed(self):
        """Test adding of feeds."""
        # Add to an existing category
        self.feedlist1.add_feed('Test Feed 1', 'http://test.example.org/feed1',
                                category='Economics & Law')
        # Add to no category
        self.feedlist1.add_feed('Test Feed 2', 'http://test.example.org/feed2')
        # Add to a new category
        self.feedlist1.add_feed('Test Feed 3', 'http://test.example.org/feed3',
                                category='Test Category')
        self.assertCategoriesAre(self.feedlist1, [None, 'Art', 'Economics & Law', 'Test Category'])
        self.assertFeedsAre(self.feedlist1,
                            ['Bartosz Ciechanowski', 'The Pudding', 'Wait But Why', 'Gwern.net Newsletter',
                             'Maggie Appleton', 'Test Feed 2', 'Apollo Magazine', 'Books | The Guardian',
                             'Bank Underground', 'CLS Blue Sky Blog', 'Credit Slips', 'Critical Macro Finance',
                             'Liberty Street Economics', 'Musings on Markets', 'Above the Law', 'Test Feed 1',
                             'Test Feed 3'])

    def test_04_del_feed(self):
        """Test deletion of feeds."""
        # Remove by name
        self.feedlist2.remove_feeds(feed_title='Liberty Street Economics')
        # Remove by URL
        self.feedlist2.remove_feeds(feed_url='https://criticalfinance.org/feed/')
        self.assertFeedsAre(self.feedlist2,
                            ['Bartosz Ciechanowski', 'The Pudding', 'Wait But Why', 'Gwern.net Newsletter',
                             'Maggie Appleton', 'Apollo Magazine', 'Books | The Guardian', 'Bank Underground',
                             'CLS Blue Sky Blog', 'Credit Slips', 'Musings on Markets', 'Above the Law'])

    def test_05_new_feedlist(self):
        new1 = FeedList()
        self.assertCategoriesAre(new1, [])
        self.assertFeedsAre(new1, [])


if __name__ == '__main__':
    unittest.main()
