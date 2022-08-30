from modmail.__init import modmail_state
from reddit_item_handler import Handler
import disnake
from disnake.components import SelectOption


class MySelection(disnake.ui.Select):
    def __init__(self, options, on_select):
        super().__init__(
            options=options,
            max_values=len(options),
            placeholder="Compose the response")
        self.on_select = on_select

    async def callback(self, inter: disnake.ModalInteraction):
        await self.on_select(inter, self.values)


class SelectionHolder(disnake.ui.View):
    def __init__(self, options, on_select):
        super().__init__(timeout=None)
        self.add_item(MySelection(options=options, on_select=on_select))


class ModmailNotification(Handler):

    def __init__(self, send_discord_message, hanami_configuration, **kwargs):
        super().__init__()
        self.send_discord_message = send_discord_message
        self.hanami_configuration = hanami_configuration

    def wot_doing(self):
        return "Notify on discord when modmails happen"

    async def on_ready(self, **kwargs):
        self._logger.warning(self.wot_doing())

    async def on_select(self, interaction, selected):
        everything_but_hey_and_bye = [i for i in selected if i not in ['Hey', 'Bye']]
        response = []
        if 'Hey' in selected:
            response += [self.hanami_configuration.greeting]

        response += [self.hanami_configuration.config[i] for i in everything_but_hey_and_bye]

        if 'Bye' in selected:
            response += [self.hanami_configuration.bye]
        await interaction.response.send_message('\n\n'.join(response))

    async def take(self, item):
        state = modmail_state(item)
        if state.archived is not None:
            return

        options = [SelectOption(label='Hey', default=True), SelectOption(label='Bye', default=True)]
        options += [SelectOption(label=i) for i in self.hanami_configuration.config]
        selection_holder = SelectionHolder(options, self.on_select)

        await self.send_discord_message(item=item,
                                        description_beginning="NEW",
                                        channel='report_comments_channel',
                                        fields={'lastmessage': item.messages[len(item.messages) - 1].body_markdown},
                                        view=selection_holder)
