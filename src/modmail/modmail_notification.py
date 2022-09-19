import disnake
from disnake import TextInputStyle
from disnake.components import SelectOption
from disnake.ui import View

from modmail.__init import modmail_state
from reddit_item_handler import Handler


class ModmailNotification(Handler):

    def __init__(self, qvbot_reddit, superstonk_subreddit, send_discord_message, hanami_configuration, **kwargs):
        super().__init__()
        self.superstonk_subreddit = superstonk_subreddit
        self.send_discord_message = send_discord_message
        self.hanami_configuration = hanami_configuration
        self.qvbot_reddit = qvbot_reddit

    def wot_doing(self):
        return "Notify on discord when modmails happen"

    async def on_select(self, modmail, moderator_name, response):
        await modmail.reply(body=f"sending on behalf of {moderator_name}", internal=True)
        await modmail.reply(body=response, author_hidden=True)
        await modmail.archive()

    async def take(self, modmail_conversation):
        modmail = await self.superstonk_subreddit.modmail(modmail_conversation.id)
        state = modmail_state(modmail)
        if state.archived is not None:
            return

        await self.send_discord_message(item=modmail,
                                        description_beginning="Received",
                                        fields={
                                            'lastmessage': modmail.messages[len(modmail.messages) - 1].body_markdown},
                                        )
