import asyncio
import os
import sys
from datetime import datetime, timedelta
from pprint import pprint

import asyncpraw
from decouple import config
from disnake.utils import escape_markdown
from psaw import PushshiftAPI

import chevron

from comments.comment_repository import Comments
from helper.links import permalink
from helper.mod_notes import __store_note, __fetch_notes, __delete_note
from helper.moderation_bot_configuration import ModerationBotConfiguration

from posts.post_repository import Posts
from superstonkDiscordModerationBot import SuperstonkModerationBot

from asyncpraw.exceptions import InvalidURL

configuration = ModerationBotConfiguration()

asyncreddit = asyncpraw.Reddit(
    **configuration.readonly_reddit_settings(),
    user_agent="com.halfdane.superstonk_moderation_bot:v0.1.1 (by u/half_dane)")


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


post_limit_reached_comment = """Your post was removed by a moderator because you have reached the limit of posts per user in 24 hours.

Every ape may submit up to 7 posts in a 24 hour window, and you already had your fill. 
Please take a little break before attempting to post again.  

List of posts that count towards that limit:

{{list_of_posts}}

List of posts that don't count towards the limit:

{{ignored_posts}}

🦍🦍🦍🦍🦍🦍

If you are repeatedly having posts/comments removed for rules violation, you will be banned either permanently or temporarily.

If you feel this removal was unwarranted, please contact us via Mod Mail: https://www.reddit.com/message/compose?to=/r/Superstonk

Thanks for being a member of r/Superstonk 💎🙌🚀
"""


async def _post_to_string(post):
    created_utc = datetime.utcfromtimestamp(post.created_utc).strftime("%m/%d/%Y, %H:%M:%S")
    return f"- **{created_utc}**: https://www.reddit.com/r/Superstonk/comments/{post.id}"


async def main():
    async with asyncreddit as reddit:
        redditor = await reddit.user.me()
        print(f"Logged in as {redditor.name}")
        subreddit = await reddit.subreddit("superstonk")

        note = """
        """

        submission = await reddit.submission(
            url='https://new.reddit.com/r/Superstonk/comments/vjflm7/here_we_go_bill_9_10_big_banks_and_risk/')
        print(permalink(submission))


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
