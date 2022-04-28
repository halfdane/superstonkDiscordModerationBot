import logging
import re

import asyncpraw.models
import disnake

from discordReaction.abstract_reaction import Reaction
from redditItemHandler import Handler
from disnake.utils import escape_markdown

import random


class Flairy(Handler, Reaction):
    emoji = '🧚'

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

        self.flairy_command_detection = r".*!\s*FL?AIRY"
        self.flair_command = rf"{self.flairy_command_detection}\s*!"

        self._flairy_text = r"\s*(.*?)"
        self._valid_colors = fr"(?:\s+({'|'.join(self._templates.keys())}))?\s*"

        self.flags = re.IGNORECASE | re.MULTILINE | re.DOTALL

        self.detect_flairy_command = \
            re.compile(rf"{self.flairy_command_detection}", self.flags)

        self._flairy_detect_user_flair_change = \
            re.compile(rf"{self.flair_command}{self._flairy_text}{self._valid_colors}$", self.flags)

        self._commands = [
            ClearCommand(self),
            SealmeCommand(self, self._templates[self._default_color]),
            RandomFlairCommand(self),
            WrongColorCommand(self)
        ]

    async def take(self, comment):
        body = getattr(comment, 'body', "")
        if (self.detect_flairy_command.match(body)) \
                and comment.author not in self.bot.moderators \
                and comment.author.name not in ["Roid_Rage_Smurf"]:

            if await self._was_recently_posted(comment, self.bot.flairy_channel):
                self._logger.info(f"skipping over recently handled flair request {self.permalink(comment)}")
                return

            for command in self._commands:
                if await command.handled(body, comment):
                    return

            flairy = self._flairy_detect_user_flair_change.match(body)
            flair_text = flairy.group(1)
            if len(flair_text) > 63:
                comment_from_flairies_view = await self.bot.flairy_reddit.comment(comment.id, fetch=False)
                message = "(ノಠ益ಠ)ノ彡┻━┻ THE FLAIR TEXT IS TOO LONG!   \nPlease use less than 64 unicode characters"
                self._logger.info(f"Too long: {self.permalink(comment)}")
                await comment_from_flairies_view.reply(message)
                return

            if self.bot.is_forbidden_comment_message(flair_text):
                self._logger.info(f"Silently refusing to grant flair with restricted content: {flair_text}")
                return

            self._logger.info(f"Sending flair request {comment} {flair_text}")
            url = self.permalink(comment)
            e = disnake.Embed(
                url=url,
                colour=disnake.Colour(0).from_rgb(207, 206, 255))
            e.description = f"[Flair Request: {escape_markdown(comment.body)}]({url})"
            e.add_field("Redditor", f"[{comment.author}](https://www.reddit.com/u/{comment.author})", inline=False)
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
            await self.flair_user(comment=comment, flair_text=flairy.group(1), flair_color=flairy.group(2))
            await self.bot.handle_reaction(message, "✅", user, channel)
        else:
            await self.bot.handle_reaction(message, "✅", user, channel)
            await message.edit(content="Flair request was removed in the meantime")

    async def flair_user(self, comment, flair_text, flair_color=None, template=None, message=""):
        if (not flair_color or template) and (flair_color or not template):
            raise Exception("give either color or color_template")

        flair_text = flair_text.strip()
        color = (flair_color or self._default_color).lower().strip()
        template = (template or self._templates[color])
        previous_flair = getattr(comment, 'author_flair_text', "")
        log_message = f"[{previous_flair}] => [{flair_text}] with template {template} for the color {color}"
        subreddit_from_flairies_view = await self.bot.flairy_reddit.subreddit("Superstonk")
        await subreddit_from_flairies_view.flair.set(
            redditor=comment.author,
            text=flair_text,
            flair_template_id=template)
        message += rf'(✿\^‿\^)━☆ﾟ.*･｡ﾟ "{flair_text}"'
        self._logger.info(log_message)
        comment_from_flairies_view = await self.bot.flairy_reddit.comment(comment.id, fetch=False)
        await comment_from_flairies_view.upvote()
        await comment_from_flairies_view.reply(message)

    def description(self):
        return "Accept the flair request. The flairy will take care of the rest."


