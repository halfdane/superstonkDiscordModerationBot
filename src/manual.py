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
from qv_bot.qv_bot_configuration import QualityVoteBotConfiguration
from qv_bot.require_qv_response import RequireQvResponse
from reports_logs.approve_old_modqueue_items import ApproveOldModqueueItems
from reports_logs.reported_comments_remover import ReportedCommentsRemover
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta

configuration = ModerationBotConfiguration()

asyncreddit = asyncpraw.Reddit(
    **configuration.qvbot_reddit_settings(),
    user_agent="com.halfdane.superstonk_moderation_bot:v0.xx (by u/half_dane)")


COMPONENTS={}
COMPONENTS.update(configuration)

async def deb(description_beginning, fields):
    print(f"{description_beginning}")
    print(fields)

async def main():
    async with asyncreddit as reddit:
        redditor = await reddit.user.me()
        print(f"Logged in as {redditor.name}")
        subreddit_name_ = COMPONENTS["subreddit_name"]
        superstonk_subreddit = await reddit.subreddit(subreddit_name_)

        configuration = QualityVoteBotConfiguration(superstonk_subreddit)
        await configuration.fetch_config_from_wiki()
        require_qv_response = RequireQvResponse(reddit, None, configuration)

        p = await reddit.submission(url="https://new.reddit.com/r/testsubsuperstonk/comments/wvn9i7/test_for_response_to_qv_bot/")

        await require_qv_response.inspect_individual_post(p, datetime.utcnow())



logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s]: %(message)s'
)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
