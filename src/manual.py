import asyncio
import logging
import re
import sqlite3
from datetime import datetime, timedelta, date
from pprint import pprint
from unittest.mock import MagicMock

import matplotlib.scale
from simhash import Simhash, SimhashIndex
import aiosqlite

import asyncpraw
from psaw import PushshiftAPI

from automod_configuration import AutomodConfiguration
from comments.comment_body_repository import CommentBodiesRepository
from comments.comment_repository import Comments
from discordReactionHandlers.modnote_reaction import ModNoteReaction
from helper.item_helper import permalink, remove_emojis
from helper.moderation_bot_configuration import ModerationBotConfiguration
from modmail.HighlightMailNotification import HighlightMailNotification
from modmail.__init import modmail_state
from modmail.modmail_notification import ModmailNotification
from posts.post_repository import Posts
from qv_bot.__init import get_qv_comment
from modmail.hanami_config import HanamiConfiguration
from qv_bot.qv_bot_configuration import QualityVoteBotConfiguration
from qv_bot.require_qv_response import RequireQvResponse
from reports_logs.approve_old_modqueue_items import ApproveOldModqueueItems
from reports_logs.reported_comments_remover import ReportedCommentsRemover
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta
from urllib.parse import urlparse

from reports_logs.unreport_handled_items import HandledItemsUnreporter
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from scipy.interpolate import make_interp_spline

configuration = ModerationBotConfiguration()

asyncreddit = asyncpraw.Reddit(
    **configuration.qvbot_reddit_settings(),
    user_agent="com.halfdane.superstonk_moderation_bot:v0.xx (by u/half_dane)")

COMPONENTS = {}
COMPONENTS.update(configuration)


async def deb(description_beginning, fields):
    print(f"{description_beginning}")
    print(fields)

async def store(item, db):
    if item.author is not None:
        meltie = item.author.name
        await db.execute('INSERT INTO trolls(USERNAME, SOURCE) VALUES (?, ?) ON CONFLICT(USERNAME, SOURCE) DO NOTHING', (meltie, item.subreddit.display_name))
        await db.commit()
        return meltie
    else:
        return None



async def main():
    async with asyncreddit as reddit:
        redditor = await reddit.user.me()
        print(f"Logged in as {redditor.name}")

        for i in ['DRSyourGME']:
            await handle_subreddit(await reddit.subreddit(i))


async def handle_subreddit(subreddit):
    async with aiosqlite.connect("trolls.db") as db:
        await db.execute('create table if not exists trolls (USERNAME, SOURCE, PRIMARY KEY(USERNAME, SOURCE));')

        async for submission in subreddit.hot(limit=1000):
            await store(submission, db)
            print(submission.title, submission.author, submission.subreddit.display_name)

            while True:
                try:
                    await submission.comments.replace_more(limit=None)
                    break
                except TypeError as e:
                    break
                except Exception as e:
                    print("Handling replace_more exception", type(e), e)
                    await asyncio.sleep(1)

            comments = await submission.comments()
            await comments.replace_more(limit=None)
            all_comments = await comments.list()
            for comment in all_comments:
                await store(comment, db)


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s]: %(message)s'
)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
