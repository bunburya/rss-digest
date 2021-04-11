from __future__ import annotations

import sqlite3 as sql
from typing import List, TYPE_CHECKING

from rss_digest.exceptions import ProfileNotFoundError

if TYPE_CHECKING:
    from rss_digest.config import AppConfig
    from rss_digest.profile import Profile

class ProfilesDAO:

    CREATE_TABLE = """CREATE TABLE IF NOT EXISTS profiles (
        profile_name TEXT PRIMARY KEY,
        email TEXT NOT NULL,
        user_name TEXT
    )"""

    ADD_PROFILE = 'INSERT OR REPLACE INTO profiles (profile_name, email, user_name) VALUES (? ? ?)'

    LOAD_PROFILE = 'SELECT * FROM profiles WHERE profile_name=?'

    DELETE_PROFILE = 'DELETE FROM profiles WHERE profile_name=?'

    LIST_PROFILES = 'SELECT profile_name FROM profiles'

    def __init__(self, db_file: str):
        self.conn = sql.connect(db_file)

    def save_profile(self, profile: 'Profile'):
        cursor = self.conn.cursor()
        cursor.execute(self.ADD_PROFILE, (profile.profile_name, profile.email, profile.user_name))
        self.conn.commit()

    def load_profile(self, profile_name: str) -> 'Profile':
        cursor = self.conn.cursor()
        cursor.execute(self.LOAD_PROFILE, (profile_name,))
        results = cursor.fetchone()
        if results:
            profile_name, email, user_name = results
            return Profile(self.config, profile_name, email, user_name, self)
        else:
            raise ProfileNotFoundError(f'No profile found for "{profile_name}".')

    def delete_profile(self, profile_name: str):
        cursor = self.conn.cursor()
        cursor.execute(self.DELETE_PROFILE, (profile_name,))
        self.conn.commit()

    def list_profiles(self) -> List[str]:
        cursor = self.conn.cursor()
        cursor.execute(self.LIST_PROFILES)
        return [r[0] for r in cursor.fetchall()]