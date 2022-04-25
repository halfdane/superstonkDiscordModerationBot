import datetime
import re

from disnake import Embed

from helper.mod_notes import fetch_modnotes
from redditItemHandler import Handler

RULE_1 = re.compile(r"rule\s*1", re.IGNORECASE)


class ImportantReports(Handler):

    async def take(self, item):
        user_report_count = sum([r[1] for r in item.user_reports])
        mod_report_count = len([r[1] for r in item.mod_reports if r[1] != "AutoModerator"])
        mods_reporting_rule_1 = [r[1] for r in item.mod_reports if RULE_1.match(r[0])]
        if len(mods_reporting_rule_1) > 0:
            await self.__send_ban_list(mods_reporting_rule_1, item)
        elif user_report_count >= 5 or mod_report_count > 0:
            self._logger.info(f"Sending reported item {item}")
            embed = Embed.from_dict(self.__create_embed(item))
            msg = await self.bot.report_channel.send(embed=embed)
            await self.bot.add_reactions(msg)

    def __create_embed(self, item):
        url = f"https://www.reddit.com{item.permalink}"
        title = getattr(item, 'title', getattr(item, 'body', ""))[:75]
        comments = getattr(item, 'comments', None)

        fields = []
        self.__field(fields, "Redditor", f"[{item.author}](https://www.reddit.com/u/{item.author})", False)
        self.__field(fields, "User Reports", "\n".join(f"{r[1]} {r[0]}" for r in item.user_reports), False)
        self.__field(fields, "Mod Reports", "\n".join(f"{r[1]} {r[0]}" for r in item.mod_reports), False)
        self.__field(fields, "Score", str(getattr(item, 'score', 0)), True)
        self.__field(fields, "QV Score",
                     str(comments[0].score) if comments and comments[0].author.name == "Superstonk_QV" else None, True)
        self.__field(fields, "Upvote Ratio", str(getattr(item, 'upvote_ratio', 0)), True)
        return {
            'url': url,
            'color': (207 << 16) + (206 << 8) + 255,
            'title': getattr(item, 'title', getattr(item, 'body', ""))[:75],
            'description': f"[Reported {item.__class__.__name__}: {title}]({url})",
            'fields': fields
        }

    def __field(self, field_list, name, value, inline):
        if value:
            field_list.append({"name": name, "value": value, "inline": inline})

    async def __send_ban_list(self, mods_reporting_rule_1, item):
        modnotes = fetch_modnotes(reddit=self.bot.reddit, redditor_param=item.author, only='banuser')
        bans = f"All bans of {item.author}   "
        async for k, v in modnotes:
            bans += f"- **{k}**: {v}   \n"
        bans += "\n\nThat's all"
        utc_datetime = datetime.datetime.utcnow()
        formatted_string = utc_datetime.strftime("%Y-%m-%d-%H%MZ")
        for reporting_mod in mods_reporting_rule_1:
            mod = await self.bot.reddit.redditor(reporting_mod)

            await mod.message(f"Bans of {item.author} at {formatted_string}", bans)
