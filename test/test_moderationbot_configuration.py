import os
import re
import tempfile
from collections import namedtuple
from pathlib import Path

import yaml

from automod_configuration import AutomodConfiguration
from helper.moderation_bot_configuration import ModerationBotConfiguration
from helper.item_helper import permalink


def temp_config_name():
    with tempfile.NamedTemporaryFile() as tmp:
        test_config = tmp.name
    # os.unlink(test_config)
    assert not os.path.exists(test_config)
    return test_config


class TestAutomodConfiguration:

    def test_create_a_config_file_if_not_exists(self):
        # given
        test_config = temp_config_name()

        # when
        ModerationBotConfiguration(test_config)

        # then
        assert os.path.exists(test_config)

    def test_create_default_config_if_not_exists(self):
        # given
        test_config = temp_config_name()

        # when
        config = ModerationBotConfiguration(test_config)

        # then
        expected_keys = ['discord_bot_token', 'discord_guild_id',
                         'flairy_channel_id', 'flairy_client_id', 'flairy_client_secret', 'flairy_password',
                         'flairy_username', 'is_live_environment', 'logging_output_channel_id', 'mod_tag_channel_id',
                         'qvbot_client_id', 'qvbot_client_secret', 'qvbot_password', 'qvbot_username',
                         'report_channel_id', 'subreddit_name', 'user_investigation_channel_id']
        expected_comment_keys = [f"~{key}" for key in expected_keys]
        both_keys = expected_keys + expected_comment_keys

        config_keys = [key for key in config.keys()]
        assert sorted(config_keys) == sorted(both_keys)

    def test_default_config_uses_integers_where_necessary(self):
        # given
        test_config = temp_config_name()

        # when
        config = ModerationBotConfiguration(test_config)

        # then
        integer_keys = ['discord_guild_id', 'flairy_channel_id', 'mod_tag_channel_id',
                        'report_channel_id', 'user_investigation_channel_id']
        for key in integer_keys:
            assert isinstance(config[key], int), f"{key} is not an integer"

    def test_extract_qvbot_user_information(self):
        # given
        test_config = temp_config_name()

        # when
        config = ModerationBotConfiguration(test_config)
        readonly = config.qvbot_reddit_settings()

        # then
        expected_keys = ['username', 'password', 'client_id', 'client_secret']
        assert sorted(expected_keys) == sorted(readonly.keys())

    def test_extract_flairy_user_information(self):
        # given
        test_config = temp_config_name()

        # when
        config = ModerationBotConfiguration(test_config)
        readonly = config.flairy_reddit_settings()

        # then
        expected_keys = ['username', 'password', 'client_id', 'client_secret']
        assert sorted(expected_keys) == sorted(readonly.keys())

    def test_should_not_contain_new_default_values(self):
        # given
        test_config = temp_config_name()
        config = ModerationBotConfiguration(test_config, default_config={})
        assert 'some_new_key' not in config

    def test_should_append_new_default_values(self):
        # given
        test_config = temp_config_name()
        default_config = {
            'some_new_key': 'the_new_value'
        }

        # when
        config = ModerationBotConfiguration(test_config, default_config)

        # then
        assert 'some_new_key' in config
        assert config['some_new_key'] == 'the_new_value'

