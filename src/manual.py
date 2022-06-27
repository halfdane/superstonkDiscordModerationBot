import asyncio
import os
import sys
from datetime import datetime, timedelta
from pprint import pprint

import asyncpraw
from decouple import config
from disnake.utils import escape_markdown
from psaw import PushshiftAPI

import chevron

from comments.comment_repository import Comments
from helper.links import permalink
from helper.mod_notes import __store_note, __fetch_notes, __delete_note
from helper.moderation_bot_configuration import ModerationBotConfiguration

from posts.post_repository import Posts
from superstonkDiscordModerationBot import SuperstonkModerationBot

from asyncpraw.exceptions import InvalidURL

configuration = ModerationBotConfiguration()

asyncreddit = asyncpraw.Reddit(
    **configuration.readonly_reddit_settings(),
    user_agent="com.halfdane.superstonk_moderation_bot:v0.1.1 (by u/half_dane)")


def pushshift():
    pushshift_api = PushshiftAPI()

    end_epoch = int(datetime.utcnow().timestamp())
    start_epoch = int((datetime.utcnow() - timedelta(days=70)).timestamp())
    start_epoch = int((datetime.utcnow() - timedelta(days=70)).timestamp())

    posts = pushshift_api.search_submissions(
        after=start_epoch,
        before=end_epoch,
        subreddit='Superstonk',
        metadata='true'
    )


async def main():
    async with asyncreddit as reddit:
        redditor = await reddit.user.me()
        print(f"Logged in as {redditor.name}")
        subreddit = await reddit.subreddit("superstonk")

        comment = await reddit.comment(id='idwslbp')
        print(vars(comment))



loop = asyncio.get_event_loop()
loop.run_until_complete(main())
