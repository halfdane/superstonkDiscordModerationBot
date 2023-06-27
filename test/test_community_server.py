import unittest
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, patch, AsyncMock
from asynctest import CoroutineMock

from src.community_server import check_new_entry, get_creds

async def async_gen():
    yield MagicMock()

class TestCheckNewEntry(IsolatedAsyncioTestCase):
    @patch('src.community_server.get_reddit')
    @patch('src.community_server.asyncio.sleep')
    @patch('src.community_server.bot.get_channel')
    @patch('src.community_server.get_creds')  # Patch the get_creds function
    async def test_check_new_entry(self, mock_get_creds, mock_get_channel, mock_sleep, mock_get_reddit):
        subreddit_mock = MagicMock()
        subreddit_mock.mod.modqueue = CoroutineMock(side_effect=async_gen)
        last_entry_mock = MagicMock()
        channel_mock = MagicMock()

        # Configure the mocks
        mock_get_reddit.return_value.subreddit = CoroutineMock(return_value=subreddit_mock)
        mock_get_channel.return_value = channel_mock

        # Define the required variables
        mock_get_creds.return_value = ("reddit_client_id", "reddit_client_secret", "reddit_username",
                                       "reddit_password", "subreddit_name", "channel_id", "discord_bot_token")

        # Run the function
        await check_new_entry("reddit_client_id", "reddit_client_secret", "reddit_username", "reddit_password",
                              "subreddit_name", "channel_id")


        # Assertions
        mock_get_reddit.assert_called_once_with("reddit_client_id", "reddit_client_secret", "reddit_username",
                                                "reddit_password")
        subreddit_mock.mod.modqueue.assert_called_once()
        channel_mock.send.assert_called_once()
        mock_sleep.assert_awaited_once_with(10)


if __name__ == '__main__':
    unittest.main()
