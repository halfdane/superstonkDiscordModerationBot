import logging
import random
import re

from helper.links import permalink, make_safe
from reddit_item_handler import Handler


class Flairy(Handler):
    _templates = {"red": "0446bc04-91c0-11ec-8118-ce042afdde96",
                  "blue": "6e40ab4c-f3cd-11eb-889e-ae4cdf00ff3b",
                  "pink": "6de5f58e-f3ce-11eb-af43-eae78a59944d",
                  "yellow": "5f91a294-f3ce-11eb-948b-d26e0741292d",
                  "green": "7dfd44fe-f3ce-11eb-a228-aaac7809dc68",
                  "black": "8abdf72e-f3ce-11eb-b3e3-22147bc43b70",
                  "white": "a39da5fa-f46d-11ec-b46b-42cab4344c7a"}

    _default_color = "black"

    def __init__(self, superstonk_moderators=[], flairy_reddit=None,
                 automod_configuration=None, is_live_environment=False,
                 flairy_comment_repo=None, flairy_reddit_username=None,
                 subreddit_name=None,
                 **kwargs):
        Handler.__init__(self)

        self.superstonk_moderators = superstonk_moderators
        self.flairy_reddit = flairy_reddit
        self.subreddit_name = subreddit_name
        self.flairy_reddit_username = flairy_reddit_username
        self.is_live_environment = is_live_environment
        self.automod_configuration = automod_configuration
        self.flairy_comment_repo = flairy_comment_repo

        self.flairy_detect_user_flair_change = None
        self.detect_flairy_command = None
        self._commands = None

    def setup_commands(self):
        flairy_command_detection = r".*!\s*FL?AIRY"
        flair_command = rf"{flairy_command_detection}\s*!"

        flairy_text = r"\s*(.*?)"
        _valid_colors = fr"(?:\s*\b({'|'.join(self._templates.keys())}))?\s*"

        regex_flags = re.IGNORECASE | re.MULTILINE | re.DOTALL

        self.detect_flairy_command = \
            re.compile(rf"{flairy_command_detection}|u/{self.flairy_reddit_username}", regex_flags)

        self.flairy_detect_user_flair_change = \
            re.compile(rf"{flair_command}{flairy_text}{_valid_colors}$", regex_flags)

        colors = list(self._templates.keys())
        self._commands = [
            CommentAlreadyHasAResponse(flairy_command_detection, regex_flags, self.flairy_reddit_username),
            RememberComment(self.flairy_comment_repo),
            FlairyExplainerCommand(self.flairy_reddit, self._templates.keys(), self.flairy_reddit_username),
            IsBlackListed(self.flairy_reddit),
            ClearCommand(self.flairy_reddit, flairy_command_detection, regex_flags, self.subreddit_name),
            SealmeCommand(self._templates[self._default_color], flairy_command_detection, regex_flags,
                          self.flair_user),
            RandomFlairCommand(flairy_command_detection, regex_flags, self.flair_user, colors),
            WrongColorCommand(self.flairy_reddit, flair_command, regex_flags, colors),
            FlairTooLongCommand(self.flairy_detect_user_flair_change, self.flairy_reddit),
            FlairContainsForbiddenPhraseCommand(self.automod_configuration,
                                                self.flairy_detect_user_flair_change),
            ApplyFlairCommand(self.flairy_detect_user_flair_change, self.flair_user)
        ]

    def wot_doing(self):
        return "Handle flair requests"

    async def on_ready(self, **kwargs):
        self.setup_commands()
        self._logger.warning(self.wot_doing())

    async def take(self, comment):
        body = getattr(comment, 'body', "")
        author = getattr(getattr(comment, "author", None), "name", None)
        if author == self.flairy_reddit_username:
            self._logger.debug(f"Not answering to myself: {permalink(comment)}")
            return

        if self.detect_flairy_command.search(body):
            is_mod = author in self.superstonk_moderators

            self._logger.debug(
                f"seems to be a flairy command from {author}. Treat like mod? {is_mod} {permalink(comment)}")

            for command in self._commands:
                if await command.handled(body, comment, is_mod):
                    return

    async def flair_user(self, comment, flair_text, flair_color=None, template=None, message=""):
        self._logger.debug("attempting to flair user")
        flair_text = flair_text.strip()
        color = (flair_color or self._default_color).lower().strip()
        template = (template or self._templates[color])
        previous_flair = getattr(comment, 'author_flair_text', "")
        log_message = f"[{make_safe(comment.author)}] [{make_safe(previous_flair)}] => [{make_safe(flair_text)}] in {color}"
        subreddit_from_flairies_view = await self.flairy_reddit.subreddit(self.subreddit_name)

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


