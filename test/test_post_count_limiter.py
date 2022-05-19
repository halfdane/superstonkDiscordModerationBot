from collections import namedtuple
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from redditItemHandler.post_count_limiter import PostCountLimiter

FakePost = namedtuple("Post", "permalink author id count_to_limit")


def fake_post(permalink="some_permalink", author="some_author", the_id="some_id", count_to_limit=True):
    return FakePost(permalink, author, the_id, count_to_limit)


class TestPostCountLimiter:

    @pytest.mark.asyncio
    async def test_not_limited(self):
        # given
        mock_bot = AsyncMock()

        mock_post_repo = AsyncMock()
        mock_post_repo.contains.return_value = False

        mock_reddit = AsyncMock()

        testee = PostCountLimiter(bot=mock_bot, post_repo=mock_post_repo, qvbot_reddit=mock_reddit)

        # when
        await testee.take(fake_post())

        # then
        mock_post_repo.fetch.assert_called()
        mock_post_repo.do_not_count_to_limit.assert_not_called()
        mock_reddit.comment.assert_not_called()
        mock_bot.report_channel.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_over_limit(self):
        # given
        mock_bot = AsyncMock()

        mock_post_repo = AsyncMock()
        mock_post_repo.contains.return_value = False
        mock_post_repo.fetch.return_value = [fake_post(f'{i}', count_to_limit=False) for i in range(8)]

        mock_reddit = AsyncMock()

        mock_report_channel = AsyncMock()

        testee = PostCountLimiter(bot=mock_bot, post_repo=mock_post_repo, qvbot_reddit=mock_reddit,
                                  report_channel=mock_report_channel)

        # when
        a_fake_post = fake_post()
        await testee.take(a_fake_post)

        # then
        mock_reddit.submission.assert_awaited()
        mock_submission = mock_reddit.submission.return_value
        mock_submission.mod.remove.assert_awaited_with(spam=False, mod_note="post count limit reached")

        mock_submission.reply.assert_awaited()
        mock_response = mock_submission.reply.return_value
        mock_response.mod.distinguish.assert_awaited_with(how="yes", sticky=True)
        mock_response.mod.ignore_reports.assert_awaited()

        mock_post_repo.do_not_count_to_limit.assert_awaited_with(a_fake_post)

        mock_report_channel.send.assert_awaited()
