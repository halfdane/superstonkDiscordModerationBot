import re

import disnake

from discordReaction.abstract_reaction import Reaction
from helper.discord_text_formatter import link
from redditItemHandler import Handler
from disnake.utils import escape_markdown


class Flairy(Handler, Reaction):
    emoji = '🧚'

    _flairy_command = ".*!\s*FL?AIRY\s*!"
    _flairy_text = "\s*(.*?)"
    _valid_colors = "(?:\s+(red|blue|pink|yellow|green|black))?\s*"
    _last_word = "(\w*)"

    _flairy_detect_user_flair_change = \
        re.compile(rf"{_flairy_command}{_flairy_text}{_valid_colors}$", re.IGNORECASE | re.MULTILINE | re.DOTALL)

    _flairy_detect_last_word = \
        re.compile(rf"{_flairy_command}{_flairy_text}{_last_word}$", re.IGNORECASE | re.MULTILINE | re.DOTALL)

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
        body = getattr(comment, 'body', "")
        if (flairy := self._flairy_detect_user_flair_change.match(body)) \
                and comment.author not in self.bot.moderators \
                and comment.author.name not in ["Roid_Rage_Smurf"]:

            flair_text = flairy.group(1)
            if len(flair_text) > 63:
                comment_from_flairies_view = await self.bot.flairy_reddit.comment(comment.id, fetch=False)
                message = "(ノಠ益ಠ)ノ彡┻━┻ THE FLAIR TEXT IS TOO LONG!   \nPlease use less than 64 unicode characters"
                self._logger.info(f"Too long: https://www.reddit.com{comment.permalink}")
                await comment_from_flairies_view.reply(message)
                return

            if self.bot.is_forbidden_comment_message(flair_text):
                self._logger.info(f"Silently refusing to grant flair with restricted content: {flair_text}")
                return

            last_word = self._flairy_detect_last_word.match(body).group(2)
            if last_word.lower() in ["orange", "grey", "gray", "purple", "white"]:
                comment_from_flairies_view = await self.bot.flairy_reddit.comment(comment.id, fetch=False)
                message = f"(ノಠ益ಠ)ノ彡┻━┻ {last_word.upper()} IS NOT A VALID COLOR!   \n" \
                          f"Valid colors are `red`, `blue`, `pink`, `yellow`, `green` or `black`.   \n" \
                          f"I'm making the change, so if that's not what you want " \
                          f"you have to summon me again."
                self._logger.info(f"Wrong color: https://www.reddit.com{comment.permalink}")
                await comment_from_flairies_view.reply(message)

            self._logger.info(f"Sending flair request {comment} {flair_text}")
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
        if channel != self.bot.flairy_channel:
            return
        comment = await self.bot.get_item(message)
        body = getattr(comment, 'body', "")
        flairy = self._flairy_detect_user_flair_change.match(body)
        if flairy is not None:
            await self.flair_user(comment, flairy.group(1), flairy.group(2))
            await self.bot.handle_reaction(message, "✅", user, channel)
        else:
            await self.bot.handle_reaction(message, "✅", user, channel)
            await message.edit(content="Flair request was removed in the meantime")

    async def flair_user(self, comment, flair_match, color_match):
        flair_text = flair_match.strip()
        color = (color_match or self._default_color).lower().strip()
        template = self._templates[color]
        previous_flair = getattr(comment, 'author_flair_text', "")
        log_message = f"[{previous_flair}] => [{flair_text}] with template {template} for the color {color}"
        subreddit_from_flairies_view = await self.bot.flairy_reddit.subreddit("Superstonk")
        await subreddit_from_flairies_view.flair.set(
            redditor=comment.author,
            text=flair_text,
            flair_template_id=template)
        message = rf"(✿\^‿\^)━☆ﾟ.*･｡ﾟ `{flair_text}`"
        self._logger.info(log_message)
        comment_from_flairies_view = await self.bot.flairy_reddit.comment(comment.id, fetch=False)
        await comment_from_flairies_view.upvote()
        await comment_from_flairies_view.reply(message)

    def description(self):
        return "Accept the flair request. The flairy will take care of the rest."
