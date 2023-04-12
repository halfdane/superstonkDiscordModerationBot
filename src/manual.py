import asyncio
import logging
from datetime import datetime

import asyncpraw

from helper.moderation_bot_configuration import ModerationBotConfiguration

configuration = ModerationBotConfiguration()

asyncreddit = asyncpraw.Reddit(
    **configuration.qvbot_reddit_settings(),
    user_agent="com.halfdane.superstonk_moderation_bot:v0.xx (by u/half_dane)")

COMPONENTS = {}
COMPONENTS.update(configuration)


async def main():
    async with asyncreddit as reddit:
        redditor = await reddit.user.me()
        print(f"Logged in as {redditor.name}")

        subreddit = await reddit.subreddit('superstonk')

        async for log in subreddit.mod.stream.log(action='banuser'):
            created_utc = datetime.utcfromtimestamp(log.created_utc).strftime("%Y/%m/%d %H:%M:%S")
            # print(f"{created_utc}: {log.details} ban")
            print(created_utc, log.details, vars(log))


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s]: %(message)s'
)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
