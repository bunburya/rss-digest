import dataclasses
import os
import unittest
from typing import Sequence

from rss_digest.feedlist import FeedList

OPML1 = os.path.join('test_data', 'opml.old', 'feeds.opml.old')
OPML2 = os.path.join('test_data', 'opml.old', 'feeds2.opml.old')


class FeedListTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.feedlist1 = FeedList.from_opml_file(OPML1)
        cls.feedlist2 = FeedList.from_opml_file(OPML2)

    def assertFeedsAre(self, feedlist: FeedList, feeds: Sequence):
        feednames = [f.name for f in feedlist]
        self.assertSequenceEqual(feednames, feeds)

    def assertCategoriesAre(self, feedlist: FeedList, categories: Sequence):
        self.assertSequenceEqual(feedlist.category_names, categories)

    def test_01_load(self):
        """Test that the OPML files have been loaded successfully."""
        self.assertCategoriesAre(self.feedlist1, [None, 'Economics', 'Spanish'])
        self.assertCategoriesAre(self.feedlist2, [None, 'Economics', 'Law', 'Fitness'])
        self.assertFeedsAre(self.feedlist1, ['BBC Academy', 'Naked Capitalism', 'Bank Underground', 'El Blog Salmón'])

    def test_02_eq(self):
        """Test basic equality of feeds."""
        self.assertNotEqual(self.feedlist1, self.feedlist2)
        copy = dataclasses.replace(self.feedlist1)
        self.assertEqual(self.feedlist1, copy)

    def test_03_add_feed(self):
        """Test adding of feeds."""
        # Add to an existing category
        self.feedlist1.add_feed('Liberty Street Economics', 'http://feeds.feedburner.com/LibertyStreetEconomics',
                                category='Economics')
        # Add to no category
        self.feedlist1.add_feed('Runtastic', 'https://www.runtastic.com/blog/en/feed')
        # Add to a new category
        self.feedlist1.add_feed('Above the Law', 'https://abovethelaw.com/feed/',
                                category='Law')
        self.assertCategoriesAre(self.feedlist1, [None, 'Economics', 'Spanish', 'Law'])
        self.assertFeedsAre(self.feedlist1, ['BBC Academy', 'Runtastic', 'Naked Capitalism', 'Bank Underground',
                                             'Liberty Street Economics', 'El Blog Salmón', 'Above the Law'])

    def test_03_del_feed(self):
        """Test deletion of feeds."""
        # Remove by name
        self.feedlist2.remove_feed(feed_name='Liberty Street Economics')
        # Remove by URL
        self.feedlist2.remove_feed(xml_url='https://criticalfinance.org/feed/')
        # Remove by

if __name__ == '__main__':
    unittest.main()
