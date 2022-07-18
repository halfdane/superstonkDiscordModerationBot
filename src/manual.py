import asyncio
import logging
import re
from datetime import datetime, timedelta
from pprint import pprint
from simhash import Simhash, SimhashIndex

import asyncpraw
from psaw import PushshiftAPI

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

def get_features(self, s):
    width = 3
    s = s.lower()
    s = re.sub(r'[^\w]+', '', s)
    return [s[i:i + width] for i in range(max(len(s) - width + 1, 1))]


async def main():
    async with asyncreddit as reddit:
        redditor = await reddit.user.me()
        print(f"Logged in as {redditor.name}")
        superstonk_subreddit = await reddit.subreddit("Superstonk")

        comment_repo = Comments()
        comment_body_repo = CommentBodiesRepository()
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        ids = await comment_repo.ids(since=last_hour)

        index = SimhashIndex(objs={}, k=3)

        for id in ids:
            body = await comment_body_repo.fetch_body(id)

            features = get_features(body)
            if len(features) == 1 and features[0] == "":
                continue

            simhash = Simhash(features)
            dups = index.get_near_dups(simhash)

            dup_items = [permalink(await reddit.comment(id=dub_id)) for dub_id in dups]
            if len(dup_items) > 3:
                print(dup_items)

            index.add(id, simhash)


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s]: %(message)s'
)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())

"https://www.reddit.com/gallery/w0cb1r"