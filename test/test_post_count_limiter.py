from collections import namedtuple
from unittest.mock import AsyncMock

import pytest

from posts.post_count_limiter import PostCountLimiter

FakePost = namedtuple("Post", "permalink author id count_to_limit created_utc")

def fake_post(permalink="some_permalink", author="some_author", the_id="some_id", count_to_limit=True, created_utc=3):
    return FakePost(permalink, author, the_id, count_to_limit, created_utc)

class TestPostCountLimiter:

    @pytest.mark.asyncio
    async def test_not_limited(self):
        # given
        mock_post_repo = AsyncMock()
        mock_post_repo.contains.return_value = False

        mock_reddit = AsyncMock()

        mock_configuration = AsyncMock()
        mock_configuration.config = {"post_limit_reached_threshold": 3}

        testee = PostCountLimiter(post_repo=mock_post_repo, qvbot_reddit=mock_reddit,
                                  is_live_environment=True, quality_vote_bot_configuration=mock_configuration)
        # when
        await testee.take(fake_post())

        # then
        mock_post_repo.fetch.assert_called()
        mock_post_repo.do_not_count_to_limit.assert_not_called()
        mock_reddit.comment.assert_not_called()

    @pytest.mark.asyncio
    async def test_ignore_removed_posts(self):
        # given
        mock_post_repo = AsyncMock()
        mock_post_repo.fetch.return_value = [fake_post(f'{i}', count_to_limit=(i % 2) == 0) for i in range(8)]

        mock_reddit = AsyncMock()

        mock_configuration = AsyncMock()
        mock_configuration.config = {"post_limit_reached_threshold": 7}

        testee = PostCountLimiter(post_repo=mock_post_repo, qvbot_reddit=mock_reddit,
                                  is_live_environment=True, quality_vote_bot_configuration=mock_configuration)

        # when
        await testee.take(fake_post())

        # then
        mock_post_repo.fetch.assert_called()
        mock_post_repo.do_not_count_to_limit.assert_not_called()
        mock_reddit.comment.assert_not_called()

        mock_submission = mock_reddit.submission.return_value
        mock_submission.mod.remove.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_over_limit(self):
        # given
        mock_post_repo = AsyncMock()
        mock_post_repo.contains.return_value = False
        mock_post_repo.fetch.return_value = [fake_post(f'{i}', created_utc=i) for i in range(8)]

        mock_reddit = AsyncMock()

        mock_configuration = AsyncMock()
        mock_configuration.config = {"post_limit_reached_threshold": 7}

        testee = PostCountLimiter(post_repo=mock_post_repo, qvbot_reddit=mock_reddit,
                                  is_live_environment=True, quality_vote_bot_configuration=mock_configuration)

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

    @pytest.mark.asyncio
    async def test_ignore_over_limit_if_environment_isnt_live(self):
        # given
        mock_post_repo = AsyncMock()
        mock_post_repo.fetch.return_value = [fake_post(f'{i}') for i in range(8)]

        mock_reddit = AsyncMock()

        mock_configuration = AsyncMock()
        mock_configuration.config = {"post_limit_reached_threshold": 3}


        local = "local"
        testee = PostCountLimiter(post_repo=mock_post_repo, qvbot_reddit=mock_reddit,
                                  is_live_environment=False, quality_vote_bot_configuration=mock_configuration)
        # when
        await testee.take(fake_post())

        # then
        mock_submission = mock_reddit.submission.return_value
        mock_submission.mod.remove.assert_not_awaited()

        mock_reddit.comment.assert_not_called()


    @pytest.mark.asyncio
    async def test_limit_is_configurable(self):
        # given
        mock_post_repo = AsyncMock()
        mock_post_repo.contains.return_value = False
        mock_post_repo.fetch.return_value = [fake_post(f'{i}', created_utc=i) for i in range(3)]

        mock_reddit = AsyncMock()

        mock_configuration = AsyncMock()
        mock_configuration.config = {"post_limit_reached_threshold": 2}

        testee = PostCountLimiter(post_repo=mock_post_repo, qvbot_reddit=mock_reddit,
                                  is_live_environment=True, quality_vote_bot_configuration=mock_configuration)

        # when
        a_fake_post = fake_post()
        await testee.take(a_fake_post)

        # then
        mock_reddit.submission.assert_awaited()
        mock_submission = mock_reddit.submission.return_value
        mock_submission.mod.remove.assert_awaited_with(spam=False, mod_note="post count limit reached")
