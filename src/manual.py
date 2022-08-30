import asyncio
import logging
import re
from datetime import datetime, timedelta
from pprint import pprint
from unittest.mock import MagicMock

from simhash import Simhash, SimhashIndex

import asyncpraw
from psaw import PushshiftAPI

from automod_configuration import AutomodConfiguration
from comments.comment_based_spam_identifier import CommentBasedSpamIdentifier
from comments.comment_body_repository import CommentBodiesRepository
from comments.comment_repository import Comments
from helper.item_helper import permalink
from helper.moderation_bot_configuration import ModerationBotConfiguration
from modmail.HighlightMailNotification import HighlightMailNotification
from modmail.__init import modmail_state
from modmail.modmail_notification import ModmailNotification
from qv_bot.__init import get_qv_comment
from modmail.hanami_config import HanamiConfiguration
from qv_bot.qv_bot_configuration import QualityVoteBotConfiguration
from qv_bot.require_qv_response import RequireQvResponse
from reports_logs.approve_old_modqueue_items import ApproveOldModqueueItems
from reports_logs.reported_comments_remover import ReportedCommentsRemover
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta
from urllib.parse import urlparse

configuration = ModerationBotConfiguration()

asyncreddit = asyncpraw.Reddit(
    **configuration.readonly_reddit_settings(),
    user_agent="com.halfdane.superstonk_moderation_bot:v0.xx (by u/half_dane)")

COMPONENTS = {}
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

        configuration = HanamiConfiguration(superstonk_subreddit)
        await configuration.on_ready(MagicMock())
        notification = ModmailNotification(superstonk_subreddit, None, configuration)

        async for item in superstonk_subreddit.mod.stream.modmail_conversations():
            m = await superstonk_subreddit.modmail(item.id)
            await notification.take(item)


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s]: %(message)s'
)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
