import asyncio
import logging
from datetime import datetime, timedelta
from pprint import pprint

import asyncpraw
from psaw import PushshiftAPI

from comments.comment_body_repository import CommentBodiesRepository
from comments.comment_repository import Comments
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


async def main():
    async with asyncreddit as reddit:
        redditor = await reddit.user.me()
        print(f"Logged in as {redditor.name}")
        superstonk_subreddit = await reddit.subreddit("Superstonk")

        this_month = datetime.now()
        this_month = datetime(this_month.year, this_month.month, day=1)
        last_month = this_month - relativedelta(months=1)
        month_before_last = last_month - relativedelta(months=1)

        comments = Comments()
        comment_bodies = CommentBodiesRepository()

        comment_ids_of_last_month = [f"t1_{c}" for c in await comments.ids(since=month_before_last)]
        count = 0
        async for c in reddit.info(comment_ids_of_last_month):
            await comment_bodies.store(c.id, c.body)
            count += 1
            if count % 100 == 0:
                print("stored 100")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s]: %(message)s'
)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())

"https://www.reddit.com/gallery/w0cb1r"