"""Functions and classes for using the command line interface."""
import logging
import sys
import argparse
from typing import Optional

from rss_digest.config import AppConfig
from rss_digest.exceptions import ProfileNotFoundError, FeedExistsError, FeedError, ProfileExistsError
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
            self._config = AppConfig()
        else:
            self._config = config
        self._app = RSSDigest(self._config)

    def configure(self, args: argparse.Namespace):
        """Configure the behaviour of the CLI based on the provided
        command line arguments.

        """
        if args.debug:
            logging.getLogger().setLevel(logging.INFO)
        args_dict = vars(args)
        self._config = AppConfig(
            args_dict['config_dir'],
            args_dict['data_dir']
        )
        self._app = RSSDigest(self._config)

    def list_profiles(self, args: argparse.Namespace):
        print('Available profiles:')
        for p in self._app.profiles:
            print(f'  {p}')

    def add_profile(self, args: argparse.Namespace):
        try:
            self._app.add_profile(args.profile_name)
            err(f'Profile "{args.profile_name}" added.')
            err('Now add some feeds and configure as necessary.')
        except ProfileExistsError:
            err(f'Profile "{args.profile_name}" already exists.')

    def delete_profile(self, args: argparse.Namespace):
        try:
            self._app.delete_profile(args.profile_name)
            err(f'Profile "{args.profile_name}" deleted.')
        except ProfileNotFoundError:
            err(f'Profile "{args.profile_name}" not found.')

    def add_feed(self, args: argparse.Namespace):
        """Add a new feed."""
        try:
            self._app.add_feed(
                args.profile_name,
                args.url,
                args.title,
                args.category,
                args.test,
                args.mark_read,
                args.fetch_title
            )
            err('Feed added.')
        except FeedError as e:
            err(f'Received error adding feed: {str(e) or type(e)}')

    def list_feeds(self, args: argparse.Namespace):
        """List all of the given profile's feeds."""
        name = args.profile_name
        try:
            feedlist = self._app.get_profile(name).feedlist
            print(f'Feeds for {name}:')
            for feed in feedlist:
                print(f'  {feed.title} (URL: {feed.xml_url}, category: {feed.category})')
        except ProfileNotFoundError:
            err(f'Profile not found: {name}')

    def delete_feed(self, args: argparse.Namespace):
        """Delete the given feed."""
        deleted = self._app.delete_feeds(args.profile_name, feed_url=args.url)
        if not deleted:
            err(f'Could not find feed with URL {args.url} to delete.')
        else:
            err(f'Deleted {deleted} feeds with URL {args.url}.')

    def run(self, args: argparse.Namespace):
        """Run rss-digest for the given profile, fetching updates for
        each feed and generating a digest.

        """
        self._app.run(
            profile_name=args.profile_name,
            save=not args.forget,
            method=args.output_method,
            format=args.output_format
        )


def get_arg_parser(cli: CLI) -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(description='Produce a digest of subscribed RSS feeds.')
    subparsers = parser.add_subparsers()

    # Basic config options

    parser.add_argument('--config-dir', '-c', help='Directory for configuration files.')
    parser.add_argument('--data-dir', '-d', help='Directory for data files.')

    parser.add_argument('--debug', action='store_true', help='Debug mode (more verbose logging).')

    # Profile-related commands (list, add, delete, edit profiles, etc)

    profile_cmd_parser = subparsers.add_parser('profile', description='Profile-related commands.')
    profile_cmds = profile_cmd_parser.add_subparsers()

    add_profile_parser = profile_cmds.add_parser('add', description='Add a new profile.')
    add_profile_parser.add_argument('profile_name', help='The name of the profile.')
    add_profile_parser.add_argument('--output-method', help='The default output method for this profile.',
                                    choices=OUTPUT_METHODS)
    add_profile_parser.add_argument('--output-email', metavar='EMAIL',
                                    help='The email to which the digest should be sent for this user (if relevant).')
    add_profile_parser.add_argument('--output-file', metavar='FILE',
                                    help='The file to which the digest should be saved for this user (if relevant).')
    add_profile_parser.add_argument('--user-name', metavar='NAME',
                                    help='The name of the user of the profile (which may be used in the output). '
                                         'If not provided, defaults to the profile name.')
    add_profile_parser.set_defaults(func=cli.add_profile)

    delete_profile_parser = profile_cmds.add_parser('delete', description='Delete the given profile.')
    delete_profile_parser.add_argument('profile_name', help='Name of profile to delete.')
    delete_profile_parser.set_defaults(func=cli.delete_profile)

    list_profiles_parser = profile_cmds.add_parser('list', description='View the list of available profiles.')
    list_profiles_parser.set_defaults(func=cli.list_profiles)

    # Feed-related commands (list, add, delete feeds, etc)

    feed_cmd_parser = subparsers.add_parser('feed', description='Feed-related commands.')
    feed_cmds = feed_cmd_parser.add_subparsers()

    add_feed_parser = feed_cmds.add_parser('add', description='Add a feed.')
    add_feed_parser.add_argument('profile_name', help='Name of profile.')
    add_feed_parser.add_argument('url', help='URL of feed.')
    add_feed_parser.add_argument('--title', help='Title of feed. If not provided, the URL is used.')
    add_feed_parser.add_argument('--category', help='(Optional) category in which to include feed.')
    add_feed_parser.add_argument('--fetch-title', action='store_true',
                                 help='If provided, the name of the feed will be fetched from the provided URL. '
                                      'Overrides --title.')
    add_feed_parser.add_argument('--test', action='store_true', help='If provided, the provided URL will be requested '
                                                                     'to ensure that it is a valid feed.')
    add_feed_parser.add_argument('--mark-read', action='store_true',
                                 help='If provided, all current entries as read so that, on the next run, only '
                                      'subsequently added entries will be displayed.')
    add_feed_parser.set_defaults(func=cli.add_feed)

    delete_feed_parser = feed_cmds.add_parser('delete', description='Delete a feed.')
    delete_feed_parser.add_argument('profile_name', help='Name of profile.')
    delete_feed_parser.add_argument('url', help='URL of feed to delete.')
    delete_feed_parser.set_defaults(func=cli.delete_feed)

    list_feeds_parser = feed_cmds.add_parser('list', description='List the feeds for a profile.')
    list_feeds_parser.add_argument('profile_name', help='Name of profile.')
    list_feeds_parser.set_defaults(func=cli.list_feeds)

    # Run command

    run_parser = subparsers.add_parser('run', description=f'Run {APP_NAME}.')
    run_parser.add_argument('profile_name', metavar='profile-name', help='Name of profile to run.')
    run_parser.add_argument('--output_format', metavar='FORMAT',
                            help='Output format for digest. If not provided, configured default is used.')
    run_parser.add_argument('--output_method', metavar='METHOD', choices=OUTPUT_METHODS,
                            help=f'How {APP_NAME} should send the generated digest. If not provided, the configured'
                                 f'default is used.')
    run_parser.add_argument('--forget', action='store_true',
                            help=f'If provided, {APP_NAME} will "forget" sending the digest, which means that, while'
                                 f'the new entries will be fetched and saved, they will not be marked as read after'
                                 f'sending.')
    run_parser.set_defaults(func=cli.run)

    return parser
