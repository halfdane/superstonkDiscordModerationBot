import logging
from datetime import datetime, timedelta

from redditItemHandler import Handler
import chevron
import yaml


class QualityVoteBot(Handler):
    default_config = {
        'report_reason': 'Score of stickied comment has dropped below threshold',
    }

    def __init__(self, qvbot_reddit, superstonk_subreddit, is_live_environment, comment_repo, **kwargs):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self.qvbot_reddit = qvbot_reddit
        self.is_live_environment = is_live_environment
        self.superstonk_subreddit = superstonk_subreddit
        self.comment_repo = comment_repo
        self.config = None

    async def on_ready(self, scheduler, **kwargs):
        self._logger.info(f"Ready to add QV comments to every post")
        scheduler.add_job(self.fetch_config_from_wiki, "cron", minute="3-59/10", next_run_time=datetime.now())
        scheduler.add_job(self.check_recent_comments, "cron", minute="4-59/10",
                          next_run_time=datetime.now()+timedelta(minutes=1))

    async def take(self, submission):
        if not self.__has_stickied_comment(submission) \
                and submission.link_flair_template_id not in self.config['ignore_flairs']:
            self._logger.info(f"https://www.reddit.com{submission.permalink}")

            if self.is_live_environment:
                post_from_qbots_view = await self.qvbot_reddit.comment(submission.id, fetch=False)

                sticky = await post_from_qbots_view.reply(self.config['vote_comment'])
                await sticky.mod.distinguish(how="yes", sticky=True)
                await sticky.mod.ignore_reports()
        else:
            self._logger.info(f"NO QV: https://www.reddit.com{submission.permalink}")

    async def check_recent_comments(self, ):
        self._logger.info("checking comments")
        now = datetime.utcnow()
        yesterday = now - timedelta(hours=24)

        qv_user = await self.qvbot_reddit.user.me()
        comments = await self.comment_repo.fetch(since=yesterday, author=qv_user.name)
        c_fids = [f"t1_{c.id}" for c in comments]

        async for comment in self.qvbot_reddit.info(c_fids):
            comment_parent = await comment.parent()
            if (await self.post_is_available(comment_parent)) and comment.score <= self.config['report_threshold']:
                model: dict = self.config.copy()
                model.update(comment_parent.__dict__)
                self._logger.debug(f"{comment.score} https://www.reddit.com{comment_parent.permalink}")
                await comment_parent.report(chevron.render(self.config['report_reason'], model))

        self._logger.info(f"looked at {len(c_fids)} comments between {yesterday} and {now}")

    async def fetch_config_from_wiki(self):
        wiki_page = await self.superstonk_subreddit.wiki.get_page("qualityvote")
        wiki_config_text = wiki_page.content_md
        wiki_config = yaml.safe_load(wiki_config_text)
        updated_config: dict = self.default_config.copy()
        updated_config.update(wiki_config)
        updated_config['vote_comment'] = chevron.render(updated_config['vote_comment'], self.__dict__)
        self.config = updated_config
        self._logger.info(f"reloaded config")
        self._logger.debug(self.config)

    def __has_stickied_comment(self, submission):
        return len(submission.comments) > 0 and submission.comments[0].stickied

    async def post_is_available(self, post):
        await post.load()
        return getattr(post, 'removed_by_category', None) is None
