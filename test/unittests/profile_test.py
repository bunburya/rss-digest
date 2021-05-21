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
        shutil.copy('test_data/config/config.ini', self.config.main_config_file)
        shutil.copy('test_data/config/output.ini', self.config.output_config_file)
        self.rss_digest = RSSDigest(self.config)
        self.profile1 = self.rss_digest.add_profile('Test Profile 1')
        shutil.copy('test_data/opml/own_feeds.opml', self.profile1.config.opml_file)
        shutil.copy('test_data/config/config.ini', self.profile1.config.main_config_file)

    def test_01_setup(self):
        """Test that the test class has been set up properly."""

        self.assertSequenceEqual(self.rss_digest.profiles, ['Test Profile 1'])
        self.assertCategoriesAre(self.profile1.feedlist, [None, 'Economics', 'Law', 'Fitness'])
        self.assertFeedTitlesAre(self.profile1.feedlist, ['Liberty Street Economics', 'Critical Macro Finance',
                                                          'Bank Underground', 'Musings on Markets', 'CLS Blue Sky Blog',
                                                          'Credit Slips', 'Above the Law', 'The Biglaw Investor',
                                                          'mapmyrun blog - Running', 'Runtastic'])
        self.assertEqual(self.profile1.config.get_main_config_value('output_method'), 'stdout')

    def test_02_add_remove(self):
        """Test adding and removing profiles."""

        # Add a profile that already exists
        self.assertRaises(ProfileExistsError, lambda: self.rss_digest.add_profile('Test Profile 1'))

        profile2 = self.rss_digest.add_profile('Test Profile 2')
        self.assertSequenceEqual(profile2.feedlist.category_names, [None])







if __name__ == '__main__':
    unittest.main()
