import csv
import logging
from datetime import datetime

import aiohttp


class TradingHaltsReporter():

    def __init__(self, send_discord_message, **kwargs):
        super().__init__()
        self.send_discord_message = send_discord_message
        self._logger = logging.getLogger(self.__class__.__name__)

    def wot_doing(self):
        return "Discord notification when trading halts occur"

    async def on_ready(self, scheduler, **kwargs):
        self._logger.warning(self.wot_doing())
        scheduler.add_job(self.notify_trading_halt, "cron", minute="*/5", next_run_time=datetime.now())

    async def notify_trading_halt(self):
        self._logger.debug("checking if a trading halt has occured")
        halted = await self.trading_halt()
        if halted is not None:
            await self.send_discord_message(description_beginning="**TRADING HALTED**", fields=halted)

    async def trading_halt(self, symbol="GME"):
        # fetch csv with current halts
        async with aiohttp.ClientSession() as session:
            async with session.get('https://www.nyse.com/api/trade-halts/current/download') as response:
                content = await response.text()
                lines = content.splitlines()
                reader = csv.reader(lines, delimiter=',')
                for i, row in enumerate(reader):
                    if i == 0:
                        headers = row
                        symbol_index = row.index("Symbol")
                    if len(row) > symbol_index and row[symbol_index] == symbol:
                        result = {}
                        for i, header in enumerate(headers):
                            if len(row[i]) > 0:
                                result[header] = row[i]
                        result['URL'] = 'https://www.nyse.com/trade-halt-current'
                        return result

        return None
