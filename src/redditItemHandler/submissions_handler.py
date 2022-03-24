import asyncpraw
import disnake

from helper.discord_text_formatter import link
from redditItemHandler import Handler


class Submissions(Handler):
    def _get_reddit_stream_function(self, subreddit: asyncpraw.reddit.Subreddit):
        return subreddit.new

    async def create_embed(self, item: asyncpraw.reddit.Submission):
        url = f"https://www.reddit.com{item.permalink}"
        e = disnake.Embed(
            url=url,
            colour=disnake.Colour(0).from_rgb(207, 206, 255))

        title = getattr(item, 'title', getattr(item, 'body', ""))[:75]
        e.description = f"[Reported {item.__class__.__name__}: {title}]({url})"
        e.add_field("Redditor", link(f"https://www.reddit.com/u/{item.author}", item.author), inline=False)

        return e
