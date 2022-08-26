import logging
from datetime import datetime

import aiosqlite

from helper.moderation_bot_configuration import CONFIG_HOME

COMMENTS_DB = f"{CONFIG_HOME}/modmailconversations.db"


class ModmailConversationRepository:
    def __init__(self, database=COMMENTS_DB):
        self.database = database
        self._logger = logging.getLogger(self.__class__.__name__)

    async def on_ready(self, **_):
        async with aiosqlite.connect(self.database) as db:
            await db.execute('CREATE TABLE if not exists '
                             'CONVERSATIONS (id PRIMARY KEY, last_updated);')

    async def store(self, conversations):
        db_conversations = [(item.id, datetime.fromisoformat(item.last_updated).timestamp()) for item in conversations]
        async with aiosqlite.connect(self.database) as db:
            await db.executemany('''
                    INSERT INTO CONVERSATIONS(id, last_updated) VALUES (?, ?)
                    ON CONFLICT(id) DO UPDATE SET last_updated=excluded.last_updated
                    ''', db_conversations)
            await db.commit()

    async def contains(self, conversation):
        async with aiosqlite.connect(self.database) as db:
            async with db.execute('select count(*) from CONVERSATIONS where id=:id and last_updated=:last_updated',
                                  {'id': conversation.id, 'last_updated': datetime.fromisoformat(conversation.last_updated).timestamp() }) as cursor:
                rows = [row async for row in cursor]
                return rows[0][0] >= 1
