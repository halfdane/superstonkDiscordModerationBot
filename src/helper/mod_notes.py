from datetime import datetime as dt

import disnake


def __transform_mod_note(n):
    note = {
        "id": n['id'],
        "created_at": dt.fromtimestamp(int(n['created_at'])).strftime('%Y-%m-%d %H:%M:%S'),
        "mod": n['operator'],
        "user": n['user'],
        "action": n['mod_action_data']['action'] or n['user_note_data']['label'] or "",
        "details": n['mod_action_data']['details'] or "",
        "fullname": n['mod_action_data']['reddit_id'] or n['user_note_data']['reddit_id'] or "",
        "description": n['mod_action_data']['description'] or n['user_note_data']['note'] or ""
    }
    return note


async def __fetch_notes(reddit, redditor_param, before=None, all=True):
    params = {"subreddit": "Superstonk", "user": redditor_param, "limit": 100}
    if before:
        params["before"] = before
    api_path = "api/mod/notes"
    response = await reddit.get(api_path, params=params)
    notes = list(map(__transform_mod_note, reversed(response['mod_notes'])))

    if response['has_next_page'] and all:
        end_cursor = response['end_cursor']
        notes = await __fetch_notes(reddit, redditor_param, end_cursor) + notes

    return notes


# possible types: BOT_BAN, PERMA_BAN, BAN, ABUSE_WARNING, SPAM_WARNING, SPAM_WATCH, SOLID_CONTRIBUTOR, HELPFUL_USER
async def __store_note(reddit, note, redditor_param, type="ABUSE_WARNING"):
    params = {"label": type, "note": note, "subreddit": "Superstonk", "user": redditor_param}
    api_path = "api/mod/notes"
    await reddit.post(api_path, params=params)


async def __delete_note(reddit, note_id, redditor_param):
    params = {"note_id": note_id, "subreddit": "Superstonk", "user": redditor_param}
    api_path = "api/mod/notes"
    await reddit.delete(api_path, params=params)


async def fetch_modnotes(reddit, redditor_param, only=None):
    notes = await __fetch_notes(reddit, redditor_param)

    if only:
        notes = [note for note in notes if note["action"] == only]

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
               f"{n['details']} {n['description'][:100]} "
               f"{link}")
