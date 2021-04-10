"""Functions and classes for using the command line interface."""
import sys
import argparse
from typing import Optional

from rss_digest.config import Config
from rss_digest.dao import ProfilesDAO
from rss_digest.exceptions import ProfileNotFoundError
from rss_digest.profile import Profile, ProfileExistsError
from rss_digest.rss_digest import RSSDigest

def err(msg: str):
    """Print a message to standard error.

    :param msg: The message to print.

    """
    print(msg, file=sys.stderr)

class CLI:

    def __init__(self, config: Optional[Config] = None):
        if config is None:
            self.config = Config()
        else:
            self.config = config
        self.rss_digest = RSSDigest(self.config)
        self.profiles_dao = self.rss_digest.profiles_dao

    def list_profiles(self, args: argparse.Namespace):
        print('Available profiles:')
        for p in self.rss_digest.profiles:
            print(f' {p}')

    def add_profile(self, args: argparse.Namespace):
        try:
            self.rss_digest.add_profile(args.profile_name, args.email, args.user_name)
            print(f'Profile "{args.profile_name}" added. Now add some feeds.')
        except ProfileExistsError:
            print(f'Profile "{args.profile_name}" already exists.')

    def view_profile(self, args: argparse.Namespace):
        try:
            profile = self.rss_digest.get_profile(args.profile_name)
            print(f'Profile name: {profile.profile_name}')
            print(f'Email: {profile.email}')
            print(f'User name: {profile.user_name}')
            feedlist = self.rss_digest.get_feedlist(profile)
            print('Subscribed feeds:')
            for category, feeds in feedlist.iter_categories:
                print(f' Category: {category}')
                for feed in feeds:
                    print(f'  Feed: {feed["text"]} ({feed["xmlUrl"]})')
            print(f'Configuration stored in "{profile.profile_dir}".')
        except ProfileNotFoundError:
            print(f'Profile "{args.profile_name}" not found.')

    def edit_profile(self, args: argparse.Namespace):
        try:
            self.rss_digest.edit_profile(args.profile_name, email=args.email, user_name=args.user_name)
            print(f'Profile "{args.profile_name}" edited.')
        except ProfileNotFoundError:
            print(f'Profile "{args.profile_name}" not found.')

    def delete_profile(self, args: argparse.Namespace):
        try:
            self.rss_digest.delete_profile(args.profile_name)
            print(f'Profile "{args.profile_name}" deleted.')
        except ProfileNotFoundError:
            print(f'Profile "{args.profile_name}" not found.')

    def add_feed(self, args: argparse.Namespace):
        """Add a new feed."""
        pass

    def view_feeds(self, args: argparse.Namespace):
        """View all of the given profile's feeds."""
        pass

    def delete_feed(self, args: argparse.Namespace):
        """Delete the given feed."""
        pass

    def run(self, args: argparse.Namespace):
        """Run rss-digest for the given profile, fetching updates for
        each feed and generating a digest.

        """
        pass