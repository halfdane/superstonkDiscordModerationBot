from unittest.mock import AsyncMock, MagicMock
from unittest.mock import ANY

import pytest

from comments.flairy import Flairy


def default_bot():
    mock_bot = AsyncMock()
    mock_bot.is_forbidden_user_message = MagicMock()
    mock_bot.is_forbidden_user_message.return_value = False
    return mock_bot


def default_comment():
    mock_comment = MagicMock()
    mock_comment.id = "some id"
    mock_comment.body = "!FLAIRY! some flair"
    mock_comment.author.name = ""
    mock_comment.author_flair_text = "existing flair"
    mock_comment.refresh = AsyncMock()
    return mock_comment


def automod(forbid_everything):
    automod_configuration = MagicMock()
    automod_configuration.is_forbidden_user_message.return_value = forbid_everything
    return automod_configuration


class TestFlairy:

    @pytest.mark.asyncio
    async def test_flair_too_long(self):
        # given
        mock_comment = default_comment()
        mock_comment.id = "some id"
        mock_comment.body = "!FLAIRY! 123456789 123456789 123456789 123456789 123456789 123456789 1234"

        flairy_reddit = AsyncMock()

        # when
        testee = Flairy(flairy_reddit=flairy_reddit,
                        automod_configuration=automod(forbid_everything=False),
                        flairy_comment_repo=AsyncMock())
        await testee.on_ready()
        await testee.take(mock_comment)

        # then
        flairy_reddit.subreddit.return_value.flair.set.assert_not_called()
        flairy_reddit.comment.assert_called_once_with("some id", fetch=False)

        flairy_comment = flairy_reddit.comment.return_value
        flairy_comment.reply.assert_called_once()

        assert "THE FLAIR TEXT IS TOO LONG" in flairy_comment.reply.call_args[0][0]

    @pytest.mark.asyncio
    async def test_flair_contains_restricted_word(self):
        # given
        mock_comment = default_comment()

        flairy_reddit = AsyncMock()

        # when
        testee = Flairy(flairy_reddit=flairy_reddit,
                        automod_configuration=automod(forbid_everything=True),
                        flairy_comment_repo=AsyncMock())
        await testee.on_ready()
        await testee.take(mock_comment)

        # then
        flairy_reddit.subreddit.return_value.flair.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_wrong_color_results_in_additional_message(self):
        # given
        mock_comment = default_comment()
        mock_comment.body = "!FLAIRY! requesting wrong color: orange"

        flairy_reddit = AsyncMock()

        # when
        testee = Flairy(flairy_reddit=flairy_reddit,
                        automod_configuration=automod(forbid_everything=False),
                        flairy_comment_repo=AsyncMock())
        await testee.on_ready()
        await testee.take(mock_comment)

        # then
        flairy_comment = flairy_reddit.comment.return_value
        flairy_comment.reply.assert_called_once()
        assert "ORANGE IS NOT A VALID COLOR!" in flairy_comment.reply.call_args[0][0]

        flairy_reddit.subreddit.return_value.flair.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_flair_clearing(self):
        # given
        mock_comment = default_comment()
        mock_comment.body = "! FLAIRY : CLEARME! whatever happens here"

        flairy_reddit = AsyncMock()

        # when
        testee = Flairy(flairy_reddit=flairy_reddit,
                        automod_configuration=automod(forbid_everything=False),
                        flairy_comment_repo=AsyncMock())
        await testee.on_ready()
        await testee.take(mock_comment)

        # then
        flairy_comment = flairy_reddit.comment.return_value
        flairy_comment.reply.assert_called_once()
        assert "Clearing the flair as requested" in flairy_comment.reply.call_args[0][0]

        flairy_reddit.subreddit.return_value.flair.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_happy_path(self):
        # given
        mock_comment = default_comment()
        mock_comment.body = "!FLAIRY! 123456789 123456789 123456789 123456789 123456789 123456789 123"

        flairy_reddit = AsyncMock()

        # when
        testee = Flairy(flairy_reddit=flairy_reddit,
                        automod_configuration=automod(forbid_everything=False),
                        is_live_environment=True,
                        flairy_comment_repo=AsyncMock())
        await testee.on_ready()
        await testee.take(mock_comment)

        # then
        flairy_reddit.subreddit.assert_awaited()
        flairy_reddit.subreddit.return_value.flair.set.assert_awaited_with(
            redditor=mock_comment.author,
            text="123456789 123456789 123456789 123456789 123456789 123456789 123",
            flair_template_id=ANY
        )

        request_comment = flairy_reddit.comment.return_value

        request_comment.upvote.assert_awaited()
        request_comment.reply.assert_awaited()

    @pytest.mark.asyncio
    async def test_flair_seal_appending(self):
        # given
        mock_comment = default_comment()
        mock_comment.body = "!FLAIRY:SEALME! whatever happens here"
        mock_comment.author_flair_text = "some flair"
        mock_comment.author_flair_template_id = "some template id"

        flairy_reddit = AsyncMock()
        flair_user = AsyncMock()

        # when
        testee = Flairy(flairy_reddit=flairy_reddit,
                        flairy_comment_repo=AsyncMock(),
                        automod_configuration=automod(forbid_everything=False))
        testee.flair_user = flair_user
        await testee.on_ready()
        await testee.take(mock_comment)

        # then
        flair_user.assert_called_once()
        _, kwargs = flair_user.call_args

        assert "Witness meee /u/Justind123" in kwargs['message']
        assert "some flair🦭" in kwargs['flair_text']
        assert "some template id" in kwargs['template']
        assert "color" not in kwargs

        flairy_reddit.subreddit.return_value.flair.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_flairy_results_in_random_flair(self):
        # given
        mock_comment = default_comment()
        mock_comment.body = "!FLAIRY!"
        flairy_reddit = AsyncMock()
        flair_user = AsyncMock()

        # when
        testee = Flairy(flairy_reddit=flairy_reddit,
                        automod_configuration=automod(forbid_everything=False),
                        flairy_comment_repo=AsyncMock())
        testee.flair_user = flair_user
        await testee.on_ready()
        await testee.take(mock_comment)

        # then
        flair_user.assert_called_once()
        _, kwargs = flair_user.call_args

        assert kwargs['comment'] == mock_comment
        assert len(kwargs['flair_text']) > 2
        assert len(kwargs['flair_color']) > 2
        assert "(✿☉｡☉) You didn't ask for a flair?!" in kwargs['message']
        assert "template" not in kwargs

        flairy_reddit.subreddit.return_value.flair.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_blacklisted_flair(self):
        # given
        mock_comment = default_comment()
        mock_comment.body = "!FLAIRY! 123456789 123456789 123456789 123456789 123456789 123456789 123"
        mock_comment.author_flair_text = "some flair [lock]"

        flairy_reddit = AsyncMock()

        # when
        testee = Flairy(flairy_reddit=flairy_reddit,
                        automod_configuration=automod(forbid_everything=False),
                        is_live_environment=True,
                        flairy_comment_repo=AsyncMock())
        await testee.on_ready()
        await testee.take(mock_comment)

        # then
        flairy_reddit.subreddit.return_value.flair.set.assert_not_called()

        flairy_comment = flairy_reddit.comment.return_value
        flairy_comment.reply.assert_awaited_once()
        assert "Sorry, I'm cowardly refusing to change a locked flair" in flairy_comment.reply.call_args[0][0]

