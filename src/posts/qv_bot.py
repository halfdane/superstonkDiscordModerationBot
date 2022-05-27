import logging
from datetime import datetime

from redditItemHandler import Handler
import chevron
import yaml


class QualityVoteBot(Handler):
    default_config = {
        'report_reason': 'Score of stickied comment has dropped below threshold',
    }

    def __init__(self, qvbot_reddit, superstonk_subreddit, environment):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self.qvbot_reddit = qvbot_reddit
        self.environment = environment
        self.superstonk_subreddit = superstonk_subreddit
        self.config = None

    async def on_ready(self, scheduler, **kwargs):
        self._logger.info(f"Ready to add QV comments to every post")
        scheduler.add_job(self.fetch_config_from_wiki, "cron", minute="3-59/10", next_run_time=datetime.now())
        scheduler.add_job(self.check_recent_comments, "cron", minute="4-59/10", next_run_time=datetime.now())

    async def take(self, submission):
        if not self.__has_stickied_comment(submission) \
                and submission.link_flair_template_id not in self.config['ignore_flairs']:
            self._logger.info(f"qv: https://www.reddit.com{submission.permalink}")

            if self.environment == 'live':
                sticky = await submission.reply(self.config['vote_comment'])
                await sticky.mod.distinguish(how="yes", sticky=True)
                await sticky.mod.ignore_reports()
        else:
            self._logger.info(f"NO QV: https://www.reddit.com{submission.permalink}")

    def check_recent_comments(self, ):
        self._logger.info("checking comments")
        count = 0
        first = None
        last = None
        for comment in self.qvbot_reddit.user.me().comments.new(limit=None):
            if first is None:
                first = comment.created_utc
            last = comment.created_utc
            count += 1
            if self.post_is_available(comment.parent()) and comment.score <= self.config['report_threshold']:
                model: dict = self.config.copy()
                model.update(comment.parent().__dict__)
                self._logger.debug(f"{comment.score} https://www.reddit.com{comment.parent().permalink}")
                comment.parent().report(chevron.render(self.config['report_reason'], model))

        self._logger.info(f"looked at {count} comments "
                          f"between {datetime.utcfromtimestamp(last).strftime('%Y-%m-%d %H:%M:%S')} "
                          f"and {datetime.utcfromtimestamp(first).strftime('%Y-%m-%d %H:%M:%S')}")

    def fetch_config_from_wiki(self):
        wiki_config_text = self.superstonk_subreddit.wiki['qualityvote'].content_md
        wiki_config = yaml.safe_load(wiki_config_text)
        updated_config: dict = self.default_config.copy()
        updated_config.update(wiki_config)
        updated_config['vote_comment'] = chevron.render(updated_config['vote_comment'], self.__dict__)
        self.config = updated_config
        self._logger.info(f"reloaded config")
        self._logger.debug(self.config)

    def __has_stickied_comment(self, submission):
        return len(submission.comments) > 0 and submission.comments[0].stickied

    def post_is_available(self, post):
        try:
            self._logger.debug(f"Forcing eager fetch of {post.title}")
        except:
            logging.info(f"ignoring problems with fetching info for {post.permalink}")
        return getattr(post, 'removed_by_category', None) is None
