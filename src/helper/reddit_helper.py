import logging
import re
from urllib.parse import urlparse

import asyncpraw

logger = logging.getLogger("SuperstonkModerationBot.reddit_helper")

REDDIT_URL_PATTERN = re.compile(
    r"((https:\/\/)?((www|old|np|mod)\.)?(reddit|redd){1}(\.com|\.it){1}([a-zA-Z0-9\/_]+))")
POST_URL_PATTERN = re.compile(
    r"/r(?:/(?P<subreddit>\w+))/comments(?:/(?P<submission>\w+))(?:/\w+/(?P<comment>\w+))?")
MODMAIL_URL_PATTERN = re.compile(
    r"https://mod.reddit.com/mail/all/(?P<id>\w+)")


async def get_item(readonly_reddit: asyncpraw.Reddit, superstonk_subreddit, string, **kwargs):
    for u in REDDIT_URL_PATTERN.findall(string):
        if is_url(u[0]):
            item = await get_item_from_url(readonly_reddit, superstonk_subreddit, u[0])
            if item:
                return item
            else:
                continue
    return None


async def get_item_from_url(reddit: asyncpraw.Reddit, subreddit, url):
    match = MODMAIL_URL_PATTERN.search(url)
    if match:
        try:
            modmail = await subreddit.modmail(match.group("id"))
            if hasattr(modmail, "subject"):
                return modmail
        except Exception as e:
            logger.error(f"Failed to fetch modmail by ID '{match.group('id')}': {e}")

    match = POST_URL_PATTERN.search(url)
    if match and not match.group("comment"):
        try:
            return await reddit.submission(match.group("submission"))
        except Exception as e:
            logger.error(f"Failed to fetch submission by ID '{match.group('submission')}': {e}")
            return None
    elif match:
        try:
            return await reddit.comment(match.group("comment"))
        except Exception as e:
            logger.error(f"Failed to fetch comment by ID '{match.group('comment')}': {e}")
            return None
    else:
        return None


def is_url(url):
    check = urlparse(url)
    return check.scheme != "" and check.netloc != ""
