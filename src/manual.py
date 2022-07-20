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
    **configuration.qvbot_reddit_settings(),
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

def get_features(s):
    width = 3
    s = s.lower()
    s = re.sub(r'[^\w]+', '', s)
    return [s[i:i + width] for i in range(max(len(s) - width + 1, 1))]


async def main():
    async with asyncreddit as reddit:
        redditor = await reddit.user.me()
        print(f"Logged in as {redditor.name}")
        comment_repo = Comments()
        comment_body_repo = CommentBodiesRepository()

        testee = CommentBasedSpamIdentifier(comment_repo, comment_body_repo, reddit, send_discord_message=None,
                                                superstonk_moderators=["Superstonk_QV", "Roid_Rage_Smurf"])

        spammers = await testee.bla()
        for k,v in spammers.items():
            print(f"{k}: {v}")


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s]: %(message)s'
)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())

"https://www.reddit.com/gallery/w0cb1r"