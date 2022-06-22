from datetime import datetime, timedelta

import disnake
from disnake import Embed

import yaml
import chevron

from helper.links import permalink, user_page
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
    return f"- **{created_utc}**: {permalink(post.id)}"


class TweetPostLimiter(Handler):
    _interval = timedelta(hours=24)

    def __init__(self, add_reactions_to_discord_message, post_repo, url_post_repo, qvbot_reddit,
                 report_channel, is_live_environment, quality_vote_bot_configuration,
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
        self.quality_vote_bot_configuration = quality_vote_bot_configuration
        self.active = False

    def wot_doing(self):
        return "Restrict Ryan Cohen Tweets to 3"

    async def on_ready(self, scheduler, **kwargs):
        self._logger.info(self.wot_doing())

    async def take(self, item):
        url = getattr(item, 'url', None)

        if "twitter.com/ryancohen" not in url:
            return

        posts_with_same_url = await self.url_post_repo.fetch_like(url="https://twitter.com/ryancohen")

        count_of_posts = len(posts_with_same_url)
        self._logger.info(f"url {url} - amount of times it was posted: {count_of_posts}")
        if count_of_posts > 3:
            self._logger.info(f"post should be removed: {permalink(item)}")
            sorted_posts = sorted(posts_with_same_url, key=lambda v: v.created_utc)
            model = {
                'previously_posted': "    \n".join([await _post_to_string(post) for post in sorted_posts]),
            }
            removal_comment = chevron.render(self.quality_vote_bot_configuration.config['url_limit_reached_comment'], model)

            self._logger.info(f"The URL is posted a lot: {removal_comment}")

            if self.is_live_environment and \
                    (self.quality_vote_bot_configuration.config['url_restriction_active'] == "true"):
                item_from_qvbot_view = await self.qvbot_reddit.submission(item.id, fetch=False)
                sticky = await item_from_qvbot_view.reply(removal_comment)
                await sticky.mod.distinguish(how="yes", sticky=True)
                await sticky.mod.ignore_reports()
                await item_from_qvbot_view.mod.remove(spam=False, mod_note="Tweet count limit reached")
            else:
                self._logger.info("Feature isn't active, so I'm not removing anything.")
            await self.report_infraction(url, item)
            return True

    async def report_infraction(self, url, item):
        author = getattr(item.author, 'name', str(item.author))
        embed = Embed(colour=disnake.Colour(0).from_rgb(207, 206, 255))
        embed.description = f"**Prevented the Tweet {url} from being posted again {permalink(item)}**  \n"
        embed.add_field("Redditor", f"[{author}]({user_page(author)})", inline=False)

        msg = await self.report_channel.send(embed=embed)
        await self.add_reactions_to_discord_message(msg)
