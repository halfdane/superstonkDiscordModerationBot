from datetime import datetime as dt

import disnake

from helper.discord_text_formatter import cut
from disnake.utils import escape_markdown
import itertools


def __transform_mod_note(n):
    note = {
        "created_at": dt.fromtimestamp(int(n['created_at'])).strftime('%Y-%m-%d %H:%M:%S'),
        "mod": n['operator'],
        "user": n['user'],
        "action": n['mod_action_data']['action'] or n['user_note_data']['label'] or "",
        "details": n['mod_action_data']['details'] or "",
        "fullname": n['mod_action_data']['reddit_id'] or n['user_note_data']['reddit_id'] or "",
        "description": n['mod_action_data']['description'] or n['user_note_data']['note'] or ""
    }
    return note


async def fetch_all_notes(reddit, redditor_param, before=None):
    params = {"subreddit": "Superstonk", "user": redditor_param, "limit": 100}
    if before:
        params["before"] = before
    api_path = "api/mod/notes"
    response = await reddit.get(api_path, params=params)
    notes = list(map(__transform_mod_note, reversed(response['mod_notes'])))

    if response['has_next_page']:
        end_cursor = response['end_cursor']
        notes = await fetch_all_notes(reddit, redditor_param, end_cursor) + notes

    infos = reddit.info([note["fullname"] for note in notes])
    infos = {info.fullname: info async for info in infos}

    def __update(dict_, info):
        dict_.update(info)
        return dict_

    notes = [__update(note, {'object': infos.get(note['fullname'])}) for note in notes]

    def __as_link(object):
        if object:
            title = getattr(object, 'title', getattr(object, 'body', "")).replace("\n", "<br>")[:75]
            title = disnake.utils.escape_markdown(title)
            return f"\n[{title}](https://www.reddit.com{object.permalink})"
        else:
            return ""

    strings = {f"**{n['created_at']}**":
               f"{n['mod']} {n['action']} "
               f"{n['details']} {cut(n['description'], 100)} "
               f"{__as_link(n['object'])}"
               for n in notes}
    return strings


async def get_mod_notes(reddit, redditor_param):
    embeds = []
    notes = await fetch_all_notes(reddit, redditor_param)

    def chunked(it, size):
        it = iter(it)
        while True:
            p = tuple(itertools.islice(it, size))
            if not p:
                break
            yield p

    for note_chunk in chunked(notes.items(), 20):
        embed = disnake.Embed(colour=disnake.Colour(0).from_rgb(207, 206, 255))
        for k, v in note_chunk:
            embed.add_field(k, v, inline=False)
        embeds.append(embed)
    embeds[0].description = f"**ModNotes for {escape_markdown(redditor_param)}**\n"
    return embeds
