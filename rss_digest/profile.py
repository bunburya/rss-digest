import os
import shutil
from configparser import ConfigParser
from copy import deepcopy
from typing import Optional, Any

import tomli
from reader import Reader, make_reader, Entry
from rss_digest.config import Config
from rss_digest.dao import ProfilesDAO
from rss_digest.exceptions import ProfileExistsError
from rss_digest.feeds import FeedList, parse_opml_file


class Profile:

    def __init__(self, config: Config, profile_name: str, email: str, user_name: Optional[str] = None,
                 dao: Optional[ProfilesDAO] = None):
        self.app_config = config
        self.dao = dao or ProfilesDAO(config.profiles_db)
        if profile_name in self.dao.list_profiles():
            raise ProfileExistsError(f'Profile "{profile_name}" already exists. '
                                     'Try loading it from the database instead.')
        self.profile_name = profile_name
        self.user_name = user_name or profile_name
        self.email = email

        self.config_dir = os.path.join(config.profile_config_dir, profile_name)
        self.config_file = os.path.join(self.config_dir, 'config.ini')
        self.templates_dir = os.path.join(self.config_dir, 'templates')
        self.data_dir = os.path.join(config.data_dir, profile_name)
        self.profile_dirs = (self.config_dir, self.templates_dir, self.data_dir)
        self.mkdirs()

        self.feedlist_fpath = os.path.join(self.config_dir, 'feeds.opml')
        self.reader_db_fpath = os.path.join(self.data_dir, 'reader.db')

        self._feedlist = None
        self._reader = None
        self._config = None

    def save(self):
        self.dao.save_profile(self)

    def mkdirs(self):
        for d in self.profile_dirs:
            if not os.path.exists(d):
                os.makedirs(d)

    def rmdirs(self):
        for d in self.profile_dirs:
            shutil.rmtree(d)

    def _load_feedlist(self) -> FeedList:
        try:
            return parse_opml_file(self.feedlist_fpath)
        except FileNotFoundError:
            return FeedList()

    @property
    def feedlist(self) -> FeedList:
        if self._feedlist is None:
            self._feedlist = self._load_feedlist()
        return self._feedlist

    def add_feed(self, title: str, url: str, category: Optional[str] = None, save: bool = True):
        feedlist = self.feedlist
        if not feedlist.has_category(category):
            feedlist.add_category(category)
        feedlist.add_feed(title, url, category)
        if save:
            feedlist.to_opml_file(self.feedlist_fpath)

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

    def get_unread_entries(self, mark_read: bool = False) -> list[Entry]:
        """Return unread feed entries."""
        with make_reader(self.reader_db_fpath) as reader:
            unread = reader.get_entries(read=False)
            if mark_read:
                for entry in unread:
                    reader.mark_entry_as_unread(entry)
        return list(unread)


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