class CommentAlreadyHasAResponse:
    def __init__(self, flairy_command_detection, flags, flairy_reddit_username):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._random_flair_command = \
            re.compile(rf"{flairy_command_detection}\s*!$", flags)
        self.flairy_reddit_username = flairy_reddit_username

    async def handled(self, body, comment, is_mod):
        await comment.refresh()
        for response in comment.replies:
            author_name__lower = getattr(getattr(response, "author", None), "name", "").lower()
            if author_name__lower == self.flairy_reddit_username.lower():
                self._logger.info(f"Flairy already responded: {permalink(response)}")
                return True
        self._logger.debug("comment doesn't have a response yet")
        return False


class RememberComment:
    def __init__(self, flairy_comment_repo):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.flairy_comment_repo = flairy_comment_repo

    async def handled(self, body, comment, is_mod):
        await self.flairy_comment_repo.push(comment.id, body)
        return False


class IsBlackListed:
    blacklisted_string = '[lock]'

    def __init__(self, flairy_reddit):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.flairy_reddit = flairy_reddit

    async def handled(self, body, comment, is_mod):
        current_flair = getattr(comment, 'author_flair_text', "") or ""
        blacklisted = ('%s' % self.blacklisted_string) in current_flair.lower()
        if blacklisted:
            self._logger.info(f"Refusing to interact with blacklisted user.   \n"
                              f"Flair: {current_flair}   \n text: {body}   \n comment {permalink(comment)} ")
            comment_from_flairies_view = await self.flairy_reddit.comment(comment.id, fetch=False)

            message = f"Sorry, I'm cowardly refusing to change a locked flair.   \n" \
                      f"Please  approach the mods for clarification.\n"
            self._logger.info(f"Wrong color: {permalink(comment)}")
            await comment_from_flairies_view.reply(message)

        return blacklisted


