from datetime import datetime, timedelta, UTC

import chevron

from helper.item_helper import permalink, author
from reddit_item_handler import Handler


async def _post_to_string(post):
    created_utc = datetime.fromtimestamp(post.created_utc, UTC).strftime("%m/%d/%Y, %H:%M:%S")
    return f"- **{created_utc}**: {permalink(post.id)}"


class PostCountLimiter(Handler):
    _interval = timedelta(hours=24)

    def __init__(self, post_repo, qvbot_reddit, is_live_environment, quality_vote_bot_configuration, **_):
        super().__init__()
        self.post_repo = post_repo
        self.qvbot_reddit = qvbot_reddit
        self.is_live_environment = is_live_environment
        self.quality_vote_bot_configuration = quality_vote_bot_configuration

    def wot_doing(self):
        limit = self.quality_vote_bot_configuration.config.get('post_limit_reached_threshold', 10)
        return f"Limit post count to {limit} per 24 hours"

    async def take(self, item):
        author_name = author(item)
        yesterday = datetime.now(UTC) - timedelta(hours=24)
        posts = await self.post_repo.fetch(author=author_name, since=yesterday)
        posts_that_count = list(filter(lambda p: p.count_to_limit, posts))
        posts_that_dont_count = list(filter(lambda p: not p.count_to_limit, posts))
        posts_that_dont_count.append(item)

        limit = self.quality_vote_bot_configuration.config.get('post_limit_reached_threshold', 10)
        if len(posts_that_count) >= limit:
            sorted_posts = sorted(posts_that_count, key=lambda v: v.created_utc)
            model = {
                'list_of_posts': "    \n".join([await _post_to_string(post) for post in sorted_posts]),
                'ignored_posts': "    \n".join([await _post_to_string(post) for post in posts_that_dont_count]),
                'post_limit_reached_threshold': limit
            }

            post_limit_reached_comment = self.quality_vote_bot_configuration.config.get('post_limit_reached_comment', None)
            removal_comment = chevron.render(post_limit_reached_comment, model)

            self._logger.info(f"Oops, looks like {author_name} is posting a lot: {removal_comment}")

            if self.is_live_environment:
                item_from_qvbot_view = await self.qvbot_reddit.submission(item.id, fetch=False)
                sticky = await item_from_qvbot_view.reply(removal_comment)
                await sticky.mod.distinguish(how="yes", sticky=True)
                await sticky.mod.ignore_reports()
                await item_from_qvbot_view.mod.remove(spam=False, mod_note="post count limit reached")

            await self.post_repo.do_not_count_to_limit(item)

            return True
