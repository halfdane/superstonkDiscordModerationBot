from datetime import datetime, timedelta
from urllib.parse import urlparse

import chevron

from helper.links import permalink
from reddit_item_handler import Handler


async def _post_to_string(post):
    created_utc = datetime.utcfromtimestamp(post.created_utc).strftime("%m/%d/%Y, %H:%M:%S")
    return f"- **{created_utc}**: {permalink(post.id)}"


class UrlPostLimiter(Handler):
    _interval = timedelta(hours=24)

    def __init__(self, post_repo, url_post_repo, qvbot_reddit,
                 is_live_environment, quality_vote_bot_configuration,
                 send_discord_message, **kwargs):
        super().__init__()
        self.post_repo = post_repo
        self.url_post_repo = url_post_repo
        self.qvbot_reddit = qvbot_reddit
        self.is_live_environment = is_live_environment
        self.quality_vote_bot_configuration = quality_vote_bot_configuration
        self.send_discord_message = send_discord_message
        self.active = False

    def wot_doing(self):
        return "Restrict the posting of similar URLs to 2"

    async def on_ready(self, scheduler, **kwargs):
        self._logger.info(self.wot_doing())

    async def take(self, item):
        url = getattr(item, 'url', None)
        reduced = self.reduce_url(url)
        posts_with_same_url = await self.url_post_repo.fetch_like(url=reduced)

        limit = 2
        if "https://twitter.com/ryancohen" in url:
            limit = 3

        count_of_posts = len(posts_with_same_url)
        self._logger.info(f"url {url} - amount of times it was posted: {count_of_posts}")
        if count_of_posts > limit:
            self._logger.info(f"post should be removed: {permalink(item)}")
            sorted_posts = sorted(posts_with_same_url, key=lambda v: v.created_utc)
            model = {
                'previously_posted': "    \n".join([await _post_to_string(post) for post in sorted_posts]),
            }
            removal_comment_template = self.quality_vote_bot_configuration.config['url_limit_reached_comment']
            removal_comment = chevron.render(removal_comment_template, model)

            self._logger.info(f"The URL is posted a lot: {removal_comment}")

            if self.is_live_environment and self.active:
                item_from_qvbot_view = await self.qvbot_reddit.submission(item.id, fetch=False)
                sticky = await item_from_qvbot_view.reply(removal_comment)
                await sticky.mod.distinguish(how="yes", sticky=True)
                await sticky.mod.ignore_reports()
                await item_from_qvbot_view.mod.remove(spam=False, mod_note="url count limit reached")
            else:
                self._logger.info("Feature isn't active, so I'm not removing anything.")

            await self.send_discord_message(
                item=item,
                description_beginning=f"Prevented {url} from being posted again  \n")
            return True

        else:
            await self.url_post_repo.store(item)

    def reduce_url(self, url):
        if "https://twitter.com" in url:
            return self.twitter_url(url)

        return url

    def twitter_url(self, url):
        o = urlparse(url)
        return f"{o.scheme}://{o.netloc}{o.path}"
