import logging
import re

import yaml


class AutomodConfiguration:

    def __init__(self, superstonk_subreddit, automod_rules=[], domain_filter=[], **kwargs):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self.superstonk_subreddit = superstonk_subreddit
        self.config = None
        self.automod_rules = automod_rules
        self.domain_filter = domain_filter

    def wot_doing(self):
        return "[internal] Read the Automod-Configuration every 10 minutes"

    async def on_ready(self, scheduler, **kwargs):
        scheduler.add_job(self.fetch_config_from_wiki, "cron", minute="3-59/10")
        # Instead of using next_run_time=datetime.now() in the scheduler, delay the startup
        # until the configuration has been read, so that the rules are
        # already available when the first items come streaming in
        await self.fetch_config_from_wiki()

    async def fetch_config_from_wiki(self):
        automod_config = await self.superstonk_subreddit.wiki.get_page("config/automoderator")
        for rule in automod_config.content_md.split("---"):
            y = yaml.safe_load(rule)
            if y and y.get('action', "") == 'remove':
                self.automod_rules += [re.compile(r) for k, v in y.items() if "regex" in k for r in v]
                self.domain_filter += [r for k, v in y.items() if "domain" in k and not "regex" in k for r in v]

        self._logger.warning(
            f"Read {len(self.automod_rules)} removal rules and {len(self.domain_filter)} domain filters from automod rules")

    def is_forbidden_user_message(self, comment_message):
        matches_regexes = any(rule.search(comment_message) for rule in self.automod_rules)
        matches_domain = any(rule in comment_message for rule in self.domain_filter)
        return matches_regexes or matches_domain
