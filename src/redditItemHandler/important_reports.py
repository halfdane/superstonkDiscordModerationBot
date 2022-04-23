import datetime
import datetime
import re

import disnake

from helper.discord_text_formatter import link
from helper.mod_notes import fetch_modnotes
from redditItemHandler import Handler

RULE_1 = re.compile(r"rule\s+1", re.IGNORECASE)


class ImportantReports(Handler):

    async def take(self, item):
        user_report_count = sum([r[1] for r in item.user_reports])
        mod_report_count = len([r[1] for r in item.mod_reports if r[1] != "AutoModerator"])
        mods_reporting_rule_1 = [r[1] for r in item.mod_reports if RULE_1.match(r[0])]
        if len(mods_reporting_rule_1) > 0:
            await self.__send_ban_list(mods_reporting_rule_1, item)
        elif user_report_count >= 5 or mod_report_count > 0:
            self._logger.info(f"Sending reported item {item}")
            embed = await self.__create_embed(item)
            if embed:
                msg = await self.bot.report_channel.send(embed=embed)
                await self.bot.add_reactions(msg)

    async def __create_embed(self, item):
        url = f"https://www.reddit.com{item.permalink}"
        e = disnake.Embed(
            url=url,
            colour=disnake.Colour(0).from_rgb(207, 206, 255))

        title = getattr(item, 'title', getattr(item, 'body', ""))[:75]
        e.description = f"[Reported {item.__class__.__name__}: {title}]({url})"
        e.add_field("Redditor", link(f"https://www.reddit.com/u/{item.author}", item.author), inline=False)

        user_reports = "\n".join(f"{r[1]} {r[0]}" for r in item.user_reports)
        if user_reports:
            e.add_field("User Reports", user_reports, inline=False)

        mod_reports = "\n".join(f"{r[1]} {r[0]}" for r in item.mod_reports)
        if mod_reports:
            e.add_field("Mod Reports", mod_reports, inline=False)
        return e

    async def __send_ban_list(self, mods_reporting_rule_1, item):
        modnotes = fetch_modnotes(reddit=self.bot.reddit, redditor_param=item.author, only='banuser')
        bans = f"All bans of {item.author}"
        async for k, v in modnotes:
            bans += f"- **{k}**: {v}\n"
        bans += "\n\nThat's all"
        utc_datetime = datetime.datetime.utcnow()
        formatted_string = utc_datetime.strftime("%Y-%m-%d-%H%MZ")
        for reporting_mod in mods_reporting_rule_1:
            mod = await self.bot.reddit.redditor(reporting_mod)

            await mod.message(f"Bans of {item.author} at {formatted_string}", bans)

