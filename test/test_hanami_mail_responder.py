import re
from unittest.mock import AsyncMock, MagicMock

import pytest

from cogs.hanami_mail_responder import Hanami


class IgnoreTestHanamiMailResponder:

    @pytest.mark.asyncio
    async def test_read_config(self):
        # given
        wikipage = MagicMock()
        wikipage.name = "hanami_config/some_type"
        wikipage.content_md = """
    keywords:
        "reporting": 5
        "found a shill": 0.2
        "shill": -3
        "user": 7
    response: |-
            **REPORT USER**

            We've detected that you might be reaching out to the mod team to report a user, post, or comment that 
            appears out of place. Maybe you’ve identified a user with a shilly post history, somebody spamming something 
            unrelated to GME in comments, or generally violating the “ape don’t fight ape” rule."""
        wikipage.load = AsyncMock()

        subreddit = MagicMock()
        subreddit.wiki.__aiter__.return_value = [wikipage]

        hanami = Hanami(subreddit)
        hanami.test_config = False

        # when
        await hanami.on_ready()
        result = hanami.config

        # then
        expected_keywords = {
            re.compile("reporting"): 5,
            re.compile("shill"): -3,
            re.compile("user"): 7,
            re.compile("found a shill"): 0.2}

        config = result['types']['some_type']
        assert len(config['keywords']) == len(expected_keywords)

        for k, v in config['keywords'].items():
            assert k in expected_keywords
            assert expected_keywords[k] == v

        assert config['response'] == "**REPORT USER**\n\nWe've detected that you might be reaching out to the mod " \
                                     "team to report a user, post, or comment that \nappears out of place. " \
                                     "Maybe you’ve identified a user with a shilly post history, somebody spamming " \
                                     "something \nunrelated to GME in comments, or generally violating " \
                                     "the “ape don’t fight ape” rule."

    @pytest.mark.asyncio
    async def test_categorize(self):
        # given
        config = {
            'types': {
                'some_type': {
                    'keywords': {
                        re.compile("reporting"): 5,
                        re.compile("shill"): -3,
                        re.compile("user"): 7,
                        re.compile("found a shill"): 0.2}
                }
            }
        }

        # when
        hanami = Hanami(MagicMock, config)

        categories = hanami.categorize(" user shill")

        # then
        assert categories == {'some_type': {'shill': -3, 'total': 7-3, 'user': 7}}

    @pytest.mark.asyncio
    async def test_preprocess(self):
        # given
        hanami = Hanami(MagicMock)

        # when
        phrase = hanami.preprocess_phrase("I found this user and I'm convinced it's a shill")

        assert phrase == "user convinced shill"