class RandomFlairCommand:

    def __init__(self, flairy_command_detection, flags, flair_user_function, colors):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._random_flair_command = \
            re.compile(rf"{flairy_command_detection}\s*!$", flags)
        self.flair_user_function = flair_user_function
        self.colors = colors

    async def handled(self, body, comment, is_mod):
        if is_mod:
            self._logger.debug("Refusing to give random flair to mods")
            return False

        if self._random_flair_command.match(body):
            await self._bestow_random_flair(comment)
            return True

        self._logger.debug("It's not a request for a random flair")
        return False

    async def _bestow_random_flair(self, comment):
        _emojis = ['🏴‍☠️', '💪', '💎', '🎊', '🌕',
                   '🦍🚀', '🦍', '💎🙌🏻', '🎮🛑',
                   '♾️', '🐵', '💙', '🍦💩🪑'
                   ]

        _flairs = ["TOMORROW!", "I'm here for the memes", "We're in the endgame now", "Gamecock",
                   "FUCK YOU PAY ME", "Locked and loaded ","Nothin But Time", "Today's the daaay",
                   "GME to the Moon! ", "I am not a cat", "I like the stock. ", "Just Like the Stonk",
                   "Infinite Risk ", "Hang in There! ", "Power to the Players ", "Power to the Creators ",
                   "Probably nothing", "Gimme me my money ", "GME", "Apes together strong", "GME go Brrrr ",
                   "Gamestop 4U", "Casual lurker until MOASS", "GMERICA ", "GME ", "Superstonk Ape", "GME to the Moon!",
                   "Pepperidge Farm remembers", "LOVE GME ", "SuperApe ", "What’s an exit strategy",
                   "ZEN APE ", "No Cell No Sell", "GameStop", "Power to the Players ", "Crayon Sniffer ",
                   "Mods are sus", "Always has been", "Apes together strong ", "wen moon", "I just love the stock ",
                   "DEEP FUCKING VALUE ", "Fuck no I’m not selling my GME!", "Fuck Citadel", "I SAID WE GREEN TODAY",
                   "FUD is the Mind-Killer", "No target, just up!", "We are in a completely fraudulent system ",
                   "Get rich or die buyin’", "Buy now, ask questions later ", "Bullish",
                   "👮 Hodl Patrodl 🚓 wee woo wee woo 🚨", "MELV-OUT", "Naked, 🩳 and 🦏",
                   "SWAPPED FASTER THAN KENNY'S ALGO", "Gimme flair", "RYANS MY DAD",
                   "We can stay retarded longer than they can stay solvent", "Fuel the Rocket!",
                   "NFT = never felt a titty", "Pirate Bae", "Go Ahead. Make My Dip Day",
                   "Melvin was only the beginning", "Yeet the Rich", "Swagasaurus FLEX",
                   "Today is yesterday's tomorrow", "Tendie side of the M🌒🌘N", "99%’s Revenge 🦍",
                   "My retardation > SHF solvency", "more like SHITadel, amirite?", "Hodl-eh-hewhooo", "Game On, Anon",
                   "I FOOKIN LOVE GME", "Zero or Many Zeroes", "paperhand deez nuts", "Smooth 🧠 AF",
                   "On our way to conquer Uranus", "Stay hydrated, drink hedgie tears!!", "Uranian Princess",
                   "That's no moon, that's Uranus!", "No Surrender", "high noon at Mount MOASS", "MOASSMAN",
                   "“Oops, MOASS?”", ":cs: :GS: :pwrup:", "( ^ ) ( ^ )", "eew eew llams a evah I", "Crayon Hog",
                   "741piece", "Divide My Stride", "4X the Zen!", "Merry Splitmas!", "The Bee’s Knees Squeeze",
                   "Show me your purple circle", "Buy now, ask questions later", "Ape’n’stein", "glorilla grip hands",
                   "Unrealised Billionaire", "'Clueless' Investor", "MICRO APE", "Hedgies R Fuk", "Knights of Harambe",
                   "Superstonk Ape", "Dip Split Dip Rip", "Who sneezed?",
                   ]

        emojis = random.sample(_emojis, 2)
        flair_text = f"🧚🧚{emojis[0]} {random.sample(_flairs, 1)[0]} {emojis[1]}🧚🧚"
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
            self._logger.debug("Refusing SEALME mods")
            return False

        if self._sealme_command.match(body):
            current_flair = getattr(comment, 'author_flair_text', "") or ""
            current_template = getattr(comment, 'author_flair_template_id', self._default_template)
            message = 'Witness meee /u/Justind123  \n\n'
            await self.flair_user_function(
                comment=comment,
                flair_text=current_flair + '🦭',
                template=current_template,
                message=message)
            self._logger.info(f"SEALING: {permalink(comment)}")
            return True

        self._logger.debug("comment isn't a sealme request")
        return False


class ClearCommand:
    def __init__(self, flairy_reddit, flairy_command_detection, flags, subreddit_name):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.flairy_reddit = flairy_reddit
        self._reset_command = \
            re.compile(rf"{flairy_command_detection}\s*:\s*CLEARME\s*!", flags)
        self.subreddit_name = subreddit_name

    async def handled(self, body, comment, is_mod):
        if is_mod:
            self._logger.debug("Refusing to clear mods' flair")
            return False

        if self._reset_command.match(body):
            message = 'Clearing the flair as requested  \n\n' + r'(✿\^‿\^)━☆ﾟ.*･｡ﾟ '
            self._logger.info(f"Clearing flair: {permalink(comment)}")

            subreddit_from_flairies_view = await self.flairy_reddit.subreddit(self.subreddit_name)
            await subreddit_from_flairies_view.flair.delete(redditor=comment.author)
            comment_from_flairies_view = await self.flairy_reddit.comment(comment.id, fetch=False)
            await comment_from_flairies_view.reply(message)
            return True

        self._logger.debug("comment isn't a flair clearing request")
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
            self._logger.debug("refusing to validate mods' color choice")
            return False

        if match := self._detect_last_word.match(body):
            last_word = match.group(1)
            if last_word.lower() in ["orange", "grey", "gray", "purple"]:
                comment_from_flairies_view = await self.flairy_reddit.comment(comment.id, fetch=False)
                message = f"(ノಠ益ಠ)ノ彡┻━┻ {last_word.upper()} IS NOT A VALID COLOR!   \n" \
                          f"Valid colors are {', '.join(self.colors)}.   \n" \
                          f"I'm making the change, so if that's not what you want " \
                          f"you have to summon me again."
                self._logger.info(f"Wrong color: {permalink(comment)}")
                await comment_from_flairies_view.reply(message)

        self._logger.debug("Found no problem with color choice")
        return False


