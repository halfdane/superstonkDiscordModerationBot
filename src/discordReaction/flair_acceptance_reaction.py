import re

import discordReaction
from bot import SuperstonkModerationBot
from discordReaction.abstract_reaction import Reaction


class FlairAcceptanceReaction(Reaction):
    emoji = '🧚'

    _flairy_detection = "!flairy!"

    _flairy_detect_user_flair_change = \
        re.compile(r".*!\s*FLAIRY\s*!(.*?)(?:(red|blue|pink|yellow|green|black))?\s*$",
                   re.IGNORECASE | re.MULTILINE | re.DOTALL)

    _templates = {"red": "0446bc04-91c0-11ec-8118-ce042afdde96",
                  "blue": "6e40ab4c-f3cd-11eb-889e-ae4cdf00ff3b",
                  "pink": "6de5f58e-f3ce-11eb-af43-eae78a59944d",
                  "yellow": "5f91a294-f3ce-11eb-948b-d26e0741292d",
                  "green": "7dfd44fe-f3ce-11eb-a228-aaac7809dc68",
                  "black": "8abdf72e-f3ce-11eb-b3e3-22147bc43b70"}

    _default_color = "black"

    async def handle(self, message, comment, emoji, user, channel, bot: SuperstonkModerationBot):
        body = getattr(comment, 'body', "")
        subreddit = bot.subreddit
        flairy_reddit = bot.flairy_reddit
        mods = bot.moderators

        user_to_be_flaired = comment.author
        flairy_user = await flairy_reddit.user.me()
        if self._flairy_detection.lower() in body.lower() \
                and user_to_be_flaired not in mods \
                and user_to_be_flaired != flairy_user:
            flairy = self._flairy_detect_user_flair_change.match(comment.body)
            if flairy:
                await self.flair_user(subreddit, comment, flairy_reddit, user_to_be_flaired, flairy.group(1), flairy.group(2))
                await discordReaction.handle(message, comment, "✅", user, channel, bot)

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
