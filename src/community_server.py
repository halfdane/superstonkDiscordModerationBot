import logging
import asyncpraw
from disnake.ext import commands
import sqlite3
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_PATH = ''

def get_creds():
    # create connection to database
    conn = sqlite3.connect(f'{BASE_PATH}config.db')
    discord_bot_token, reddit_client_id, reddit_client_secret, reddit_password, reddit_username, channel_id, subreddit_name \
        = conn.execute("select value from settings where key in "
                       "('discord_bot_token', 'report_channel_id_community', 'reddit_client_id',"
                       "'reddit_client_secret','reddit_username','reddit_password','subreddit_name')"
                       "ORDER BY key;") \
        .fetchall()
    return reddit_client_id[0], reddit_client_secret[0], reddit_username[0], reddit_password[0], subreddit_name[0], \
        channel_id[0], discord_bot_token[0]


def get_reddit(reddit_client_id, reddit_client_secret, reddit_username, reddit_password):
    reddit = asyncpraw.Reddit(client_id=reddit_client_id,
                              client_secret=reddit_client_secret,
                              user_agent="com.halfdane.superstonk_moderation_bot:v0.2.0 (by u/half_dane)",
                              username=reddit_username,
                              password=reddit_password)
    return reddit


# create discord bot
bot = commands.Bot(command_prefix="!")


async def check_new_entry(reddit_client_id, reddit_client_secret, reddit_username, reddit_password, subreddit_name, channel_id):
    check_new_entry.last_entry = None
    reddit = get_reddit(reddit_client_id, reddit_client_secret, reddit_username, reddit_password)

    subreddit = await reddit.subreddit(subreddit_name)

    try:
        modqueue_generator = subreddit.mod.modqueue(limit=1000)
        modqueue = []

        async for entry in modqueue_generator:
            modqueue.append(entry)

        last_entry = modqueue[0] if modqueue else None
        # Check if new entry is detected
        if last_entry and (check_new_entry.last_entry is None or last_entry != check_new_entry.last_entry):

            # Get the details
            title = 'www.reddit.com' + last_entry.permalink
            redditor = last_entry.author
            mod_reports = last_entry.mod_reports
            user_reports = last_entry.user_reports

            # Format the message
            msg = f'title: {title}\n' \
                  f'Redditor: {redditor} \n' \
                  f'Mod Reports: {mod_reports} \n' \
                  f'User Reports: {user_reports}'

            # Log the message
            logger.info(f'Sending message: {msg}')

            # Send the message to discord channel
            try:
                channel = bot.get_channel(int(channel_id))
                await channel.send(msg)
                logger.info('Message sent successfully')
            except Exception as e:
                logger.error(f'Failed to send message: {e}')

            # Update the last entry
            check_new_entry.last_entry = last_entry

        # Wait for a while before checking again
        await asyncio.sleep(10)

    except Exception as e:
        logger.exception('An error occurred in check_new_entry', exc_info=e)


@bot.event
async def on_ready():
    bot.loop.create_task(
        check_new_entry(reddit_client_id, reddit_client_secret, reddit_username, reddit_password, subreddit_name,
                        channel_id))

if __name__ == '__main__':
    reddit_client_id, reddit_client_secret, reddit_username, \
        reddit_password, subreddit_name, channel_id, discord_bot_token = get_creds()

    try:
        bot.run(discord_bot_token)
    except Exception as e:
        logger.exception('An error occurred while running the bot', exc_info=e)
