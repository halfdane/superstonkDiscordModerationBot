import os
import sys
from pathlib import Path

import yaml

CONFIG_HOME = os.path.dirname(os.path.realpath(sys.path[0]))
CONFIG_FILE = f"{CONFIG_HOME}/config.yaml"

DEFAULT_CONFIG = {
    '~discord_bot_token': 'get it from the developer settings in discord',
    'discord_bot_token': 'some token',
    '~discord_guild_id': 'it is the id of the discord server where the bot reports stuff',
    'discord_guild_id': 1234567890,

    '~is_live_environment': 'True or False',
    'is_live_environment': False,

    '~flairy_username': 'The username of the superstonk flairy bot',
    'flairy_username': 'Superstonk-Flairy',
    '~flairy_channel_id': 'the channel id where flairy bot should report stuff',
    'flairy_channel_id': 1234567890,
    '~flairy_client_id': 'get it from the reddit developer settings',
    'flairy_client_id': 'some client id',
    '~flairy_client_secret': 'get it from the reddit developer settings',
    'flairy_client_secret': 'some client secret',
    '~flairy_password': 'it is the password of the reddit account that should be used by flairy bot',
    'flairy_password': 'some password',

    '~qvbot_username': 'The username of the superstonk qvbot',
    'qvbot_username': 'Superstonk_QV',
    '~qvbot_client_id': 'the client id of the reddit app that should be used by qvbot',
    'qvbot_client_id': 'some client id',
    '~qvbot_client_secret': 'the client secret of the reddit app that should be used by qvbot',
    'qvbot_client_secret': 'some client secret',
    '~qvbot_password': 'the password of the reddit account that should be used by qvbot',
    'qvbot_password': 'some password',

    '~logging_output_channel_id': 'the channel id where the bot should log debugging messages',
    'logging_output_channel_id': 1234567890,
    '~mod_tag_channel_id': 'the channel id where the bot should report mod tags',
    'mod_tag_channel_id': 1234567890,

    '~report_channel_id': 'the channel id where the bot should report stuff',
    'report_channel_id': 1234567890,
    '~subreddit_name': 'the name of the subreddit where the bot should operate',
    'subreddit_name': 'superstonk',
    '~user_investigation_channel_id': 'the channel id where the bot listens for user investigation requests',
    'user_investigation_channel_id': 1234567890
}


class ModerationBotConfiguration(dict):

    def __init__(self, config_file=CONFIG_FILE, default_config=DEFAULT_CONFIG):
        super().__init__()
        # start with default values
        for key, value in default_config.items():
            self[key] = value

        # read config file and override all keys
        config_path = Path(config_file)
        if not config_path.exists():
            config_path.write_text(yaml.dump(DEFAULT_CONFIG, sort_keys=False))
        yaml_config = yaml.safe_load(config_path.read_text())

        for key, value in yaml_config.items():
            self[key] = value

        self.qvbot_reddit_settings = self.__reddit_settings('qvbot')
        self.flairy_reddit_settings = self.__reddit_settings('flairy')

    def __reddit_settings(self, prefix):
        return lambda: {
            'username': self[f"{prefix}_username"],
            'password': self[f"{prefix}_password"],
            'client_id': self[f"{prefix}_client_id"],
            'client_secret': self[f"{prefix}_client_secret"]
        }
