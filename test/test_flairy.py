from superstonkDiscordModerationBot import SuperstonkModerationBot
from redditItemHandler.flairy import Flairy
from unittest.mock import patch, Mock, AsyncMock
from asyncpraw.models import Comment
import pytest


class TestFlairyRegex:

    def default_bot(self, mock_bot):
        mock_bot.flairy_reddit.comment = AsyncMock()
        mock_bot.flairy_reddit.comment.return_value = AsyncMock()
        mock_bot.flairy_channel.send = AsyncMock()
        mock_bot.is_forbidden_comment_message.return_value = False

    def default_comment(self, mock_comment):
        mock_comment.id = "some id"
        mock_comment.body = "!FLAIRY! some flair"
        mock_comment.author.name = ""


    @patch('superstonkDiscordModerationBot.SuperstonkModerationBot', autospec=True)
    @patch('asyncpraw.models.Comment')
    @pytest.mark.asyncio
    async def test_too_long(self, mock_comment, mock_bot):
        # given
        self.default_comment(mock_comment)
        mock_comment.id = "some id"
        mock_comment.body = "!FLAIRY! 123456789 123456789 123456789 123456789 123456789 123456789 1234"

        self.default_bot(mock_bot)

        # when
        testee = Flairy(mock_bot)
        await testee.take(mock_comment)

        # then
        mock_bot.flairy_reddit.comment.assert_called_once_with("some id", fetch=False)

        flairy_comment = mock_bot.flairy_reddit.comment.return_value
        flairy_comment.reply.assert_called_once()

        assert "THE FLAIR TEXT IS TOO LONG" in flairy_comment.reply.call_args[0][0]

        mock_bot.flairy_channel.send.assert_not_called()

    @patch('superstonkDiscordModerationBot.SuperstonkModerationBot', autospec=True)
    @patch('asyncpraw.models.Comment')
    @pytest.mark.asyncio
    async def test_is_forwarded_to_discord(self, mock_comment, mock_bot):
        # given
        self.default_comment(mock_comment)
        mock_comment.body = "!FLAIRY! 123456789 123456789 123456789 123456789 123456789 123456789 123"

        self.default_bot(mock_bot)

        # when
        testee = Flairy(mock_bot)
        await testee.take(mock_comment)

        # then
        mock_bot.flairy_reddit.comment.assert_not_called()
        mock_bot.flairy_channel.send.assert_called_once()



