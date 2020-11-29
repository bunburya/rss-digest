import dataclasses
import os
import unittest

from rss_digest.feedlist import FeedList

OPML1 = os.path.join('test_data', 'opml', 'feeds.opml')
OPML2 = os.path.join('test_data', 'opml', 'feeds2.opml')


class FeedListTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.feedlist1 = FeedList.from_opml_file(OPML1)
        cls.feedlist2 = FeedList.from_opml_file(OPML2)

    def test_01_load(self):
        """Test that the OPML files have been loaded successfully."""
        self.assertSequenceEqual(self.feedlist1.category_names, [None, 'Economics', 'Spanish'])
        self.assertSequenceEqual(self.feedlist2.category_names, [None, 'Economics', 'Law', 'Fitness'])
        feednames1 = [f.name for f in self.feedlist1]
        self.assertSequenceEqual(feednames1, ['BBC Academy', 'Naked Capitalism', 'Bank Underground', 'El Blog Salmón'])

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
        self.assertSequenceEqual(self.feedlist1.category_names, [None, 'Economics', 'Spanish', 'Law'])
        feednames1 = [f.name for f in self.feedlist1]
        self.assertSequenceEqual(feednames1, ['BBC Academy', 'Runtastic', 'Naked Capitalism', 'Bank Underground',
                                              'Liberty Street Economics', 'El Blog Salmón', 'Above the Law'])

if __name__ == '__main__':
    unittest.main()
