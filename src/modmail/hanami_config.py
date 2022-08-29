
import logging
import re
from datetime import datetime

import yaml


class HanamiConfiguration:
    def __init__(self, superstonk_subreddit, **kwargs):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self.superstonk_subreddit = superstonk_subreddit
        self.hanami_configs = re.compile(r'hanami_config/(.+)')
        self.config = None
        self.ready = False

    def wot_doing(self):
        return "Reload Hanami's configuration every 10 minutes"

    async def on_ready(self, scheduler, **kwargs):
        self._logger.warning(self.wot_doing())
        scheduler.add_job(self.fetch_config_from_wiki, "cron", minute="3-59/10", next_run_time=datetime.now())

    async def fetch_config_from_wiki(self):
        config = dict()
        config['types'] = dict()

        print(f"iterating {self.superstonk_subreddit.wiki}")
        async for wikipage in self.superstonk_subreddit.wiki:
            print(f"handling {wikipage}")
            await wikipage.load()
            if hanami_config := self.hanami_configs.match(wikipage.name):
                self._logger.info(f"Reading {self.superstonk_subreddit} {wikipage.name}")
                wiki_config = yaml.safe_load(wikipage.content_md)
                config['types'][hanami_config.group(1)] = wiki_config
            else:
                self._logger.info(f"Ignoring {self.superstonk_subreddit} {wikipage.name}")

        self.config = config

