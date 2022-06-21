import logging

import aiosqlite

from helper.moderation_bot_configuration import CONFIG_HOME

POSTS_DB = f"{CONFIG_HOME}/url_posts.db"


class UrlPosts:
    def __init__(self, database=POSTS_DB):
        self.database = database
        self._logger = logging.getLogger(self.__class__.__name__)

    async def on_ready(self, **_):
        async with aiosqlite.connect(self.database) as db:
            await db.execute('CREATE TABLE if not exists '
                             'URL_POSTS (id PRIMARY KEY, url);')

    async def store(self, post):
        async with aiosqlite.connect(self.database) as db:
            await db.execute('''
                    INSERT INTO URL_POSTS(id, url) VALUES (?, ?) ON CONFLICT(id) DO NOTHING
                    ''', (post.id, getattr(post, 'url', "NONE")))
            await db.commit()

    async def fetch(self, url):
        async with aiosqlite.connect(self.database) as db:
            statement = 'select id from URL_POSTS where url=:url'
            async with db.execute(statement, {'url': url}) as cursor:
                return [row[0] async for row in cursor]

    async def fetch_like(self, url):
        async with aiosqlite.connect(self.database) as db:
            statement = 'select id from URL_POSTS where url like :url'
            async with db.execute(statement, {'url': f"{url}%"}) as cursor:
                return [row[0] async for row in cursor]

    async def remove(self, ids):
        async with aiosqlite.connect(self.database) as db:
            statement = 'delete from URL_POSTS where id = :id'
            for id in ids:
                await db.execute(statement, {'id': id})
            await db.commit()
