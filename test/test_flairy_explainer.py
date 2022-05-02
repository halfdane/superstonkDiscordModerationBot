from unittest.mock import patch, AsyncMock, MagicMock
import asyncpraw
import pytest
from redditItemHandler.flairy import FlairyExplainerCommand, Flairy


class TestFlairyExplainer:

    def default_comment(self):
        mock_comment: asyncpraw.models.Comment = MagicMock()
        mock_comment.id = "some id"
        mock_comment.author.name = ""
        mock_comment.refresh = AsyncMock()
        return mock_comment

    @pytest.mark.asyncio
    async def test_happy_path(self):
        mock_reddit = MagicMock()
        mock_reddit.comment = AsyncMock()
        testee = FlairyExplainerCommand(mock_reddit, ['some', 'weird', 'color'])

        # given
        mock_comment = self.default_comment()
        mock_comment.body = "If you're looking for an explainer on how to get or change a flair, just tag the u/Superstonk-Flairy"

        # when
        await testee.handled(mock_comment.body, mock_comment, True)

        # then
        mock_reddit.comment.assert_called_once_with("some id", fetch=False)

        flairy_comment = mock_reddit.comment.return_value
        flairy_comment.reply.assert_called_once()



