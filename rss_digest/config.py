#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import logging
import os
import shutil
from json import dump, load
from configparser import ConfigParser
from typing import Optional, Any, Mapping

import appdirs

# Few helper functions
from rss_digest.metadata import APP_NAME


def load_json(fpath, empty_type=dict):
    try:
        with open(fpath) as f:
            return load(f)
    except FileNotFoundError:
        return empty_type()


def save_json(data, fpath):
    with open(fpath, 'w') as f:
        dump(data, f, indent=4)

MAIN_CONFIG_TYPES = {
    'name': str,
    'output_format': str,
    'output_method': str,
    'max_displayed_entries': int,
    'max_displayed_feeds': int,
    'include_updated': bool,
    'date_format': str,
    'time_format': str,
    'datetime_format': str,
    'timezone': str
}

OUTPUT_CONFIG_TYPES = {
    'smtp': {
        'username': str,
        'password': str,
        'from_email': str,
        'from_name': str,
        'to_email': str,
        'to_name': str,
        'server': str,
        'port': int
    },
    'file': {
        'path': str
    }
}

class BaseConfig:
    """A base class for configuration classes. Contains some common
    methods for reading configurations (writing configurations is not
    currently supported).

    """

    def __init__(self, main_config_file: str, output_config_file: str,
                 existing_main_config_file: Optional[str] = None,
                 existing_output_config_file: Optional[str] = None,
                 require_config: bool = False):
        self.main_config_file = main_config_file
        if existing_main_config_file:
            shutil.copy(existing_main_config_file, main_config_file)
        self.output_config_file = output_config_file
        if existing_output_config_file:
            shutil.copy(existing_output_config_file, output_config_file)

        self.main_config = ConfigParser()
        try:
            with open(self.main_config_file) as f:
                self.main_config.read_file(f)
        except FileNotFoundError as e:
            if require_config:
                raise e

        # Only load output.ini when we need it (as it could contain sensitive information)
        self._output_config: Optional[ConfigParser] = None

        logging.debug(f'{self.__class__.__name__} initialised.')
        logging.debug(f'Main config file: {self.main_config_file}')
        logging.debug(f'Output config file: {self.output_config_file}')

    @property
    def output_config(self) -> ConfigParser:
        if self._output_config is None:
            self._output_config = ConfigParser()
            with open(self.output_config_file) as f:
                self._output_config.read_file(f)
        return self._output_config

    def _get_config_value(self, conf: ConfigParser, types: Mapping[str, type], section: str, key: str) -> Any:
        """Look up the given configuration value and return it as the
        appropriate datatype.

        :param conf: The ConfigParser object to search.
        :param section: The section of the ConfigParser object to check.
        :param types: A mapping of configuration options to the
            appropriate datatypes.
        :param key: The name of the option to look up.
        :return: The requested value, as the correct datatype.

        """
        logging.debug(f'Searching for config option "{key}" in section "{section}".')
        raw_val = conf.get(section, key, fallback=None)
        if raw_val is not None:
            to_type = types[key]
            logging.debug(f'Found value "{raw_val}"; converting to {to_type}.')
            raw_val = to_type(raw_val)
        else:
            logging.debug('Value not found!')
        return raw_val

    def get_main_config_value(self, key: str) -> Any:
        """Get the configuration value for a particular option from the
        main configuration file.

        :param key: The name of the option to look up.
        :return: The specified value, as the correct datatype.

        """
        return self._get_config_value(self.main_config, MAIN_CONFIG_TYPES, 'defaults', key)

    def get_output_config_value(self, section: str, key: str) -> Any:
        """Get the configuration value for a particular option from the
        output configuration file.

        :param section: The section in the output configuration file to
            search, corresponding to the type of output, eg, smtp.
        :param key: The name of the option to look up.
        :return: The specified value, as the correct datatype.

        """
        return self._get_config_value(self.output_config, OUTPUT_CONFIG_TYPES[section], section, key)


