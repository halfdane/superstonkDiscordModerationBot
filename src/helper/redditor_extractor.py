import re

import disnake

USER_PAGE_MATCHER = re.compile('https://(?:www|old).reddit.com/(?:u|user)/([\w-]*)',
                               re.IGNORECASE | re.MULTILINE | re.DOTALL)

USER_REFERENCE_MATCHER = re.compile(r'u/([\w-]*)',
                                    re.IGNORECASE | re.MULTILINE | re.DOTALL)


def extract_redditor(msg: disnake.Message):
    if redditor := __find_redditor_in_embeds(msg):
        return redditor

    return __find_redditor(msg.content)


def __find_redditor_in_embeds(msg):
    for e in msg.embeds:
        for f in e.fields:
            if redditor := __find_redditor(f.value):
                return redditor

        if redditor := __find_redditor(e.description):
            return redditor


def __find_redditor(string):
    if m := USER_PAGE_MATCHER.search(string):
        return m.group(1)
    if m := USER_REFERENCE_MATCHER.search(string):
        return m.group(1)

