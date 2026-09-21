import shutil
import unittest

from rss_digest.exceptions import ProfileExistsError
from rss_digest.rss_digest import RSSDigest
from test.unittests._base import RSSDigestTestCaseBase, get_test_config


class ProfilesTestCase(RSSDigestTestCaseBase):
    """Tests for managing profiles."""

    @classmethod
    def setUpClass(self):
        self.config = get_test_config('profile_test')
        shutil.copy('test/test_data/config/config.ini', self.config.config_dir)
        shutil.copy('test/test_data/config/output.ini', self.config.config_dir)
        self.rss_digest = RSSDigest(self.config)
        self.profile1 = self.rss_digest.add_profile('Test Profile 1')
        shutil.copy('test/test_data/opml/feeds.opml', self.profile1.opml_file)
        shutil.copy('test/test_data/config/config.ini', self.profile1.config_file)

    def test_01_setup(self):
        """Test that the test class has been set up properly."""

        self.assertSetEqual(set(self.rss_digest.profiles), {'Test Profile 1'})
        self.assertCategoriesAre(self.profile1.feedlist, ["Economics", "Art and Culture", "Tech", None])
        self.assertFeedTitlesAre(self.profile1.feedlist, [
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
        ])

    def test_02_add_remove(self):
        """Test adding and removing profiles."""

        # Add a profile that already exists
        self.assertRaises(ProfileExistsError, lambda: self.rss_digest.add_profile('Test Profile 1'))

        profile2 = self.rss_digest.add_profile('New Test Profile')
        self.assertSequenceEqual(profile2.feedlist.category_names, [])
        self.assertSetEqual(set(self.rss_digest.profiles), {'Test Profile 1', 'New Test Profile'})

        self.rss_digest.delete_profile('New Test Profile')
        self.assertSetEqual(set(self.rss_digest.profiles), {'Test Profile 1'})

if __name__ == '__main__':
    unittest.main()
