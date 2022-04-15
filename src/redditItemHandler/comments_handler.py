from functools import lru_cache

import disnake

import discordReaction
from helper.discord_text_formatter import link
from redditItemHandler import Handler
from disnake.utils import escape_markdown


class Comments(Handler):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(self.bot.reddit, self.bot.subreddit)
        self._flairy_detection = "!flairy!"

    async def handle(self, channels):
        self._logger.info(f"[{self._current_task.get_name()}] Cached: {self.send_flairy_request.cache_info()}")
        async for comment in self._subreddit.stream.comments():
            if self._flairy_detection.lower() in comment.body.lower() and comment.author not in self.bot.moderators:
                await self.send_flairy_request(comment)

    @lru_cache(maxsize=5)
    async def send_flairy_request(self, comment):
        self._logger.info(f"[{self._current_task.get_name()}] Sending flair request {comment}")
        url = f"https://www.reddit.com{comment.permalink}"
        e = disnake.Embed(
            url=url,
            colour=disnake.Colour(0).from_rgb(207, 206, 255))
        e.description = f"[Flair Request: {escape_markdown(comment.body)}]({url})"
        e.add_field("Redditor", link(f"https://www.reddit.com/u/{comment.author}", comment.author), inline=False)
        for channel in self.bot.flairy_channels:
            msg = await channel.send(embed=e)
            reactions = discordReaction.FLAIR_REACTIONS + discordReaction.GENERIC_REACTIONS + discordReaction.USER_REACTIONS
            await discordReaction.add_reactions(msg, reactions=reactions)
