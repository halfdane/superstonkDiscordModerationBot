import logging
from datetime import datetime, timedelta

import chevron

from helper.item_helper import permalink
from reddit_item_handler import Handler


class QualityVoteBot(Handler):
    def __init__(self, qvbot_reddit, is_live_environment, comment_repo, quality_vote_bot_configuration, **kwargs):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self.qvbot_reddit = qvbot_reddit
        self.is_live_environment = is_live_environment
        self.comment_repo = comment_repo
        self.quality_vote_bot_configuration = quality_vote_bot_configuration

    def wot_doing(self):
        return "Add QV comments to every post and report when they are downvoted"

    async def on_ready(self, scheduler, **kwargs):
        scheduler.add_job(self.check_recent_comments, "cron", minute="4-59/15",
                          next_run_time=datetime.now() + timedelta(minutes=1))

    async def take(self, submission):
        config = self.quality_vote_bot_configuration.config
        if not self.__has_stickied_comment(submission) \
                and getattr(submission, 'link_flair_template_id', None) not in config['ignore_flairs']:

            default_comment = config['vote_comment']
            flair_specific_comment_key = 'vote_comment_' + getattr(submission, 'link_flair_template_id', '')
            vote_comment = config.get(flair_specific_comment_key, default_comment)

            qv_user = await self.qvbot_reddit.user.me()
            post_from_qbots_view = await self.qvbot_reddit.submission(submission.id, fetch=False)
            self._logger.debug(f"adding {qv_user} comment to https://www.reddit.com{submission.permalink}")

            if self.is_live_environment:
                sticky = await post_from_qbots_view.reply(vote_comment)
                await sticky.mod.distinguish(how="yes", sticky=True)
                await sticky.mod.ignore_reports()

                return True
        else:
            self._logger.info(f"NO QV: https://www.reddit.com{submission.permalink}")

    async def check_recent_comments(self, ):
        self._logger.info("checking comments")
        now = datetime.utcnow()
        yesterday = now - timedelta(hours=24)

        qv_user = await self.qvbot_reddit.user.me()
        comments = await self.comment_repo.fetch(since=yesterday, author=qv_user.name)
        c_fids = [f"t1_{c.id}" for c in comments]

        fetched_comments = await self.qvbot_reddit.info(c_fids)
        parent_fids = [comment.parent_id for comment in fetched_comments]
        fetched_parents = {parent.fullname: parent async for parent in self.qvbot_reddit.info(parent_fids)}

        async for comment in self.qvbot_reddit.info(c_fids):
            comment_parent = fetched_parents.get(comment.parent_id)
            if (await self.post_is_available(comment_parent)) and \
                    comment.score <= self.quality_vote_bot_configuration.config['report_threshold']:
                model: dict = self.quality_vote_bot_configuration.config.copy()
                model.update(comment_parent.__dict__)
                self._logger.debug(f"{comment.score} {permalink(comment_parent)}")
                await comment_parent.report(
                    chevron.render(self.quality_vote_bot_configuration.config['report_reason'], model))

        self._logger.info(f"looked at {len(c_fids)} comments between {yesterday} and {now}")

    def __has_stickied_comment(self, submission):
        return len(submission.comments) > 0 and submission.comments[0].stickied

    async def post_is_available(self, post):
        return getattr(post, 'removed_by_category', None) is None
