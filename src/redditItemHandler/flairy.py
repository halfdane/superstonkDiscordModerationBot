import re

import disnake

from discordReaction.abstract_reaction import Reaction
from helper.discord_text_formatter import link
from redditItemHandler import Handler
from disnake.utils import escape_markdown


class Flairy(Handler, Reaction):
    emoji = '🧚'

    _flairy_detect_user_flair_change = \
        re.compile(r".*!\s*FL?AIRY\s*!\s*(.*?)(?:\s+(red|blue|pink|yellow|green|black))?\s*$",
                   re.IGNORECASE | re.MULTILINE | re.DOTALL)

    _templates = {"red": "0446bc04-91c0-11ec-8118-ce042afdde96",
                  "blue": "6e40ab4c-f3cd-11eb-889e-ae4cdf00ff3b",
                  "pink": "6de5f58e-f3ce-11eb-af43-eae78a59944d",
                  "yellow": "5f91a294-f3ce-11eb-948b-d26e0741292d",
                  "green": "7dfd44fe-f3ce-11eb-a228-aaac7809dc68",
                  "black": "8abdf72e-f3ce-11eb-b3e3-22147bc43b70"}

    _default_color = "black"

    def __init__(self, bot):
        Handler.__init__(self, bot)
        Reaction.__init__(self, bot)

    async def take(self, comment):
        if self._flairy_detect_user_flair_change.match(comment.body) \
                and comment.author not in self.bot.moderators \
                and comment.author.name not in ["Roid_Rage_Smurf"] \
                and await self.is_new_item(self.bot.flairy_channel, comment):
            self._logger.info(f"Sending flair request {comment}")
            url = f"https://www.reddit.com{comment.permalink}"
            e = disnake.Embed(
                url=url,
                colour=disnake.Colour(0).from_rgb(207, 206, 255))
            e.description = f"[Flair Request: {escape_markdown(comment.body)}]({url})"
            e.add_field("Redditor", link(f"https://www.reddit.com/u/{comment.author}", comment.author), inline=False)
            msg = await self.bot.flairy_channel.send(embed=e)
            await msg.add_reaction(self.emoji)
            await self.bot.add_reactions(msg)

    async def handle_reaction(self, message, emoji, user, channel):
        comment = await self.bot.get_item(message)
        body = getattr(comment, 'body', "")
        subreddit = self.bot.subreddit
        flairy_reddit = self.bot.flairy_reddit
        mods = self.bot.moderators

        user_to_be_flaired = comment.author
        flairy_user = await flairy_reddit.user.me()
        if (flairy := self._flairy_detect_user_flair_change.match(body)) \
                     and user_to_be_flaired not in mods \
                     and user_to_be_flaired != flairy_user:
            await self.flair_user(subreddit, comment, flairy_reddit, user_to_be_flaired, flairy.group(1),
                                  flairy.group(2))
            await self.bot.handle_reaction(message, "✅", user, channel)

    async def flair_user(self, subreddit, comment, flairy_reddit, user_to_be_flaired, flair_match, color_match):
        flair_text = flair_match.strip()
        color = (color_match or self._default_color).lower().strip()
        if color not in self._templates.keys():
            message = f"Cowardly refusing to use [{color}] as a color!"
            log_message = f"Wrong color [{color}]: not changing {user_to_be_flaired}'s flair"
        elif len(flair_text) > 63:
            message = f"(ノಠ益ಠ)ノ彡┻━┻ THE FLAIR TEXT IS TOO LONG!"
            log_message = f"Too long: Not changing {user_to_be_flaired}'s flair to [{flair_text}]"
        else:
            template = self._templates[color]
            previous_flair = getattr(comment, 'author_flair_text', "")
            log_message = f"[{previous_flair}] => [{flair_text}] with template {template} for the color {color}"
            await subreddit.flair.set(redditor=user_to_be_flaired, text=flair_text, flair_template_id=template)
            message = rf"(✿\^‿\^)━☆ﾟ.*･｡ﾟ `{flair_text}`"
        self._logger.info(log_message)
        comment_from_flairies_view = await flairy_reddit.comment(comment.id, fetch=False)
        await comment_from_flairies_view.upvote()
        await comment_from_flairies_view.reply(message)

    def description(self):
        return "Accept the flair request. The flairy will take care of the rest."
