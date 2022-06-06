import asyncio
import logging

import disnake

from disnake.ext import commands
from yahoo_fin import stock_info as si
from millify import millify


class GmeTickerAsUserName:

    def __init__(self, superstonk_discord_moderation_bot, **kwargs):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.superstonk_discord_moderation_bot = superstonk_discord_moderation_bot

    async def on_ready(self, scheduler, **kwargs):
        self._logger.info("Scheduling gamestop ticker ")
        scheduler.add_job(self.change_name_to_market_data_with_timeout, "cron", second="*/10")

    async def change_name_to_market_data_with_timeout(self):
        try:
            await asyncio.wait_for(self.change_name_to_market_data(), timeout=9)
        except asyncio.TimeoutError:
            pass

    async def change_name_to_market_data(self):
        change = si.get_quote_data("gme")
        market_state = change['marketState']
        if market_state == "PRE":
            price = change['preMarketPrice']
            activity = f"PM: ${millify(change['preMarketChange'], 2)} " \
                       f"{millify(change['preMarketChangePercent'], 2)}% "
        elif market_state == "REGULAR":
            price = si.get_live_price("gme")
            activity = f"${millify(change['regularMarketChange'], 2)} " \
                       f"{millify(change['regularMarketChangePercent'], 2)}% " \
                       f"{millify(change['regularMarketVolume'], 2)}"
        elif market_state == "POST":
            price = change['postMarketPrice']
            activity = f"AH: ${millify(change['postMarketChange'], 2)} " \
                       f"{millify(change['postMarketChangePercent'], 2)}% "
        else:
            price = change['postMarketPrice']
            activity = f"Closed: ${millify(change['postMarketPrice'], 2)}"

        live_price = str(round(price, 2))

        name = f"GME: ${live_price}"
        for guild in self.superstonk_discord_moderation_bot.guilds:
            if guild:
                await guild.me.edit(nick=name)
        await self.superstonk_discord_moderation_bot.change_presence(
            activity=disnake.Activity(type=disnake.ActivityType.watching, name=activity))

