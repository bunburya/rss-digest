"""Functions and classes for using the command line interface."""
import argparse

from rss_digest.config import Config
from rss_digest.dao import ProfilesDAO
from rss_digest.exceptions import ProfileNotFoundError
from rss_digest.profile import Profile, ProfileExistsError
from rss_digest.rss_digest import RSSDigest


class CLI:

    def __init__(self, config: Config):
        self.config = config
        self.rss_digest = RSSDigest(config)
        self.profiles_dao = ProfilesDAO(config)

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
            for c in feedlist.categories:
                print(f' Category: {c.name}')
                for f in c:
                    print(f' Feed: {f.name} ({f.xml_url})')
            print(f'Configuration stored in "{profile.config_dir}".')
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