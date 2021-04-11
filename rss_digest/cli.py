"""Functions and classes for using the command line interface."""
import sys
import argparse
from typing import Optional

from rss_digest.config import AppConfig
from rss_digest.exceptions import ProfileNotFoundError, FeedExistsError, FeedError
from rss_digest.profile import ProfileExistsError
from rss_digest.rss_digest import RSSDigest
from rss_digest.metadata import APP_NAME

COMMANDS = [
    'profiles',
    'add-profile',
    'view-profile',
    'edit-profile',
    'delete-profile',
    'add-feed',
    'view-feeds',
    'delete-feed'
    'run'
]

OUTPUT_METHODS = [
    'stdout',
    'smtp',
    'file'
]

def err(msg: str):
    """Print a message to standard error.

    :param msg: The message to print.

    """
    print(msg, file=sys.stderr)

class CLI:

    def __init__(self, config: Optional[AppConfig] = None):
        if config is None:
            self.config = AppConfig()
        else:
            self.config = config
        self.rss_digest = RSSDigest(self.config)
        self.profiles_dao = self.rss_digest.profiles_dao

    def list_profiles(self, args: argparse.Namespace):
        print('Available profiles:')
        for p in self.rss_digest.profiles:
            print(f'  {p}')

    def add_profile(self, args: argparse.Namespace):
        try:
            self.rss_digest.add_profile(args.profile_name)
            err(f'Profile "{args.profile_name}" added.')
            err('Now add some feeds and configure as necessary.')
        except ProfileExistsError:
            err(f'Profile "{args.profile_name}" already exists.')

    def delete_profile(self, args: argparse.Namespace):
        try:
            self.rss_digest.delete_profile(args.profile_name)
            err(f'Profile "{args.profile_name}" deleted.')
        except ProfileNotFoundError:
            err(f'Profile "{args.profile_name}" not found.')

    def add_feed(self, args: argparse.Namespace):
        """Add a new feed."""
        try:
            self.rss_digest.add_feed(
                args.profile_name,
                args.feed_url,
                args.feed_title,
                args.category,
                args.test_feed,
                args.mark_read,
                args.fetch_title
            )
            err('Feed added.')
        except FeedError as e:
            err(f'Received error adding feed: {str(e) or type(e)}')

    def view_feeds(self, args: argparse.Namespace):
        """View all of the given profile's feeds."""
        name = args.profile_name
        feedlist = self.rss_digest.get_profile_feedlist(name)
        print(f'Feeds for {name}:')
        for feed in feedlist:
            print(f'  {feed.title} (URL: {feed.xml_url}, category: {feed.category}')

    def delete_feed(self, args: argparse.Namespace):
        """Delete the given feed."""
        deleted = self.rss_digest.delete_feeds(args.profile_name, feed_url=args.url)
        if not deleted:
            err(f'Could not find feed with URL {args.url} to delete.')
        else:
            err(f'Deleted {deleted} feeds with URL {args.url}.')

    def run(self, args: argparse.Namespace):
        """Run rss-digest for the given profile, fetching updates for
        each feed and generating a digest.

        """
        pass


def get_arg_parser(cli: CLI) -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(description='Produce a digest of subscribed RSS feeds.')
    subparsers = parser.add_subparsers()

    profiles_parser = subparsers.add_parser('list-profiles', description='View the list of available profiles.')
    profiles_parser.set_defaults(func=cli.list_profiles)

    add_profile_parser = subparsers.add_parser('add-profile', description='Add a new profile.')
    add_profile_parser.add_argument('profile_name', metavar='profile-name', help='The name of the profile.')
    add_profile_parser.add_argument('email', help='The email address for the profile.')
    add_profile_parser.add_argument('--user-name', help='The name of the user of the profile (which will be used in '
                                                        'the email, for example). If not provided, defaults to the '
                                                        'profile name.')
    add_profile_parser.set_defaults(func=cli.add_profile)

    delete_profile_parser = subparsers.add_parser('delete-profile', description='Delete the given profile.')
    delete_profile_parser.add_argument('profile_name', metavar='profile-name', help='Name of profile to delete.')
    delete_profile_parser.set_defaults(func=cli.delete_profile)

    add_feed_parser = subparsers.add_parser('add-feed', description='Add a feed.')
    add_feed_parser.add_argument('profile_name', metavar='profile-name', help='Name of profile.')
    add_feed_parser.add_argument('url', help='URL of feed.')
    add_feed_parser.add_argument('--title', help='Title of feed. If not provided, the URL is used.')
    add_feed_parser.add_argument('--category', help='(Optional) category in which to include feed.')
    add_feed_parser.add_argument('--fetch-name', action='store_true',
                                 help='If provided, the name of the feed will be fetched from the provided URL. '
                                      'Overrides --name.')
    add_feed_parser.add_argument('--test', action='store_true', help='If provided, the provided URL will be requested '
                                                                     'to ensure that it is a valid feed.')
    add_feed_parser.add_argument('--mark-read', action='store_true',
                                 help='If provided, all current entries as read so that, on the next run, only '
                                      'subsequently added entries will be displayed.')
    add_feed_parser.set_defaults(func=cli.add_feed)

    delete_feed_parser = subparsers.add_parser('delete_feed', description='Delete a feed.')
    delete_feed_parser.add_argument('profile_name', metavar='profile-name', help='Name of profile.')
    delete_feed_parser.add_argument('url', help='URL of feed to delete.')

    run_parser = subparsers.add_parser('run', description=f'Run {APP_NAME}.')
    run_parser.add_argument('profile_name', metavar='profile-name', help='Name of profile to run.')
    run_parser.add_argument('output_format', metavar='output-format', default='text',
                            help='Output format for digest. Defaults to "text".')
    run_parser.add_argument('output_method', metavar='output-method', choices=OUTPUT_METHODS, default='stdout',
                            help=f'How {APP_NAME} should send the generated digest. Defaults to "stdout".')

    return parser