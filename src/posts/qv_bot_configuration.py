import logging
from datetime import datetime

import yaml


class QualityVoteBotConfiguration:
    default_config = {
        'report_reason': 'Score of stickied comment has dropped below threshold',
    }

    def __init__(self, superstonk_subreddit, **kwargs):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self.superstonk_subreddit = superstonk_subreddit
        self.config = None

    def wot_doing(self):
        return "Reload QV-Bot's configuration every few minutes"

    async def on_ready(self, scheduler, **kwargs):
        self._logger.info(self.wot_doing())
        scheduler.add_job(self.fetch_config_from_wiki, "cron", minute="3-59/10")
        # Instead of using next_run_time=datetime.now() in the scheduler, delay the startup
        # until the qv config has been read, so that qvbot has the comment templates
        # already available when the first items come streaming in
        await self.fetch_config_from_wiki()

    async def fetch_config_from_wiki(self):
        wiki_page = await self.superstonk_subreddit.wiki.get_page("qualityvote")
        wiki_config_text = wiki_page.content_md
        wiki_config = yaml.safe_load(wiki_config_text)
        updated_config: dict = self.default_config.copy()
        updated_config.update(wiki_config)

        self.config = updated_config
        self._logger.info(f"reloaded config")
        self._logger.debug(self.config)

