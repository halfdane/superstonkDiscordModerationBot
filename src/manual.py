import asyncio
import os
import sys
from datetime import datetime, timedelta
from pprint import pprint

import asyncpraw
from disnake.utils import escape_markdown
from psaw import PushshiftAPI

import chevron
from dateutil.relativedelta import relativedelta

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


COMPONENTS={}
COMPONENTS.update(configuration)

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

        subreddit_name_ = COMPONENTS["subreddit_name"]
        print(type(subreddit_name_))
        subreddit = await reddit.subreddit(subreddit_name_)

        async for item in subreddit.stream.submissions():
            print(f"got item {item}")



loop = asyncio.get_event_loop()
loop.run_until_complete(main())
