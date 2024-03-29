from unittest.mock import patch, AsyncMock, MagicMock
import asyncpraw
import pytest
from comments.flairy import FlairyExplainerCommand, Flairy


class TestFlairyExplainer:

    def default_comment(self):
        mock_comment: asyncpraw.models.Comment = MagicMock()
        mock_comment.id = "some id"
        mock_comment.author.name = ""
        mock_comment.refresh = AsyncMock()
        return mock_comment

    @pytest.mark.asyncio
    async def test_happy_path(self):

        reddit_username = "flairy's_reddit_username"
        mock_reddit = MagicMock()
        mock_reddit.comment = AsyncMock()
        testee = FlairyExplainerCommand(mock_reddit, reddit_username)

        # given
        mock_comment = self.default_comment()
        mock_comment.body = f"If you're looking for an explainer, just tag the u/{reddit_username}"

        # when
        await testee.handled(mock_comment.body, mock_comment, True)

        # then
        mock_reddit.comment.assert_called_once_with("some id", fetch=False)

        flairy_comment = mock_reddit.comment.return_value
        flairy_comment.reply.assert_awaited_once()

        args, _ = flairy_comment.reply.call_args
        assert len(args) == 1
        assert "!FLAIRY!🚀" in args[0]
        assert "red, blue, pink, yellow, green, black, white" in args[0]
        assert f"{reddit_username}" in args[0]
        assert "`!FLAIRY!`" in args[0]
        assert "`!FLAIRY:CLEARME!`" in args[0]
        assert "`!FLAIRY:SEALME!`" in args[0]
        assert "[lock]" in args[0]