class AppConfig(BaseConfig):
    """A class to control and store app-level configuration settings."""

    def __init__(self, config_dir: Optional[str] = None, data_dir: Optional[str] = None,
                 existing_main_config_file: Optional[str] = None, existing_output_config_file: Optional[str] = None):
        """Create a new AppConfig object.

        :param config_dir: Where to store the config directory.
        :param data_dir: Where to store the data directory.
        :param existing_main_config_file: A path to an existing config.ini file
            to be copied to the appropriate location.
        :param existing_output_config_file: A path to an existing output.ini file
            to be copied to the appropriate location.

        If an argument is not provided, a location will be chosen based
        on the operating system (using the ``appdirs`` library).

        """
        self.config_dir = config_dir or appdirs.user_config_dir(APP_NAME)
        self.profiles_config_dir = os.path.join(self.config_dir, 'profiles')
        if not os.path.exists(self.profiles_config_dir):
            os.makedirs(self.profiles_config_dir)
        self.templates_dir = os.path.join(self.config_dir, 'templates')
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)

        self.data_dir = data_dir or appdirs.user_data_dir(APP_NAME)
        self.profiles_data_dir = os.path.join(self.data_dir, 'profiles')
        if not os.path.exists(self.profiles_data_dir):
            os.makedirs(self.profiles_data_dir)

        main_config_file = os.path.join(self.config_dir, 'config.ini')
        output_config_file = os.path.join(self.config_dir, 'output.ini')
        super().__init__(main_config_file, output_config_file, existing_main_config_file, existing_output_config_file)

    def get_profile_config_dir(self, name: str) -> str:
        """Get the location of a profile configuration directory.

        :param name: The name of the profile.
        :return: The path to the relevant directory.

        """
        return os.path.join(self.profiles_config_dir, name)

    def get_profile_data_dir(self, name: str) -> str:
        """Get the location of a profile data directory.

        :param name: The name of the profile.
        :return: The path to the relevant directory.

        """
        return os.path.join(self.profiles_data_dir, name)

    def get_profile_config(self, name: str, config_ini: Optional[str] = None, output_ini: Optional[str] = None,
                           opml_file: Optional[str] = None) -> ProfileConfig:
        """Get a ProfileConfig object for a specific profile.

        :param name: The name of the profile.
        :return: A :class:`ProfileConfig` object for the relevant profile.

        """
        return ProfileConfig(self, name)


class ProfileConfig(BaseConfig):
    """A class to control and store profile-specific configuration
    settings.

    """

    def __init__(self, app_config: AppConfig, profile_name: str,
                 existing_main_config_file: Optional[str] = None, existing_output_config_file: Optional[str] = None):
        """Create a new ProfileConfig object.

        :param app_config: An :class:`AppConfig` object storing
            app-level configuration options.
        :param profile_name: The name of the profile.
        :param existing_main_config_file: A path to an existing config.ini file
            to be copied to the appropriate location.
        :param existing_output_config_file: A path to an existing output.ini file
            to be copied to the appropriate location.

        """
        self.app_config = app_config
        self.profile_name = profile_name
        self.config_dir = self.app_config.get_profile_config_dir(profile_name)
        self.data_dir = self.app_config.get_profile_data_dir(profile_name)
        for dir in (self.config_dir, self.data_dir):
            if not os.path.exists(dir):
                os.makedirs(dir)

        self.opml_file = os.path.join(self.config_dir, 'feeds.opml')
        self.feeds_db_file = os.path.join(self.data_dir, 'feeds.db')
        self.last_updated_file = os.path.join(self.data_dir, 'last_updated')

        main_config_file = os.path.join(self.config_dir, 'config.ini')
        output_config_file = os.path.join(self.config_dir, 'output.ini')
        super().__init__(main_config_file, output_config_file, existing_main_config_file, existing_output_config_file)

    def get_main_config_value(self, key: str) -> Any:
        """Get the configuration value for a particular option from the
        profile's main configuration file, or the app's main
        configuration file if the option is not set in the profile's
        configuration file.

        :param key: The name of the option to look up.
        :return: The specified value, as the correct datatype.

        """
        logging.debug(f'Getting main config value "{key}" for profile "{self.profile_name}".')
        val = super().get_main_config_value(key)
        if val is None:
            logging.debug('Not found in profile config; searching app config.')
            val = self.app_config.get_main_config_value(key)
        else:
            logging.debug(f'Value is "{val}".')
        return val

    def get_output_config_value(self, section: str, key: str) -> Any:
        """Get the configuration value for a particular option from the
        profile's output configuration file, or the app's output
        configuration file if the option is not set in the profile's
        configuration file.

        :param section: The section in the output configuration file to
            search, corresponding to the type of output, eg, smtp.
        :param key: The name of the option to look up.
        :return: The specified value, as the correct datatype.

        """
        val = super().get_main_config_value(key)
        if val is None:
            val = self.app_config.get_main_config_value(key)
        return val