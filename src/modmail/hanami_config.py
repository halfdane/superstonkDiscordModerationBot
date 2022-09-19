
import logging
import re
from datetime import datetime

import yaml


class HanamiConfiguration:
    def __init__(self, superstonk_subreddit, **kwargs):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self.superstonk_subreddit = superstonk_subreddit
        self.config = None
        self.greeting = None
        self.bye = None

    def wot_doing(self):
        return "[internal] Reload Hanami's configuration every 10 minutes"

    async def on_ready(self, scheduler, **kwargs):
        scheduler.add_job(self.fetch_config_from_wiki, "cron", minute="3-59/10")
        # Instead of using next_run_time=datetime.now() in the scheduler, delay the startup
        # until the qv config has been read, so that qvbot has the comment templates
        # already available when the first items come streaming in
        await self.fetch_config_from_wiki()

    async def fetch_config_from_wiki(self):
        wiki_page = await self.superstonk_subreddit.wiki.get_page("hanami_config")
        wiki_config_text = wiki_page.content_md
        self.config = yaml.safe_load(wiki_config_text)
        self._logger.info(f"reloaded config with {len(self.config)} entries")
