from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from redditItemHandler.flairy import Flairy


class TestFlairy:

    def default_bot(self):
        mock_bot = AsyncMock()

        mock_bot.is_forbidden_comment_message = MagicMock()

        mock_bot.flairy_channel.history = MagicMock()
        mock_bot.flairy_channel.history.filter.return_value.__aiter__.return_value = []

        mock_bot.is_forbidden_comment_message.return_value = False

        return mock_bot

    def default_comment(self, mock_comment):
        mock_comment.id = "some id"
        mock_comment.body = "!FLAIRY! some flair"
        mock_comment.author.name = ""
        mock_comment.author_flair_text = "existing flair"
        mock_comment.refresh = AsyncMock()

    @patch('asyncpraw.models.Comment')
    @pytest.mark.asyncio
    async def test_happy_path(self, mock_comment):
        # given
        self.default_comment(mock_comment)
        mock_comment.body = "!FLAIRY! 123456789 123456789 123456789 123456789 123456789 123456789 123"

        mock_bot = self.default_bot()

        # when
        testee = Flairy(bot=mock_bot)
        await testee.take(mock_comment)

        # then
        mock_bot.flairy_reddit.comment.assert_not_called()
        mock_bot.flairy_channel.send.assert_awaited_once()

    @patch('asyncpraw.models.Comment')
    @pytest.mark.asyncio
    async def test_flair_too_long(self, mock_comment):
        # given
        self.default_comment(mock_comment)
        mock_comment.id = "some id"
        mock_comment.body = "!FLAIRY! 123456789 123456789 123456789 123456789 123456789 123456789 1234"

        mock_bot = self.default_bot()

        # when
        testee = Flairy(bot=mock_bot)
        await testee.take(mock_comment)

        # then
        mock_bot.flairy_reddit.comment.assert_called_once_with("some id", fetch=False)

        flairy_comment = mock_bot.flairy_reddit.comment.return_value
        flairy_comment.reply.assert_called_once()

        assert "THE FLAIR TEXT IS TOO LONG" in flairy_comment.reply.call_args[0][0]

        mock_bot.flairy_channel.send.assert_not_called()

    @patch('asyncpraw.models.Comment')
    @pytest.mark.asyncio
    async def test_flair_contains_restricted_word(self, mock_comment):
        # given
        self.default_comment(mock_comment)
        mock_bot = self.default_bot()

        mock_bot.is_forbidden_comment_message.return_value = True

        # when
        testee = Flairy(bot=mock_bot)
        await testee.take(mock_comment)

        # then
        mock_bot.flairy_channel.send.assert_not_called()

    @patch('asyncpraw.models.Comment')
    @pytest.mark.asyncio
    async def test_empty_flairy_results_in_random_flair(self, mock_comment):
        # given
        self.default_comment(mock_comment)
        mock_bot = self.default_bot()
        mock_comment.body = "!FLAIRY!"

        # when
        testee = Flairy(bot=mock_bot)
        testee.flair_user = AsyncMock()
        await testee.take(mock_comment)

        # then
        testee.flair_user.assert_called_once()
        _, kwargs = testee.flair_user.call_args

        assert kwargs['comment'] == mock_comment
        assert len(kwargs['flair_text']) > 2
        assert len(kwargs['flair_color']) > 2
        assert "(✿☉｡☉) You didn't ask for a flair?!" in kwargs['message']
        assert "template" not in kwargs

    @patch('asyncpraw.models.Comment')
    @pytest.mark.asyncio
    async def test_wrong_color_results_in_additional_message(self, mock_comment):
        # given
        self.default_comment(mock_comment)
        mock_comment.body = "!FLAIRY! requesting wrong color: orange"

        mock_bot = self.default_bot()

        # when
        testee = Flairy(bot=mock_bot)
        await testee.take(mock_comment)

        # then
        flairy_comment = mock_bot.flairy_reddit.comment.return_value
        flairy_comment.reply.assert_called_once()
        assert "ORANGE IS NOT A VALID COLOR!" in flairy_comment.reply.call_args[0][0]
        mock_bot.flairy_channel.send.assert_called_once()

    @patch('asyncpraw.models.Comment')
    @pytest.mark.asyncio
    async def test_flair_clearing(self, mock_comment):
        # given
        self.default_comment(mock_comment)
        mock_comment.body = "! FLAIRY : CLEARME! whatever happens here"

        mock_bot = self.default_bot()

        # when
        testee = Flairy(bot=mock_bot)
        await testee.take(mock_comment)

        # then
        flairy_comment = mock_bot.flairy_reddit.comment.return_value
        flairy_comment.reply.assert_called_once()
        assert "Clearing the flair as requested" in flairy_comment.reply.call_args[0][0]

        mock_bot.flairy_channel.send.assert_not_called()

        mock_bot.flairy_reddit.subreddit.return_value.flair.delete.assert_called_once()

    @patch('asyncpraw.models.Comment')
    @pytest.mark.asyncio
    async def test_flair_seal_appending(self, mock_comment):
        # given
        self.default_comment(mock_comment)
        mock_comment.body = "!FLAIRY:SEALME! whatever happens here"
        mock_comment.author_flair_text = "some flair"
        mock_comment.author_flair_template_id = "some template id"

        mock_bot = self.default_bot()

        # when
        testee = Flairy(bot=mock_bot)
        testee.flair_user = AsyncMock()
        await testee.take(mock_comment)

        # then
        testee.flair_user.assert_called_once()
        _, kwargs = testee.flair_user.call_args

        assert "Witness meee /u/Justind123" in kwargs['message']
        assert "some flair🦭" in kwargs['flair_text']
        assert "some template id" in kwargs['template']
        assert "color" not in kwargs

        mock_bot.flairy_channel.send.assert_not_called()

        mock_bot.flairy_reddit.subreddit.return_value.flair.delete.assert_not_called()

