from datetime import datetime, timedelta

import disnake
from disnake import Embed

from redditItemHandler import Handler
from redditItemHandler.abstract_handler import permalink

REMOVAL_COMMENT = """
Your post was removed by a moderator because you have reached the limit of posts per user in 24 hours.

Every ape may submit up to 7 posts in a 24 hour window, and you already had your fill. 
Please take a little break before attempting to post again.  

🦍🦍🦍🦍🦍🦍

If you are repeatedly having posts/comments removed for rules violation, you will be banned either permanently or temporarily.

If you feel this removal was unwarranted, please contact us via Mod Mail: https://www.reddit.com/message/compose?to=/r/Superstonk

Thanks for being a member of r/Superstonk 💎🙌🚀
"""


class PostCountLimiter(Handler):
    _interval = timedelta(hours=24)

    def __init__(self, bot, post_repo=None):
        super().__init__(bot)
        self.post_repo = post_repo

    async def take(self, item):
        if await self.post_repo.contains(item):
            return

        author_name = getattr(item.author, 'name', str(item.author))
        yesterday = datetime.utcnow() - timedelta(hours=24)
        posts = [p async for p in self.post_repo.fetch(author=author_name, since=yesterday, only_counting_to_limit=True)]

        if len(posts) > 7:
            self._logger.info(f"Oops, looks like {author_name} is posting a lot: {posts}")
            sticky = await item.reply(REMOVAL_COMMENT)
            sticky.mod.distinguish(how="yes", sticky=True)
            sticky.mod.ignore_reports()

            await item.mod.remove(spam=True, mod_note="post count limit reached")
            await self.post_repo.do_not_count_to_limit(item)
            await self.report_infraction(author_name, item)

    async def report_infraction(self, author, item):
        embed = Embed(colour=disnake.Colour(0).from_rgb(207, 206, 255))
        embed.description = f"**Prevented {author} from posting {permalink(item)}**  \n"
        embed.add_field("Redditor", f"[{author}](https://www.reddit.com/u/{author})", inline=False)

        msg = await self.bot.report_channel.send(embed=embed)
        await self.bot.add_reactions(msg)
