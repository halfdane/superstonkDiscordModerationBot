from datetime import datetime, timedelta

import disnake
from disnake import Embed

import yaml
import chevron

from helper.links import permalink
from reddit_item_handler import Handler

REMOVAL_COMMENT = """
    Your post was removed by a moderator because this URL has already been posted in the last 24 hours.
    
    {{previously_posted}}
    
    🦍🦍🦍🦍🦍🦍
    
    If you feel this removal was unwarranted, please contact us via Mod Mail: https://www.reddit.com/message/compose?to=/r/Superstonk
    
    Thanks for being a member of r/Superstonk 💎🙌🚀
"""


async def _post_to_string(post):
    created_utc = datetime.utcfromtimestamp(post.created_utc).strftime("%m/%d/%Y, %H:%M:%S")
    return f"- **{created_utc}**: https://www.reddit.com/r/Superstonk/comments/{post.id}"


class PostUrlLimiter(Handler):
    _interval = timedelta(hours=24)

    def __init__(self, add_reactions_to_discord_message, post_repo, url_post_repo, qvbot_reddit,
                 report_channel, is_live_environment,
                 superstonk_subreddit, **kwargs):
        super().__init__()
        self.post_repo = post_repo
        self.url_post_repo = url_post_repo
        self.qvbot_reddit = qvbot_reddit
        self.report_channel = report_channel
        self.add_reactions_to_discord_message = add_reactions_to_discord_message
        self.is_live_environment = is_live_environment
        self.superstonk_subreddit = superstonk_subreddit
        self.post_limit_reached_comment = REMOVAL_COMMENT
        self.active = False

    async def on_ready(self, scheduler, **kwargs):
        self._logger.info("Ready to restrict URL posts")
        scheduler.add_job(self.fetch_config_from_wiki, "cron", minute="6-59/10", next_run_time=datetime.now())
        scheduler.add_job(self.cleanup_database, "cron", hour="*", next_run_time=datetime.now())

    async def take(self, item):
        url = getattr(item, 'url', None)
        posts_with_same_url = await self.url_post_repo.fetch(url=url)

        limit = 1
        if "twitter.com/ryancohen" in url:
            limit = 3

        if len(posts_with_same_url) > limit:
            sorted_posts = sorted(posts_with_same_url, key=lambda v: v.created_utc)
            model = {
                'previously_posted': "    \n".join([await _post_to_string(post) for post in sorted_posts]),
            }
            removal_comment = chevron.render(self.post_limit_reached_comment, model)

            self._logger.info(f"The URL is posted a lot: {removal_comment}")

            if self.is_live_environment:
                item_from_qvbot_view = await self.qvbot_reddit.submission(item.id, fetch=False)
                sticky = await item_from_qvbot_view.reply(removal_comment)
                await sticky.mod.distinguish(how="yes", sticky=True)
                await sticky.mod.ignore_reports()
                await item_from_qvbot_view.mod.remove(spam=False, mod_note="url count limit reached")
            await self.report_infraction(url, item)

        else:
            self.url_post_repo.store(item)

    async def report_infraction(self, url, item):
        author = getattr(item.author, 'name', str(item.author))
        embed = Embed(colour=disnake.Colour(0).from_rgb(207, 206, 255))
        embed.description = f"**Prevented {url} from being posted again {permalink(item)}**  \n"
        embed.add_field("Redditor", f"[{author}](https://www.reddit.com/u/{author})", inline=False)

        msg = await self.report_channel.send(embed=embed)
        await self.add_reactions_to_discord_message(msg)

    async def fetch_config_from_wiki(self):
        wiki_page = await self.superstonk_subreddit.wiki.get_page("qualityvote")
        wiki_config_text = wiki_page.content_md
        wiki_config = yaml.safe_load(wiki_config_text)
        self.post_limit_reached_comment = wiki_config['url_limit_reached_comment']
        self.active = wiki_config['url_restriction_active'] == "true"

    async def cleanup_database(self):
        yesterday = datetime.utcnow() - timedelta(hours=24)
        posts = await self.post_repo.fetch(since=yesterday)
        ids = [post.id for post in posts]
        await self.url_post_repo.remove(ids)
