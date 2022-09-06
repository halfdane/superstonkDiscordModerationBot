from datetime import datetime, time

import pytz

from reddit_item_handler import Handler


class WeekendRestrictor(Handler):
    # nyse timezone
    nytz = pytz.timezone('America/New_York')
    # The NYSE is open from Monday through Friday 9:30 a.m. to 4:00 p.m. Eastern time.
    # datetime(year, month, day[, hour[, minute[, second[, microsecond[,tzinfo]]]]])
    market_open_time = time(9, 30)
    market_close_time = time(16, 00)

    def __init__(self, post_repo=None, url_post_repo=None, qvbot_reddit=None,
                 is_live_environment=None, quality_vote_bot_configuration=None,
                 send_discord_message=None, **kwargs):
        super().__init__()
        self.post_repo = post_repo
        self.url_post_repo = url_post_repo
        self.qvbot_reddit = qvbot_reddit
        self.is_live_environment = is_live_environment
        self.quality_vote_bot_configuration = quality_vote_bot_configuration
        self.send_discord_message = send_discord_message

    def wot_doing(self):
        return "Remove posts with weekend-only flairs"

    async def take(self, item):
        config = self.quality_vote_bot_configuration.config
        if getattr(item, 'link_flair_template_id', None) in config['restrict_flair_to_weekend'] and \
            self.it_is_not_weekend():

            removal_comment = config['restrict_to_weekend_removal']
            flair_specific_removal_comment_key = 'restrict_to_weekend_removal_' + item.link_flair_template_id
            removal_comment = config.get(flair_specific_removal_comment_key, removal_comment)

            if self.is_live_environment:
                item_from_qvbot_view = await self.qvbot_reddit.submission(item.id, fetch=False)
                sticky = await item_from_qvbot_view.reply(removal_comment)
                await sticky.mod.distinguish(how="yes", sticky=True)
                await sticky.mod.ignore_reports()
                await item_from_qvbot_view.mod.remove(spam=False, mod_note="Flair is restricted to weekend")
            else:
                self._logger.info("Feature isn't active, so I'm not removing anything.")

            await self.send_discord_message(
                item=item,
                description_beginning=f"Prevented {item.link_flair_text} from posted on a outside the weekend  \n",
                fields={'auto_clean': False})
            return True

    def it_is_not_weekend(self):
        now = datetime.utcnow()
        weekday = now.weekday()

        # Monday is 0, Friday is 4 and Sunday is 6
        if weekday == 4:
            # Weekend starts after market close on friday
            return now.time() < self.market_close_time
        elif weekday in [5, 6]:
            # saturday and sunday are easy
            return False
        elif weekday == 0:
            # Weekend ends before market open on monday
            return now.time() > self.market_open_time

        return True
