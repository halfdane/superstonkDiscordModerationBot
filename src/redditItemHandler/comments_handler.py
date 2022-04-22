import disnake

import discordReaction
from helper.discord_text_formatter import link
from redditItemHandler import Handler
from disnake.utils import escape_markdown


class Comments(Handler):
    def __init__(self, bot):
        super().__init__(bot)
        self._flairy_detection = "!flairy!"

    async def handle(self):
        async for comment in self.bot.subreddit.stream.comments():
            if self._flairy_detection.lower() in comment.body.lower() and comment.author not in self.bot.moderators:
                if await self.is_new_item(self.bot.flairy_channel, comment):
                    self._logger.info(f"Sending flair request {comment}")
                    await self.send_flairy_request(comment)
                else:
                    self._logger.info(f"Skipping over already existing request {comment}")
                    continue

    async def send_flairy_request(self, comment):
        url = f"https://www.reddit.com{comment.permalink}"
        e = disnake.Embed(
            url=url,
            colour=disnake.Colour(0).from_rgb(207, 206, 255))
        e.description = f"[Flair Request: {escape_markdown(comment.body)}]({url})"
        e.add_field("Redditor", link(f"https://www.reddit.com/u/{comment.author}", comment.author), inline=False)
        msg = await self.bot.flairy_channel.send(embed=e)
        reactions = discordReaction.FLAIR_REACTIONS + discordReaction.GENERIC_REACTIONS + discordReaction.USER_REACTIONS
        await discordReaction.add_reactions(msg, reactions=reactions)
