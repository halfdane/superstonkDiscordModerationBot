import asyncpraw
import disnake

from helper.discord_text_formatter import link
from redditItemHandler import Handler


class Comments(Handler):
    def _get_reddit_stream_function(self, subreddit: asyncpraw.reddit.Subreddit):
        return subreddit.comments

    async def create_embed(self, item: asyncpraw.reddit.Comment):
        url = f"https://www.reddit.com{item.permalink}"
        e = disnake.Embed(
            url=url,
            colour=disnake.Colour(0).from_rgb(207, 206, 255))

        title = getattr(item, 'title', getattr(item, 'body', ""))[:75]
        e.description = f"[Reported {item.__class__.__name__}: {title}]({url})"
        e.add_field("Redditor", link(f"https://www.reddit.com/u/{item.author}", item.author), inline=False)

        return e
