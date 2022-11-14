import shutil
import unittest

from rss_digest.exceptions import ProfileExistsError
from rss_digest.rss_digest import RSSDigest
from test._base import RSSDigestTestCaseBase, get_test_config


class ProfilesTestCase(RSSDigestTestCaseBase):
    """Tests for managing profiles."""

    @classmethod
    def setUpClass(cls):
        config = get_test_config('profile_test')
        rss_digest = RSSDigest(config)
        profile1 = rss_digest.add_profile('Test Profile 1')
        shutil.copy('test_data/opml/own_feeds_no_category.opml', profile1.opml_file)
        cls.config = config
        cls.rss_digest = rss_digest
        cls.profile1 = profile1
        #self.profile2 = self.rss_digest.add_profile('Test Profile 2')
        #shutil.copy('test_data/opml/own_feeds_no_category.opml', self.profile2.config.opml_file)
        #shutil.copy('test_data/config/config.ini', self.profile2.config.main_config_file)

    def test_01_setup(self):
        """Test that the test class has been set up properly."""

        self.assertSetEqual(set(self.rss_digest.profiles), {'Test Profile 1'})
        self.assertCategoriesAre(self.profile1.feedlist, [None])
        self.assertFeedTitlesAre(self.profile1.feedlist, ['Liberty Street Economics', 'Critical Macro Finance',
                                                          'Bank Underground', 'Musings on Markets', 'CLS Blue Sky Blog',
                                                          'Credit Slips', 'Above the Law', 'The Biglaw Investor',
                                                          'mapmyrun blog - Running', 'Runtastic'])
        self.assertEqual(self.profile1.config['delivery_method'], 'sendmail_output')

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
