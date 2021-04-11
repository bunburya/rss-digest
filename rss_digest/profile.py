import os
import shutil
from dataclasses import dataclass
from typing import Optional

from rss_digest.config import AppConfig
from rss_digest.dao import ProfilesDAO
from rss_digest.exceptions import ProfileExistsError

@dataclass
class Profile:

    name: str

    ### BELOW IS LEGACY CODE

    def update_last_updated(self, failures=None):
        """Set last_updated (for each feed, and for the profile as a
        whole), to the current time."""
        update_time = datetime.now().timetuple()
        self.set_last_updated(update_time)
        for f in self.feedlist:
            self.set_last_updated(update_time, f['xmlUrl'])
        # finish (is there anything else that needs to be done)?

    # state is data related to the working of the rss-digest programme
    # itself (as opposed to data relating to feeds, etc)

    @property
    def state_file(self):
        return join(self.profile_dir, 'state.json')

    def load_state(self):
        self.state = load_json(self.state_file)
        self.new_state = {}
        # If there is no state, assume this is the first run.
        self.first_run = not self.state

    def save_state(self):
        if self.new_state:
            self.state = self.new_state
            self.new_state = {}
        save_json(self.state, self.state_file)

    # feeddata is data (entries, etc) relating to feeds that have
    # already been downloaded

    @property
    def data_file(self):
        return join(self.profile_dir, 'data.json')

    def load_data(self):
        self.feeddata = load_json(self.data_file)

    def save_data(self, data=None):
        if data is not None:
            self.feeddata = data
        save_json(self.feeddata, self.data_file)

    @property
    def list_file(self):
        return join(self.profile_dir, 'feeds.opml.old')

    def load_list(self):
        self.feedlist = FeedURLList(self.list_file)

    def save_list(self):
        self.feedlist.to_opml(self.list_file)

    def get_last_updated(self, url=None):
        # If url is None, this returns the last update of the feedlist
        # as a whole (same goes for setter function below)

        # NOTE:  We don't currently provide a way to access new_state,
        # because I think when you are checking state you will always
        # want the pre-existing state.

        # print(self.state)

        updated_dict = self.state.get('last_updated', {})
        if (url is None) and (None not in updated_dict):
            # If we haven't set a specific value for the feedlist as a
            # whole, just return the most recent URL-specific value
            try:
                result = max(updated_dict.values())
            except ValueError:
                result = None
        else:
            result = updated_dict.get(url)

        if result is None:
            return result
        else:
            return struct_time(result)

    def set_last_updated(self, last_updated, url=None, new=True):
        # if new == True, we save to self.new_state instead of
        # self.state.  new_state is then copied to state when saving.
        # This is to allow us to access the old last_updated value when
        # generating HTML.  True is the default value because I think
        # you will always want to save to the buffer.

        if new:
            state = self.new_state
        else:
            state = self.state
        if 'last_updated' not in state:
            state['last_updated'] = {}
        state['last_updated'][url] = last_updated

    def get_conf(self, key, val_type=None):
        return self.config.get(key, val_type)

    def add_feed(self, title, url, posn=-1, save=True, *args, **kwargs):
        self.load_list()
        self.load_data()
        self.feedlist.insert_feed(posn, 'rss', title, url,
                                  # Can't serialise None, so remove None args
                                  *filter(lambda a: a is not None, args),
                                  **{k: v for k, v in kwargs.items() if v is not None})
        self.feeddata[url] = {}
        if save:
            self.save_data()
            self.save_list()

    def get_feed_by_url(self, url):
        return self.feedlist.get_feed_by_url(url)
