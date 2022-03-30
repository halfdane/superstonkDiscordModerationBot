from datetime import datetime as dt

import disnake

from helper.discord_text_formatter import cut


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


async def __fetch_notes(reddit, redditor_param, before=None):
    params = {"subreddit": "Superstonk", "user": redditor_param, "limit": 100}
    if before:
        params["before"] = before
    api_path = "api/mod/notes"
    response = await reddit.get(api_path, params=params)
    notes = list(map(__transform_mod_note, reversed(response['mod_notes'])))

    if response['has_next_page']:
        end_cursor = response['end_cursor']
        notes = await __fetch_notes(reddit, redditor_param, end_cursor) + notes

    return notes


async def fetch_modnotes(reddit, redditor_param, before=None):
    notes = await __fetch_notes(reddit, redditor_param, before)

    infos = reddit.info([note["fullname"] for note in notes])
    infos = {info.fullname: info async for info in infos}

    for n in notes:
        link = ""
        if reddit_item := infos.get(n['fullname']):
            title = getattr(reddit_item, 'title', getattr(reddit_item, 'body', "")).replace("\n", "<br>")[:75]
            title = disnake.utils.escape_markdown(title)
            link = f"\n[{title}](https://www.reddit.com{reddit_item.permalink})"

        yield (f"**{n['created_at']}**",
               f"{n['mod']} {n['action']} "
               f"{n['details']} {cut(n['description'], 100)} "
               f"{link}")

