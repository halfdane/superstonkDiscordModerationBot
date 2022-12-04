import disnake
from disnake.ext import commands

from discord_reaction_handler import Reaction


class ModbotListCog(commands.Cog):
    def __init__(self, components, **kwargs):
        self.components = components

    @commands.slash_command(
        description="Lists all functionalities of the moderation bot."
    )
    async def modbot_info(self, ctx):
        await ctx.response.defer()
        internal_stuff = {}
        discord_commands = {}
        discord_reactions = {}
        subreddit_visible_behaviour = {}

        for name, component in self.components.items():
            if hasattr(component, 'wot_doing'):
                wot_doing = component.wot_doing()
                if isinstance(component, commands.Cog):
                    discord_commands[name] = wot_doing
                elif isinstance(component, Reaction):
                    discord_reactions[name] = wot_doing
                elif '[internal]' in wot_doing:
                    internal_stuff[name] = wot_doing
                else:
                    subreddit_visible_behaviour[name] = wot_doing

        await ctx.edit_original_message(embeds=[
            await self.add_components(subreddit_visible_behaviour, "General behaviour"),
            await self.add_components(discord_reactions, "Reactions to discord emojis"),
            await self.add_components(discord_commands, "Discord commands"),
            await self.add_components(internal_stuff, "Internal stuff that happens"),
        ])

    async def add_components(self, compontent_dict, title):
        e = disnake.Embed(title=title, colour=disnake.Colour(0).from_rgb(207, 206, 255))
        for k, v in compontent_dict.items():
            e.add_field(k, v, inline=False)
        return e

    def wot_doing(self):
        return f"discord command `/modbot_info`: Lists all functionalities of the moderation bot."

