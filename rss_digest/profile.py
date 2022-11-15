from __future__ import annotations

import logging
import os
import shutil
from copy import deepcopy
from datetime import datetime, timezone
from typing import Optional, Any

import pytz
import tomli
from pytz import tzinfo
from reader import make_reader, Entry, FeedExistsError as reader_FeedExistsError, ParseError, UpdatedFeed, \
    ReaderError
from rss_digest.exceptions import FeedExistsError, FeedError
from rss_digest.feeds import FeedList, parse_opml_file, WILDCARD

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from rss_digest.config import Config

logger = logging.getLogger(__name__)


class Profile:

    def __init__(self, config: Config, profile_name: str):
        self.app_config = config
        self.name = profile_name

        self.config_dir = os.path.join(config.profile_config_dir, profile_name)
        self.config_file = os.path.join(self.config_dir, 'config.toml')
        self.opml_file = os.path.join(self.config_dir, 'feeds.opml')
        self.data_dir = os.path.join(config.profile_data_dir, profile_name)
        self.last_updated_file = os.path.join(self.data_dir, 'last_updated')

        self.profile_dirs = (self.config_dir, self.data_dir)
        self.mkdirs()

        self.reader_db_file = os.path.join(self.data_dir, 'reader.db')

        self._feedlist = None
        self._config = None


    def _update_config_dict(self, config_fpath: str, config_dict: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Update a dict with config values read from the given TOML config file.

        :param config_fpath: Path to the TOML file.
        :param config_dict: A dict holding existing config values. If none is provided, an empty dict will be used.
        :return: A new dict with the updated values (provided dict is not changed).
        """
        if config_dict is None:
            to_update = {}
        else:
            to_update = deepcopy(config_dict)
        with open(config_fpath, 'rb') as f:
            to_update.update(tomli.load(f))
        return to_update

    @property
    def config(self) -> dict[str, Any]:
        if self._config is None:
            _config = self._update_config_dict(self.app_config.default_config_file, self._config)
            if os.path.exists(self.config_file):
                _config = self._update_config_dict(self.config_file, _config)
            self._config = _config
        return self._config

    def mkdirs(self):
        for d in self.profile_dirs:
            if not os.path.exists(d):
                os.makedirs(d)

    def rmdirs(self):
        for d in self.profile_dirs:
            if os.path.exists(d):
                shutil.rmtree(d)

    def _load_feedlist(self) -> FeedList:
        try:
            return parse_opml_file(self.opml_file)
        except FileNotFoundError:
            return FeedList()

    @property
    def feedlist(self) -> FeedList:
        if self._feedlist is None:
            self._feedlist = self._load_feedlist()
        return self._feedlist

    @property
    def last_updated(self) -> Optional[datetime]:
        """Return the date and time at which a profile's feeds were
        last updated (ie, fetched), in UTC. If no updated has been
        performed, return None.

        """
        try:
            with open(self.last_updated_file) as f:
                dt = datetime.fromisoformat(f.read())
            if dt.tzinfo is None:
                dt = dt.astimezone(timezone.utc)
            return dt
        except FileNotFoundError:
            return None

    @last_updated.setter
    def last_updated(self, dt: datetime):
        with open(self.last_updated_file, 'w') as f:
            f.write(dt.astimezone(timezone.utc).isoformat())

    @property
    def local_timezone(self) -> tzinfo:
        return pytz.timezone(self.config['timezone'])

    def sync_reader(self):
        """Sync the profile's :class:`reader.Reader` to its OPML file
        (adding feeds that are in the OPML file but not the Reader,
        and deleting those that are in the Reader but not the OPML
        file).

        :param: The name of the profile whose Reader to sync.

        """
        logger.info(f'Syncing OPML file with reader database for profile {self.name}.')
        logger.info(f'Using reader DB file at {self.reader_db_file}')
        feedlist = self.feedlist
        with make_reader(self.reader_db_file) as reader:
            opml_urls = {f.xml_url for f in feedlist}
            reader_urls = {f.url for f in reader.get_feeds()}
            removed = 0
            added = 0
            for url in reader_urls:
                if url not in opml_urls:
                    reader.delete_feed(url)
                    removed += 1
            for url in opml_urls:
                if url not in reader_urls:
                    reader.add_feed(url)
                    added += 1
            logger.debug(f'Removed {removed} feeds and added {added} feeds.')

    def add_feed(self, feed_url: str, feed_title: str, category: Optional[str] = None,
                 test_feed: bool = False, mark_read: bool = False, fetch_title: bool = False,
                 write: bool = True):
        """Add a feed to the :class:`FeedList`.

        :param feed_url: The URL of the feed.
        :param feed_title: The title of the feed.
        :param category: The category to which the feed belongs.
        :param test_feed: If True, request the feed's URL to ensure it is valid.
        :param mark_read: If True, update the feed and mark all existing entries as read immediately, so that the next
            time we generate a digest only subsequently added entries will be listed.
        :param fetch_title: If True, request the feed URL and set the title from the response. Overrides ``feed_title``.
        :param write: If True, write the FeedList to the profile's OPML file upon adding the feed.

        """
        with make_reader(self.reader_db_file) as reader:
            try:
                reader.add_feed(feed_url)
            except reader_FeedExistsError:
                raise FeedExistsError(f'Feed with URL already exists: {feed_url}')

            if test_feed or mark_read or fetch_title:
                try:
                    reader.update_feed(feed_url)
                except ParseError:
                    reader.delete_feed(feed_url)
                    raise FeedError(f'Error fetching or parsing feed at URL: {feed_url}')
                if mark_read:
                    for entry in reader.get_entries(feed=feed_url):
                        reader.mark_entry_as_read(entry)
                if fetch_title:
                    feed_title = reader.get_feed(feed_url).title or feed_title

            feedlist = self.feedlist
            feedlist.add_feed(feed_title, feed_url, category)
            if write:
                feedlist.to_opml_file(self.opml_file)

    def delete_feeds(self, feed_url: Optional[str] = WILDCARD, feed_title: Optional[str] = WILDCARD,
                     category: Optional[str] = WILDCARD) -> int:
        """Delete all feeds for the given profile and matching the given
        title, URL and category.

        :param feed_url: URL of feed to remove.
        :param feed_title: Title of feed to remove.
        :param category: Category of feed to remove.
        :return: The total number of feeds removed.

        """
        feedlist = self.feedlist
        return feedlist.remove_feeds(feed_title, feed_url, category)

    def set_opml_file(self, fpath: str, sync: bool = True):
        """Set the OPML file for the profile, replacing the existing one
        if it exists.

        :param fpath: The path to the new OPML file.
        :param sync: If True, automatically reload the profile's
            :class:`FeedList` object and sync the profile's ``reader``
            with it.

        """
        shutil.copy(fpath, self.opml_file)
        self._feedlist = None
        if sync:
            self.sync_reader()

    def update_feeds(self) -> tuple[set[str], set[str]]:
        """Update all feeds for this profile.

        :return: A tuple of two sets, the first of which contains of urls of feeds that have been updated and the
            second of which contains URLs of feeds for which an error was received when updating.

        """

        updated_urls = set()
        error_urls = set()
        self.sync_reader()
        with make_reader(self.reader_db_file) as reader:
            for (url, value) in reader.update_feeds_iter():
                if isinstance(value, UpdatedFeed):
                    logger.info(f'Got updated feed for {url} with {value.new} new entries '
                                f'and {value.modified} updated entries.')
                    if value.new:
                        updated_urls.add(url)
                elif isinstance(value, ReaderError):
                    logger.error(f'Got error when updating {url}')
                    error_urls.add(url)
            return updated_urls, error_urls

    def get_unread_entries(self, mark_read: bool = False) -> dict[str, list[Entry]]:
        """Get all unread entries for this profile.

        :param mark_read: Whether to mark each entry as read.
        :return: A dict mapping feed URLs to lists of unread entries.

        """
        with make_reader(self.reader_db_file) as reader:
            unread = reader.get_entries(read=False)
            entries = {}
            for e in unread:
                url = e.feed_url
                if url in entries:
                    entries[url].append(e)
                else:
                    entries[url] = [e]

                if mark_read:
                    reader.mark_entry_as_read(e)

            return entries

    def mark_read(self, entries: Optional[list[Entry]] = None):
        """Mark entries as read.

        :param entries: List of entries to mark as read. If not provided,
            all unread entries will be marked as read.

        """

        with make_reader(self.reader_db_file) as reader:
            if entries is None:
                entries = reader.get_entries(read=False)
            for e in entries:
                reader.mark_entry_as_read(e)

    ### BELOW IS LEGACY CODE

    # def update_last_updated(self, failures=None):
    #     """Set last_updated (for each feed, and for the profile as a
    #     whole), to the current time."""
    #     update_time = datetime.now().timetuple()
    #     self.set_last_updated(update_time)
    #     for f in self.feedlist:
    #         self.set_last_updated(update_time, f['xmlUrl'])
    #     # finish (is there anything else that needs to be done)?
    #
    # # state is data related to the working of the rss-digest programme
    # # itself (as opposed to data relating to feeds, etc)
    #
    # @property
    # def state_file(self):
    #     return join(self.profile_dir, 'state.json')
    #
    # def load_state(self):
    #     self.state = load_json(self.state_file)
    #     self.new_state = {}
    #     # If there is no state, assume this is the first run.
    #     self.first_run = not self.state
    #
    # def save_state(self):
    #     if self.new_state:
    #         self.state = self.new_state
    #         self.new_state = {}
    #     save_json(self.state, self.state_file)
    #
    # # feeddata is data (entries, etc) relating to feeds that have
    # # already been downloaded
    #
    # @property
    # def data_file(self):
    #     return join(self.profile_dir, 'data.json')
    #
    # def load_data(self):
    #     self.feeddata = load_json(self.data_file)
    #
    # def save_data(self, data=None):
    #     if data is not None:
    #         self.feeddata = data
    #     save_json(self.feeddata, self.data_file)
    #
    # @property
    # def list_file(self):
    #     return join(self.profile_dir, 'feeds.opml.old')
    #
    # def load_list(self):
    #     self.feedlist = FeedURLList(self.list_file)
    #
    # def save_list(self):
    #     self.feedlist.to_opml(self.list_file)
    #
    # def get_last_updated(self, url=None):
    #     # If url is None, this returns the last update of the feedlist
    #     # as a whole (same goes for setter function below)
    #
    #     # NOTE:  We don't currently provide a way to access new_state,
    #     # because I think when you are checking state you will always
    #     # want the pre-existing state.
    #
    #     # print(self.state)
    #
    #     updated_dict = self.state.get('last_updated', {})
    #     if (url is None) and (None not in updated_dict):
    #         # If we haven't set a specific value for the feedlist as a
    #         # whole, just return the most recent URL-specific value
    #         try:
    #             result = max(updated_dict.values())
    #         except ValueError:
    #             result = None
    #     else:
    #         result = updated_dict.get(url)
    #
    #     if result is None:
    #         return result
    #     else:
    #         return struct_time(result)
    #
    # def set_last_updated(self, last_updated, url=None, new=True):
    #     # if new == True, we save to self.new_state instead of
    #     # self.state.  new_state is then copied to state when saving.
    #     # This is to allow us to access the old last_updated value when
    #     # generating HTML.  True is the default value because I think
    #     # you will always want to save to the buffer.
    #
    #     if new:
    #         state = self.new_state
    #     else:
    #         state = self.state
    #     if 'last_updated' not in state:
    #         state['last_updated'] = {}
    #     state['last_updated'][url] = last_updated
    #
    # def get_conf(self, key, val_type=None):
    #     return self.config.get(key, val_type)
    #
    # def add_feed(self, title, url, posn=-1, save=True, *args, **kwargs):
    #     self.load_list()
    #     self.load_data()
    #     self.feedlist.insert_feed(posn, 'rss', title, url,
    #                               # Can't serialise None, so remove None args
    #                               *filter(lambda a: a is not None, args),
    #                               **{k: v for k, v in kwargs.items() if v is not None})
    #     self.feeddata[url] = {}
    #     if save:
    #         self.save_data()
    #         self.save_list()
    #
    # def get_feed_by_url(self, url):
    #     return self.feedlist.get_feed_by_url(url)
