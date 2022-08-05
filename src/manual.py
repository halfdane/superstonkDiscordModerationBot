import asyncio
import logging
import re
from datetime import datetime, timedelta
from pprint import pprint
from simhash import Simhash, SimhashIndex

import asyncpraw
from psaw import PushshiftAPI

from comments.comment_based_spam_identifier import CommentBasedSpamIdentifier
from comments.comment_body_repository import CommentBodiesRepository
from comments.comment_repository import Comments
from helper.links import permalink
from helper.moderation_bot_configuration import ModerationBotConfiguration
from reports_logs.approve_old_modqueue_items import ApproveOldModqueueItems
from reports_logs.reported_comments_remover import ReportedCommentsRemover
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta

configuration = ModerationBotConfiguration()

asyncreddit = asyncpraw.Reddit(
    **configuration.readonly_reddit_settings(),
    user_agent="com.halfdane.superstonk_moderation_bot:v0.xx (by u/half_dane)")


COMPONENTS={}
COMPONENTS.update(configuration)

async def deb(description_beginning, fields):
    print(f"{description_beginning}")
    print(fields)

async def main():
    async with asyncreddit as reddit:
        redditor = await reddit.user.me()
        superstonk_subreddit = await reddit.subreddit("Superstonk")
        print(f"Logged in as {redditor.name}")
        comment_repo = Comments()
        comment_body_repo = CommentBodiesRepository()


        testee = ReportedCommentsRemover(superstonk_subreddit, reddit, send_discord_message=deb, is_live_environment=True)

        p = await reddit.submission(url="https://new.reddit.com/r/Superstonk/comments/wgcmnt/")

        # await testee.handle_post_ids([p.name])

        # c = await reddit.comment(url="https://new.reddit.com/r/Superstonk/comments/wgcmnt/comment/iiz1u6n/")
        # print(c.body)
        # await c.mod.remove()



logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s]: %(message)s'
)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
