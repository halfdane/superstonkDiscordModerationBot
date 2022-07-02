import asyncio
import logging
from datetime import datetime, timedelta

import asyncpraw
from psaw import PushshiftAPI

from helper.moderation_bot_configuration import ModerationBotConfiguration
from reports_logs.approve_old_modqueue_items import ApproveOldModqueueItems
from reports_logs.reported_comments_remover import ReportedCommentsRemover

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

        approver = ApproveOldModqueueItems(subreddit_name="Superstonk", qvbot_reddit=reddit, send_discord_message=None)
        await approver.handle_obsolete_modqueue_items()


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s]: %(message)s'
)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
