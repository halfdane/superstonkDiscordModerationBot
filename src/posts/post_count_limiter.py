from datetime import datetime, timedelta

import disnake
from disnake import Embed

import yaml
import chevron

from helper.links import permalink
from reddit_item_handler import Handler

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

    def __init__(self, add_reactions_to_discord_message, post_repo, qvbot_reddit,
                 report_channel, is_live_environment,
                 superstonk_subreddit, **kwargs):
        super().__init__()
        self.post_repo = post_repo
        self.qvbot_reddit = qvbot_reddit
        self.report_channel = report_channel
        self.add_reactions_to_discord_message = add_reactions_to_discord_message
        self.is_live_environment = is_live_environment
        self.superstonk_subreddit = superstonk_subreddit
        self.post_limit_reached_comment = REMOVAL_COMMENT

    async def on_ready(self, scheduler, **kwargs):
        self._logger.info("Ready to limit post count")
        scheduler.add_job(self.fetch_config_from_wiki, "cron", minute="6-59/10", next_run_time=datetime.now())

    async def take(self, item):
        author_name = getattr(item.author, 'name', str(item.author))
        yesterday = datetime.utcnow() - timedelta(hours=24)
        posts = await self.post_repo.fetch(author=author_name, since=yesterday)
        posts_that_count = list(filter(lambda p: p.count_to_limit, posts))

        if len(posts_that_count) > 7:

            list_of_posts = "    \n".join([f"- **{post['created_utc']}**: {permalink(post)}"
                for post in sorted(posts_that_count, key=lambda v: v['created_utc'])])

            model = {'list_of_posts': list_of_posts}
            removal_comment = chevron.render(self.post_limit_reached_comment, model)

            self._logger.info(f"Oops, looks like {author_name} is posting a lot: {removal_comment}")

            if self.is_live_environment:
                item_from_qvbot_view = await self.qvbot_reddit.submission(item.id, fetch=False)
                sticky = await item_from_qvbot_view.reply(removal_comment)
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

    async def fetch_config_from_wiki(self):
        wiki_page = await self.superstonk_subreddit.wiki.get_page("qualityvote")
        wiki_config_text = wiki_page.content_md
        wiki_config = yaml.safe_load(wiki_config_text)
        self.post_limit_reached_comment = wiki_config['post_limit_reached_comment']

