import asyncio
import logging

from datetime import datetime, timedelta
import random


class CalculatePostStatistics:

    def __init__(self, post_repo=None, asyncio_loop=None, **kwargs):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.persist_posts = post_repo
        self.asyncio_loop = asyncio_loop

    async def on_ready(self, scheduler, **kwargs):
        self._logger.info(f"Scheduling statistics calculation")
        scheduler.add_job(self.update_posts, "cron", hour="*")

    async def update_posts(self):
        self._logger.info(f"Starting to update posts database")

