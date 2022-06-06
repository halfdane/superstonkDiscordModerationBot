from datetime import datetime, timedelta

import disnake
import yaml
import chevron

from disnake import Embed

from helper.links import permalink, make_safe
from redditItemHandler import Handler


class RAllStickyCreator(Handler):
    _interval = timedelta(hours=24)

    def __init__(self, add_reactions_to_discord_message=None, qvbot_reddit=None,
                 superstonk_subreddit=None,
                 report_channel=None, is_live_environment=None, **kwargs):
        super().__init__()
        self.qvbot_reddit = qvbot_reddit
        self.report_channel = report_channel
        self.add_reactions_to_discord_message = add_reactions_to_discord_message
        self.is_live_environment = is_live_environment
        self.superstonk_subreddit = superstonk_subreddit
        self.r_all_comment = None

    async def on_ready(self, scheduler, **kwargs):
        self._logger.info("Ready to react when a post hits r/all")
        scheduler.add_job(self.fetch_config_from_wiki, "cron", minute="4-59/10", next_run_time=datetime.now())

    async def take(self, item):
        subreddit = item.subreddit
        if subreddit == "SuperStonk" and await self.__needs_r_all_comment(item):
            await self.report_r_all_was_hit(item)
            post_from_qbots_view = await self.qvbot_reddit.submission(item.id, fetch=False)

            if self.is_live_environment and self.active:
                self._logger.info(f"adding r/all comment to {permalink(item)}")
                sticky = await post_from_qbots_view.reply(self.r_all_comment)
                await sticky.mod.distinguish(how="yes", sticky=True)
                await sticky.mod.ignore_reports()
            else:
                self._logger.info(f"NOT adding r/all comment to {permalink(item)}")

    async def report_r_all_was_hit(self, item):
        author = getattr(item.author, 'name', str(item.author))
        embed = Embed(colour=disnake.Colour(0).from_rgb(207, 206, 255))
        embed.description = f"**[NEW ON R/ALL: {make_safe(item.title)}]({permalink(item)})**  \n"
        embed.add_field("Redditor", f"[{author}](https://www.reddit.com/u/{author})", inline=False)

        msg = await self.report_channel.send(embed=embed)
        await self.add_reactions_to_discord_message(msg)

    async def fetch_config_from_wiki(self):
        wiki_page = await self.superstonk_subreddit.wiki.get_page("qualityvote")
        wiki_config_text = wiki_page.content_md
        wiki_config = yaml.safe_load(wiki_config_text)
        self.r_all_comment = wiki_config['r_all_comment']

    async def __needs_r_all_comment(self, submission):
        await submission.load()
        myself = await self.qvbot_reddit.user.me()
        has_comments = len(submission.comments) > 0

        if has_comments:
            first_comment = submission.comments[0]
            missing_sticky = not first_comment.stickied
            is_qv_sticky = first_comment.author.name == myself.name
            isnot_rall_comment = 'r/all' not in getattr(first_comment, 'body', "")

            return missing_sticky or (is_qv_sticky and isnot_rall_comment)
        else:
            return True
