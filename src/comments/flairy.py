import logging
import random
import re

import disnake
from disnake.utils import escape_markdown

from discordReaction.abstract_reaction import Reaction
from discordReaction.wip_reaction import WipReaction
from helper.links import permalink


class Flairy(Reaction):
    _templates = {"red": "0446bc04-91c0-11ec-8118-ce042afdde96",
                  "blue": "6e40ab4c-f3cd-11eb-889e-ae4cdf00ff3b",
                  "pink": "6de5f58e-f3ce-11eb-af43-eae78a59944d",
                  "yellow": "5f91a294-f3ce-11eb-948b-d26e0741292d",
                  "green": "7dfd44fe-f3ce-11eb-a228-aaac7809dc68",
                  "black": "8abdf72e-f3ce-11eb-b3e3-22147bc43b70"}

    _default_color = "black"

    def __init__(self, superstonk_moderators=[], flairy_channel=None, flairy_reddit=None,
                 is_forbidden_comment_message=None, add_reactions_to_discord_message=None,
                 is_live_environment=False, **kwargs):
        Reaction.__init__(self)

        self.superstonk_moderators = superstonk_moderators
        self.flairy_channel = flairy_channel
        self.flairy_reddit = flairy_reddit

        flairy_command_detection = r".*!\s*FL?AIRY"
        flair_command = rf"{flairy_command_detection}\s*!"

        flairy_text = r"\s*(.*?)"
        _valid_colors = fr"(?:\s*\b({'|'.join(self._templates.keys())}))?\s*"

        regex_flags = re.IGNORECASE | re.MULTILINE | re.DOTALL

        self.detect_flairy_command = \
            re.compile(rf"{flairy_command_detection}|u/superstonk-flairy", regex_flags)

        self.flairy_detect_user_flair_change = \
            re.compile(rf"{flair_command}{flairy_text}{_valid_colors}$", regex_flags)

        colors = list(self._templates.keys())
        self._commands = [
            CommentAlreadyHasAResponse(flairy_command_detection, regex_flags),
            FlairyExplainerCommand(flairy_reddit, self._templates.keys()),
            ClearCommand(flairy_reddit, flairy_command_detection, regex_flags),
            SealmeCommand(self._templates[self._default_color], flairy_command_detection, regex_flags,
                          self.flair_user),
            RandomFlairCommand(flairy_command_detection, regex_flags, self.flair_user, colors),
            WrongColorCommand(flairy_reddit, flair_command, regex_flags, colors),
            FlairTooLongCommand(self.flairy_detect_user_flair_change, flairy_reddit),
            FlairContainsForbiddenPhraseCommand(is_forbidden_comment_message, self.flairy_detect_user_flair_change),
            ApprovingFlairRequestCommand(self.flairy_detect_user_flair_change, flairy_channel,
                                         add_reactions_to_discord_message, self.flair_user)
        ]
        self.is_live_environment = is_live_environment

    async def on_ready(self):
        self._logger.info("Ready to handle flair requests")

    async def take(self, comment):
        body = getattr(comment, 'body', "")
        author = getattr(getattr(comment, "author", None), "name", None)
        if author == "Superstonk-Flairy":
            self._logger.debug(f"Not answering to myself: {permalink(comment)}")
            return

        if self.detect_flairy_command.search(body):
            is_mod = author in self.superstonk_moderators + ["Roid_Rage_Smurf"]

            self._logger.debug(
                f"seems to be a flairy command from {author}. Treat like mod? {is_mod} {permalink(comment)}")

            for command in self._commands:
                if await command.handled(body, comment, is_mod):
                    return

    async def flair_user(self, comment, flair_text, flair_color=None, template=None, message=""):
        flair_text = flair_text.strip()
        color = (flair_color or self._default_color).lower().strip()
        template = (template or self._templates[color])
        previous_flair = getattr(comment, 'author_flair_text', "")
        log_message = f"[{previous_flair}] => [{flair_text}] with template {template} for the color {color}"
        subreddit_from_flairies_view = await self.flairy_reddit.subreddit("Superstonk")

        if self.is_live_environment:
            await subreddit_from_flairies_view.flair.set(
                redditor=comment.author,
                text=flair_text,
                flair_template_id=template)
            message += rf'(✿\^‿\^)━☆ﾟ.*･｡ﾟ {flair_text}'
            self._logger.info(log_message)
            comment_from_flairies_view = await self.flairy_reddit.comment(comment.id, fetch=False)
            await comment_from_flairies_view.upvote()
            await comment_from_flairies_view.reply(message)

    @staticmethod
    def description():
        return "Accept the flair request. The flairy will take care of the rest."


