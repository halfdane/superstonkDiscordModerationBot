from reddit_item_handler import Handler
import disnake
from disnake.components import SelectOption


class MySelection(disnake.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="Compose the response")
        intro = SelectOption(label='Greeting', value='Some friendly words to greet',
                             description="Greet the user", default=True)
        a = SelectOption(label='a', value='valueA', description="The value of a")
        b = SelectOption(label='b', value='valueB', description="The value of b")
        c = SelectOption(label='c', value='valueC', description="The value of c")
        end = SelectOption(label='End', value='forever yours', description="say good bye", default=True)
        self.options = [intro, a, b, c, end]
        self.max_values = 5
        intro.default = True
        end.default = True

    # The callback received when the user input is completed.
    async def callback(self, inter: disnake.ModalInteraction):
        self.disabled = True
        await inter.response.send_message(f"You selected {self.values}.")


class SelectionHolder(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MySelection())


class ModmailNotification(Handler):

    def __init__(self, send_discord_message, **kwargs):
        super().__init__()
        self.send_discord_message = send_discord_message

    def wot_doing(self):
        return "Notify on discord when modmails happen"

    async def on_ready(self, **kwargs):
        self._logger.warning(self.wot_doing())

    async def take(self, item):
        self._logger.warning(f"Got a new convo: {vars(item)}")

        await self.send_discord_message(item=item,
                                        description_beginning="NEW",
                                        channel='report_comments_channel',
                                        view=SelectionHolder())

