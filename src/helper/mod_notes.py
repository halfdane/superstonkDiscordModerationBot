from datetime import datetime as dt

import disnake

from helper.discord_text_formatter import b, e, link, cut


def __chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


async def get_mod_notes(reddit, redditor_param):
    api_path = "api/mod/notes"
    response = await reddit.get(api_path, params={"subreddit": "Superstonk", "user": redditor_param})
    embeds = []
    redditor = None
    for note_chunk in __chunks(list(reversed(response['mod_notes'])), 10):
        embed = disnake.Embed(colour=disnake.Colour(0).from_rgb(207, 206, 255))
        redditor = note_chunk[0]['user']
        notes = [
            f"{dt.fromtimestamp(int(n['created_at'])).strftime('%Y-%m-%d %H:%M:%S')} "
            f"{b(n['operator'])} {e(n['mod_action_data']['action'])} "
            f"{n['mod_action_data']['details']} {cut(n['mod_action_data']['description'], 100)}"
            for n in note_chunk]
        embed.description = "\n".join(notes)
        embeds.append(embed)
    embeds[0].description = f"**ModNotes for {redditor}**\n" + embeds[0].description
    return embeds