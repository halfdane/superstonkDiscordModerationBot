import logging
from os.path import expanduser
import sqlite3

home = expanduser("~")
CONFIG_DB = f"{home}/config.db"


class ModerationBotConfiguration(dict):

    def __init__(self, database=CONFIG_DB):
        super().__init__()
        with sqlite3.connect(database) as db:
            cur = db.execute("select key, value from settings;")
            for row in cur.fetchall():
                self[row[0]] = row[1]

        self['is_live_environment'] = (self['environment'] == 'live')
        self.__as_int('discord_guild_id')
        self.__as_int('report_channel_id')
        self.__as_int('report_comments_channel_id')
        self.__as_int('flairy_channel_id')
        self.__as_int('logging_output_channel_id')
        self.__as_int('user_investigation_channel_id')

        self.readonly_reddit_settings = self.__reddit_settings('reddit')
        self.qvbot_reddit_settings = self.__reddit_settings('qvbot')
        self.flairy_reddit_settings = self.__reddit_settings('flairy')

    def remove_secrets(self):
        for prefix in ['reddit', 'qvbot', 'flairy']:
            for key in ['username', 'password', 'client_id', 'client_secret']:
                del self[f"{prefix}_{key}"],

    def __reddit_settings(self, prefix):
        return lambda: {
            'username': self[f"{prefix}_username"],
            'password': self[f"{prefix}_password"],
            'client_id': self[f"{prefix}_client_id"],
            'client_secret': self[f"{prefix}_client_secret"]
        }

    def __as_int(self, key):
        self[key] = int(self[key])


