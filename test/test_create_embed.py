from superstonkDiscordModerationBot import SuperstonkModerationBot


class TestCreateEmbed:

    def test_happy_path(self):
        testee = SuperstonkModerationBot(None)

        testee.create_embed(None, None)