import os
import unittest

from rss_digest.exceptions import FeedExistsError
from rss_digest.feeds import parse_opml_file
from test.unittests._base import RSSDigestTestCaseBase

FEEDS_CAT = os.path.join('test', 'test_data', 'opml', 'feeds.opml')
FEEDS_NO_CAT = os.path.join('test', 'test_data', 'opml', 'feeds_no_cat.opml')
MORE_FEEDS = os.path.join('test', 'test_data', 'opml', 'feeds2.opml')

import logging

logging.getLogger().setLevel(logging.DEBUG)


class FeedListTestCase(RSSDigestTestCaseBase):
    """Tests for FeedList."""

    @classmethod
    def setUpClass(cls):
        cls.feedlist1 = parse_opml_file(FEEDS_CAT)
        cls.feedlist2 = parse_opml_file(FEEDS_NO_CAT)
        cls.feedlist3 = parse_opml_file(MORE_FEEDS)

        cls.titles = [
            "Bank Underground",
            "CLS Blue Sky Blog",
            "Critical Macro Finance",
            "Liberty Street Economics",
            "Musings on Markets",
            "Bits about Money",
            "Credit Slips",
            "The Tontine Coffee-House",
            "Open Culture",
            "Books | The Guardian",
            "The Marginalian",
            "The Collector",
            "Literary  Hub",
            "Hackaday",
            "IEEE Spectrum",
            "computers are bad",
            "Krebs on Security",
            "LWN",
            "Liliputing",
            "lcamtuf’s thing",
            "Aeon | a world of ideas",
            "Atlas Obscura - Latest Articles and Places",
            "Bartosz Ciechanowski"
        ]

    def test_01_load(self):
        """Test that the OPML files have been loaded successfully."""
        self.assertCategoriesAre(self.feedlist1, ["Economics", "Art and Culture", "Tech", None])
        self.assertCategoriesAre(self.feedlist2, [None])
        self.assertCategoriesAre(self.feedlist3, ["Reddit", None])

        self.assertFeedTitlesAre(self.feedlist1, self.titles)
        self.assertFeedTitlesAre(self.feedlist2, self.titles)
        self.assertFeedTitlesAre(self.feedlist3, ["RSS Subreddit", "AITA Subreddit", "Selfhosted Subreddit"])

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

    def test_04_add_feed(self):
        """Test adding of feeds."""
        copy = self.feedlist1.copy()

        # Add to an existing category
        copy.add_feed("CBS Moneywatch", "https://www.cbsnews.com/latest/rss/moneywatch", category="Economics")
        # Add to no category
        copy.add_feed("CBS Opinion", "https://www.cbsnews.com/latest/rss/opinion")
        # Add to a new category
        copy.add_feed("CBS News", "https://www.cbsnews.com/latest/rss/evening-news", category="News")

        self.assertRaises(
            FeedExistsError,
            lambda: copy.add_feed("CBS News Again", "https://www.cbsnews.com/latest/rss/evening-news", category="News")
        )

        self.assertCategoriesAre(copy, ["Economics", "Art and Culture", "Tech", None, "News"])
        self.assertFeedTitlesAre(copy, self.titles + ["CBS Moneywatch", "CBS Opinion", "CBS News"])

    def test_05_del_feed(self):
        """Test deletion of feeds."""
        copy = self.feedlist1.copy()
        # Remove by name
        removed = copy.remove_feeds(feed_title="Liberty Street Economics")
        self.assertEqual(1, removed)
        # Remove by URL
        removed = copy.remove_feeds(feed_url="https://criticalfinance.org/feed/")
        self.assertEqual(1, removed)
        # Remove entire category
        removed = copy.remove_feeds(category="Art and Culture")
        self.assertEqual(5, removed)
        # Try to remove feed that's not there
        removed = copy.remove_feeds(feed_url="blah blah")
        self.assertEqual(0, removed)
        self.assertCategoriesAre(copy, ["Economics", "Tech", None])
        new_titles = [
            "Bank Underground",
            "CLS Blue Sky Blog",
            "Musings on Markets",
            "Bits about Money",
            "Credit Slips",
            "The Tontine Coffee-House",
            "Hackaday",
            "IEEE Spectrum",
            "computers are bad",
            "Krebs on Security",
            "LWN",
            "Liliputing",
            "lcamtuf’s thing",
            "Aeon | a world of ideas",
            "Atlas Obscura - Latest Articles and Places",
            "Bartosz Ciechanowski"
        ]
        self.assertFeedTitlesAre(copy, new_titles)


if __name__ == '__main__':
    unittest.main()