class FlairTooLongCommand:
    def __init__(self, flairy_detect_user_flair_change, flairy_reddit):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.flairy_detect_user_flair_change = flairy_detect_user_flair_change
        self.flairy_reddit = flairy_reddit

    async def handled(self, body, comment, is_mod):
        if is_mod:
            self._logger.debug("refusing to validate length of mod's flairy request")
            return False

        flairy = self.flairy_detect_user_flair_change.match(body)
        flair_text = flairy.group(1)
        if len(flair_text) > 63:
            comment_from_flairies_view = await self.flairy_reddit.comment(comment.id, fetch=False)
            message = "(ノಠ益ಠ)ノ彡┻━┻ THE FLAIR TEXT IS TOO LONG!   \nPlease use less than 64 unicode characters"
            self._logger.info(f"Too long: {permalink(comment)}")
            await comment_from_flairies_view.reply(message)
            return True

        self._logger.debug("Found no problem with the length of the flair request")
        return False


class FlairContainsForbiddenPhraseCommand:
    def __init__(self, automod_configuration, flairy_detect_user_flair_change):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.automod_configuration = automod_configuration
        self.flairy_detect_user_flair_change = flairy_detect_user_flair_change

    async def handled(self, body, comment, is_mod):
        if is_mod:
            self._logger.debug("refusing to check mod's flair request for restricted words")
            return False

        flairy = self.flairy_detect_user_flair_change.match(body)
        flair_text = flairy.group(1)
        if self.automod_configuration.is_forbidden_comment_message(flair_text):
            self._logger.info(f"Silently refusing to grant flair with restricted content: {flair_text}")
            return True

        self._logger.debug("Found no restricted words in flair request")
        return False


class FlairyExplainerCommand:
    def __init__(self, flairy_reddit, available_colors, flairy_reddit_username):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._flairy_reddit = flairy_reddit
        self.flairy_reddit_username = flairy_reddit_username
        self._flairy_explanation_text = f"""Are you talking about me? 😍   
        
This is how it works: you can request a flair with the magic incantation

    !FLAIRY!🚀 some flair text 🚀

The default color is black, but you can change that by writing one of these words at the very end : {', '.join(available_colors)} 

Other available commands:   
- `!FLAIRY!` : if you can't think of a flair, I'll give you one of my own choice 🤭   
- `!FLAIRY:CLEARME!` : remove all flairs and pretend you're a new ape   
- `!FLAIRY:SEALME!` : Justin seduced me to get this 🥵    
- `u/{self.flairy_reddit_username}`  : If you tag me, I'll come around and explain how to get flairs

Please note that the flairy will refuse to change your flair if it contains the string `{IsBlackListed.blacklisted_string}`.

Some custom emojis are supported, like `:triforce:` - 
[please check this post for details](https://new.reddit.com/r/Superstonk/comments/v89p0h/new_superstonk_user_flair_emojis_how_to_edit_your/id8hj7r/)
"""

    async def handled(self, body, comment, is_mod):
        if f"u/{self.flairy_reddit_username}".lower() in body.lower():
            comment_from_flairies_view = await self._flairy_reddit.comment(comment.id, fetch=False)
            self._logger.info(f"Explaining flairs: {permalink(comment)}")
            await comment_from_flairies_view.reply(self._flairy_explanation_text)
            return True

        self._logger.debug("comment isn't a flairy explanation request")
        return False


class ApplyFlairCommand:
    def __init__(self, flairy_detect_user_flair_change, flair_user_function):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.flairy_detect_user_flair_change = flairy_detect_user_flair_change
        self.flair_user_function = flair_user_function

    async def handled(self, body, comment, is_mod):
        if is_mod:
            self._logger.debug("refusing to bestow flair upon mods")
            return False

        flairy = self.flairy_detect_user_flair_change.match(body)

        if flairy is not None:
            await self.flair_user_function(comment=comment, flair_text=flairy.group(1), flair_color=flairy.group(2))
            return True

        self._logger.debug("comment isn't a flair request at all")
        return False
