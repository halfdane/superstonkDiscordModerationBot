from datetime import datetime, timedelta

import disnake
from disnake import Embed

from helper.links import permalink
from redditItemHandler import Handler

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

    def __init__(self, add_reactions_to_discord_message=None, post_repo=None, qvbot_reddit=None, report_channel=None, is_live_environment=None, **kwargs):
        super().__init__()
        self.post_repo = post_repo
        self.qvbot_reddit = qvbot_reddit
        self.report_channel = report_channel
        self.add_reactions_to_discord_message = add_reactions_to_discord_message
        self.is_live_environment = is_live_environment

    async def on_ready(self):
        self._logger.info("Ready to limit post count")

    async def take(self, item):
        author_name = getattr(item.author, 'name', str(item.author))
        yesterday = datetime.utcnow() - timedelta(hours=24)
        posts = await self.post_repo.fetch(author=author_name, since=yesterday)
        posts_that_count = list(filter(lambda p: p.count_to_limit, posts))

        if len(posts_that_count) > 7:
            self._logger.info(f"Oops, looks like {author_name} is posting a lot: {posts}")
            item_from_qvbot_view = await self.qvbot_reddit.submission(item.id, fetch=False)

            if self.is_live_environment:
                sticky = await item_from_qvbot_view.reply(REMOVAL_COMMENT)
                await sticky.mod.distinguish(how="yes", sticky=True)
                await sticky.mod.ignore_reports()
                await item_from_qvbot_view.mod.remove(spam=False, mod_note="post count limit reached")

            await self.post_repo.do_not_count_to_limit(item)
            await self.report_infraction(author_name, item)

    async def report_infraction(self, author, item):
        embed = Embed(colour=disnake.Colour(0).from_rgb(207, 206, 255))
        embed.description = f"**Prevented {author} from posting {permalink(item)}**  \n"
        embed.add_field("Redditor", f"[{author}](https://www.reddit.com/u/{author})", inline=False)

        msg = await self.report_channel.send(embed=embed)
        await self.add_reactions_to_discord_message(msg)