class CommentAlreadyHasAResponse:
    def __init__(self, flairy_command_detection, flags):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._random_flair_command = \
            re.compile(rf"{flairy_command_detection}\s*!$", flags)

    async def handled(self, body, comment, is_mod):
        await comment.refresh()
        for response in comment.replies:
            author_name__lower = getattr(getattr(response, "author", None), "name", "").lower()
            if author_name__lower == "superstonk-flairy":
                self._logger.info(f"Flairy already responded: {permalink(response)}")
                return True
        return False


class RandomFlairCommand:

    def __init__(self, flairy_command_detection, flags, flair_user_function, colors):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._random_flair_command = \
            re.compile(rf"{flairy_command_detection}\s*!$", flags)
        self.flair_user_function = flair_user_function
        self.colors = colors

    async def handled(self, body, comment, is_mod):
        if is_mod:
            return False

        if self._random_flair_command.match(body):
            await self._bestow_random_flair(comment)
            return True

        return False

    async def _bestow_random_flair(self, comment):
        _emojis = ['🏴‍☠️', '💪', '💎', '🎊', '🌕',
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
        color = random.sample(self.colors, 1)[0]
        message = f"""(✿☉｡☉) You didn't ask for a flair?! Lemme get one for you...   \n"""
        self._logger.info(f"Randomly assigning: {permalink(comment)}")

        await self.flair_user_function(
            comment=comment,
            flair_text=flair_text,
            flair_color=color,
            message=message)


class SealmeCommand:
    def __init__(self, default_template, flairy_command_detection, flags, flair_user_function):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._sealme_command = \
            re.compile(rf"{flairy_command_detection}:SEALME\s*!", flags)
        self._default_template = default_template
        self.flair_user_function = flair_user_function

    async def handled(self, body, comment, is_mod):
        if is_mod:
            return False

        if self._sealme_command.match(body):
            current_flair = getattr(comment, 'author_flair_text', "")
            current_template = getattr(comment, 'author_flair_template_id', self._default_template)
            message = 'Witness meee /u/Justind123  \n\n'
            await self.flair_user_function(
                comment=comment,
                flair_text=current_flair + '🦭',
                template=current_template,
                message=message)
            self._logger.info(f"SEALING: {permalink(comment)}")
            return True

        return False


class ClearCommand:
    def __init__(self, flairy_reddit, flairy_command_detection, flags):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.flairy_reddit = flairy_reddit

        self._reset_command = \
            re.compile(rf"{flairy_command_detection}\s*:\s*CLEARME\s*!", flags)

    async def handled(self, body, comment, is_mod):
        if is_mod:
            return False

        if self._reset_command.match(body):
            message = 'Clearing the flair as requested  \n\n' + r'(✿\^‿\^)━☆ﾟ.*･｡ﾟ '
            self._logger.info(f"Clearing flair: {permalink(comment)}")

            subreddit_from_flairies_view = await self.flairy_reddit.subreddit("Superstonk")
            await subreddit_from_flairies_view.flair.delete(redditor=comment.author)
            comment_from_flairies_view = await self.flairy_reddit.comment(comment.id, fetch=False)
            await comment_from_flairies_view.reply(message)
            return True

        return False


class WrongColorCommand:
    def __init__(self, flairy_reddit, flair_command, flags, colors):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._last_word = r"(\w*)"
        self._detect_last_word = re.compile(rf"{flair_command}.*?{self._last_word}$", flags)
        self.colors = colors
        self.flairy_reddit = flairy_reddit

    async def handled(self, body, comment, is_mod):
        if is_mod:
            return False

        if match := self._detect_last_word.match(body):
            last_word = match.group(1)
            if last_word.lower() in ["orange", "grey", "gray", "purple", "white"]:
                comment_from_flairies_view = await self.flairy_reddit.comment(comment.id, fetch=False)
                message = f"(ノಠ益ಠ)ノ彡┻━┻ {last_word.upper()} IS NOT A VALID COLOR!   \n" \
                          f"Valid colors are {', '.join(self.colors)}.   \n" \
                          f"I'm making the change, so if that's not what you want " \
                          f"you have to summon me again."
                self._logger.info(f"Wrong color: {permalink(comment)}")
                await comment_from_flairies_view.reply(message)

        return False


class FlairTooLongCommand:
    def __init__(self, flairy_detect_user_flair_change, flairy_reddit):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.flairy_detect_user_flair_change = flairy_detect_user_flair_change
        self.flairy_reddit = flairy_reddit

    async def handled(self, body, comment, is_mod):
        if is_mod:
            return False

        flairy = self.flairy_detect_user_flair_change.match(body)
        flair_text = flairy.group(1)
        if len(flair_text) > 63:
            comment_from_flairies_view = await self.flairy_reddit.comment(comment.id, fetch=False)
            message = "(ノಠ益ಠ)ノ彡┻━┻ THE FLAIR TEXT IS TOO LONG!   \nPlease use less than 64 unicode characters"
            self._logger.info(f"Too long: {permalink(comment)}")
            await comment_from_flairies_view.reply(message)
            return True

        return False


class FlairContainsForbiddenPhraseCommand:
    def __init__(self, is_forbidden_comment_message, flairy_detect_user_flair_change):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.is_forbidden_comment_message = is_forbidden_comment_message
        self.flairy_detect_user_flair_change = flairy_detect_user_flair_change

    async def handled(self, body, comment, is_mod):
        if is_mod:
            return False

        flairy = self.flairy_detect_user_flair_change.match(body)
        flair_text = flairy.group(1)
        if self.is_forbidden_comment_message(flair_text):
            self._logger.info(f"Silently refusing to grant flair with restricted content: {flair_text}")
            return True

        return False


class FlairyExplainerCommand:
    def __init__(self, flairy_reddit, available_colors):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._flairy_reddit = flairy_reddit
        self._flairy_explanation_text = f"""Are you talking about me? 😍   
        
This is how it works: you can request a flair with the magic incantation

    !FLAIRY!🚀 some flair text 🚀

The default color is black, but you can change that by writing one of these words at the very end : {', '.join(available_colors)} 

Other available commands:   
- `!FLAIRY!` : if you can't think of a flair, I'll give you one of my own choice 🤭   
- `!FLAIRY:CLEARME!` : remove all flairs and pretend you're a new ape   
- `!FLAIRY:SEALME!` : Justin seduced me to get this 🥵    
- `u/Superstonk-Flairy`  : If you tag me, I'll come around and explain how to get flairs
"""

    async def handled(self, body, comment, is_mod):
        if "u/superstonk-flairy" in body.lower():
            comment_from_flairies_view = await self._flairy_reddit.comment(comment.id, fetch=False)
            self._logger.info(f"Explaining flairs: {permalink(comment)}")
            await comment_from_flairies_view.reply(self._flairy_explanation_text)
            return True

        return False


class ApprovingFlairRequestCommand:
    def __init__(self, flairy_detect_user_flair_change, flairy_channel, add_reactions_to_discord_message,
                 flair_user_function):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.flairy_detect_user_flair_change = flairy_detect_user_flair_change
        self.flairy_channel = flairy_channel
        self.add_reactions_to_discord_message = add_reactions_to_discord_message
        self.flair_user_function = flair_user_function

    async def handled(self, body, comment, is_mod):
        if is_mod:
            return False

        flairy = self.flairy_detect_user_flair_change.match(body)
        flair_text = flairy.group(1)

        self._logger.info(f"Sending flair request {comment} {flair_text}")
        url = permalink(comment)
        e = disnake.Embed(
            url=url,
            colour=disnake.Colour(0).from_rgb(207, 206, 255))
        e.description = f"[Already appproved flair Request: {escape_markdown(comment.body)}]({url})"
        e.add_field("Redditor", f"[{comment.author}](https://www.reddit.com/u/{comment.author})", inline=False)
        message = await self.flairy_channel.send(embed=e)
        await self.add_reactions_to_discord_message(message)

        if flairy is not None:
            await self.flair_user_function(comment=comment, flair_text=flairy.group(1), flair_color=flairy.group(2))
        else:
            await message.edit(content="Flair request was removed in the meantime")
        await WipReaction.handle_reaction(None, message, None)

        return False
