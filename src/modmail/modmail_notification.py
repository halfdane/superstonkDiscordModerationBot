from modmail.__init import modmail_state
from reddit_item_handler import Handler
import disnake
from disnake.components import SelectOption, ActionRow
from disnake.ui import Modal, View
from disnake.ext import commands
from disnake import TextInputStyle


class TextSnippetSelection(disnake.ui.Select):
    def __init__(self, options, on_select, modmail, hanami_configuration):
        super().__init__(
            options=options,
            max_values=len(options),
            placeholder="Compose the response")
        self.on_select = on_select
        self.hanami_configuration = hanami_configuration
        self.modmail = modmail

    async def callback(self, inter: disnake.MessageInteraction):
        everything_but_hey_and_bye = [i for i in self.values if i not in ['Hey', 'Bye']]
        response = []
        if 'Hey' in self.values:
            response += [self.hanami_configuration.greeting]

        response += [self.hanami_configuration.config[i] for i in everything_but_hey_and_bye]

        if 'Bye' in self.values:
            response += [self.hanami_configuration.bye]

        on_select = self.on_select
        modmail = self.modmail

        class MailResponseEditor(disnake.ui.Modal):
            def __init__(self):
                components = [
                    disnake.ui.TextInput(
                        label="response",
                        custom_id="adjusted_text",
                        value='\n\n'.join(response),
                        style=TextInputStyle.paragraph
                    )]
                super().__init__(title="This would be your response", components=components)

            async def callback(self, modal_interaction: disnake.ModalInteraction):
                moderator_name = modal_interaction.author
                await modal_interaction.response.send_message("Sending response")
                await on_select(modmail, moderator_name, modal_interaction.text_values['adjusted_text'])

        await inter.response.send_modal(modal=MailResponseEditor())


class ModmailNotification(Handler):

    def __init__(self, qvbot_reddit, superstonk_subreddit, send_discord_message, hanami_configuration, **kwargs):
        super().__init__()
        self.superstonk_subreddit = superstonk_subreddit
        self.send_discord_message = send_discord_message
        self.hanami_configuration = hanami_configuration
        self.qvbot_reddit = qvbot_reddit

    def wot_doing(self):
        return "Notify on discord when modmails happen"

    async def on_ready(self, **kwargs):
        self._logger.warning(self.wot_doing())

    async def on_select(self, modmail, moderator_name, response):
        await modmail.reply(body=f"sending on behalf of {moderator_name}", internal=True)
        await modmail.reply(body=response, author_hidden=True)
        await modmail.archive()

    async def take(self, modmail_conversation):
        modmail = await self.superstonk_subreddit.modmail(modmail_conversation.id)
        state = modmail_state(modmail)
        if state.archived is not None:
            return

        options = [SelectOption(label='Hey', default=True), SelectOption(label='Bye', default=True)]
        options += [SelectOption(label=i) for i in self.hanami_configuration.config]
        selection_holder = View()
        selection_holder.add_item(TextSnippetSelection(options=options, on_select=self.on_select,
                                                       hanami_configuration=self.hanami_configuration,
                                                       modmail=modmail))

        await self.send_discord_message(item=modmail,
                                        description_beginning="Received",
                                        fields={
                                            'lastmessage': modmail.messages[len(modmail.messages) - 1].body_markdown},
                                        view=selection_holder
                                        )