class RandomFlairCommand:

    def __init__(self, flairy):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._flairy = flairy
        self._random_flair_command = \
            re.compile(rf"{self._flairy.flairy_command_detection}\s*!$", self._flairy.flags)

    async def handled(self, body, comment):
        if self._random_flair_command.match(body):
            await self._bestow_random_flair(comment)
            return True

        return False

    async def _bestow_random_flair(self, comment):
        _emojis = ['🏴‍☠', '💪', '💎', '🎊', '🌕',
                   '🦍🚀', '🦍', '💎🙌🏻', '🎮🛑',
                   '♾️', '🐵', '💙', '🍦💩🪑'
                   ]

        _flairs = ["TOMORROW!", "Hola", "I'm here for the memes", "es mucho", "We're in the endgame now", "Gamecock",
                   "FUCK YOU PAY ME", "Locked and loaded ", "Power to the Players", "Nothin But Time",
                   "GME to the Moon! ",
                   "Infinite Risk ", "Hang in There! ", "Power to the Players ", "Power to the Creators ",
                   "Probably nothing", "Gimme me my money ", "GME ", "Apes together strong", "before the split",
                   "Gamestop 4U", "Casual lurker until MOASS", "GMERICA ", "GME ", "Superstonk Ape", "GME to the Moon!",
                   "Pepperidge Farm remembers", "LOVE GME ", "SuperApe ", "What’s an exit strategy", "C.R.E.A.M",
                   "ZEN APE ", "No Cell No Sell", "GameStop", "Power to the Players ", "Crayon Sniffer ",
                   "Mods are sus",
                   "DEEP FUCKING VALUE ", "Fuck no I’m not selling my GME!", "Fuck Citadel", "I just love the stock ",
                   "FUD is the Mind-Killer", "No target, just up!", "We are in a completely fraudulent system ",
                   "Get rich or die buyin’", "GME go Brrrr ", "Apes together strong ", "wen moon",
                   "I SAID WE GREEN TODAY",
                   "Buy now, ask questions later ", "I am not a cat", "I like the stock. ", "Just Like the Stonk",
                   "Bullish"]

        emojis = random.sample(_emojis, 2)
        flair_text = f"{emojis[0]} {random.sample(_flairs, 1)[0]} {emojis[1]}"
        color = random.sample(list(self._flairy._templates.keys()), 1)[0]
        message = "(ノಠ益ಠ)ノ彡┻━┻ YOU DIDN'T ASK FOR A FLAIR!\n\n " \
                  "Let me show you how to do it:  \n\n" \
                  f"     !FLAIRY!{flair_text}{color}\n\n...\n\n...\n\n"
        self._logger.info(f"Randomly assigning: {self._flairy.permalink(comment)}")

        await self._flairy.flair_user(
            comment=comment,
            flair_text=flair_text,
            flair_color=color,
            message=message)


class SealmeCommand:
    def __init__(self, flairy, default_template):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._flairy = flairy
        self._sealme_command = \
            re.compile(rf"{self._flairy.flairy_command_detection}:SEALME\s*!", self._flairy.flags)
        self._default_template = default_template

    async def handled(self, body, comment):
        if self._sealme_command.match(body):
            current_flair = getattr(comment, 'author_flair_text', "")
            current_template = getattr(comment, 'author_flair_template_id', self._default_template)
            message = 'Witness meee /u/Justind123  \n\n'
            await self._flairy.flair_user(
                comment=comment,
                flair_text=current_flair+'🦭',
                template=current_template,
                message=message)

            return True

        return False


class ClearCommand:
    def __init__(self, flairy):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._flairy = flairy

        self._reset_command = \
            re.compile(rf"{self._flairy.flairy_command_detection}:CLEARME\s*!", self._flairy.flags)

    async def handled(self, body, comment):
        if self._reset_command.match(body):
            message = 'Clearing the flair as requested  \n\n' + r'(✿\^‿\^)━☆ﾟ.*･｡ﾟ '
            self._logger.info(f"Clearing flair: {self._flairy.permalink(comment)}")

            subreddit_from_flairies_view = await self._flairy.bot.flairy_reddit.subreddit("Superstonk")
            await subreddit_from_flairies_view.flair.delete(redditor=comment.author)
            comment_from_flairies_view = await self._flairy.bot.flairy_reddit.comment(comment.id, fetch=False)
            await comment_from_flairies_view.reply(message)
            return True

        return False


class WrongColorCommand:
    def __init__(self, flairy):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._flairy = flairy

        self._last_word = r"(\w*)"

        self._detect_last_word = \
            re.compile(rf"{self._flairy.flair_command}.*?{self._last_word}$", self._flairy.flags)

    async def handled(self, body, comment):
        last_word = self._detect_last_word.match(body).group(1)
        if last_word.lower() in ["orange", "grey", "gray", "purple", "white"]:
            comment_from_flairies_view = await self._flairy.bot.flairy_reddit.comment(comment.id, fetch=False)
            message = f"(ノಠ益ಠ)ノ彡┻━┻ {last_word.upper()} IS NOT A VALID COLOR!   \n" \
                      f"Valid colors are {', '.join(self._flairy._templates.keys())}.   \n" \
                      f"I'm making the change, so if that's not what you want " \
                      f"you have to summon me again."
            self._logger.info(f"Wrong color: {self._flairy.permalink(comment)}")
            await comment_from_flairies_view.reply(message)

        return False
