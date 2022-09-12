import asyncio
import logging
import re
from datetime import datetime, timedelta, date
from pprint import pprint
from unittest.mock import MagicMock

import matplotlib.scale
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

from reports_logs.stats_repository import StatisticsRepository
from reports_logs.unreport_handled_items import HandledItemsUnreporter
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from scipy.interpolate import make_interp_spline

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

        posts = Posts()
        comments = Comments()
        statistics_repository = StatisticsRepository()

        await posts.on_ready()
        await comments.on_ready()
        await statistics_repository.on_ready()

        # await statistics_repository.store_stats(await comments.stats())
        # await statistics_repository.store_stats(await posts.stats())

        df = pd.DataFrame(await statistics_repository.fetch_stats(), columns=["date", "type", "count"])

        emoj = re.compile("["
                      u"\U0001F600-\U0001F64F"  # emoticons
                      u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                      u"\U0001F680-\U0001F6FF"  # transport & map symbols
                      u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                      u"\U00002500-\U00002BEF"  # chinese char
                      u"\U00002702-\U000027B0"
                      u"\U00002702-\U000027B0"
                      u"\U000024C2-\U0001F251"
                      u"\U0001f926-\U0001f937"
                      u"\U00010000-\U0010ffff"
                      u"\u2640-\u2642"
                      u"\u2600-\u2B55"
                      u"\u200d"
                      u"\u23cf"
                      u"\u23e9"
                      u"\u231a"
                      u"\ufe0f"  # dingbats
                      u"\u3030"
                      "]+", re.UNICODE)

        for flair in df.type.unique():
            f = df[df.type == flair]
            f = f[["date", "count"]]
            f = f.set_index('date')

            print(f"flair {flair} {f.shape} {f.dtypes}")

            fig, ax = plt.subplots()
            ax.plot(f.resample('D').sum(),  color="orange", label='daily')
            ax2 = ax.twinx()
            ax2.plot(f.resample('W').sum(), color='blue', label='weekly')
            ax.set_ylim(bottom=0)
            ax2.set_ylim(bottom=0)

            plt.xlabel('Date')
            plt.title(f"{emoj.sub('', flair)} submissions")
            fig.autofmt_xdate()
            fig.legend()
            filename = ''.join(e for e in flair if e.isalnum())
            plt.savefig(f"stats/{filename}.png")
            plt.close(fig)

        await statistics_repository.shutdown()


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s]: %(message)s'
)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
