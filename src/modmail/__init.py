from collections import namedtuple
from datetime import datetime
from urllib.parse import urlparse


def modmail_state(conversation):
    mod_actions = conversation.mod_actions
    mod_actions.sort(key=lambda c: datetime.fromisoformat(c.date))
    ModmailState = namedtuple("ModmailState", ['highlighted', 'filtered', 'archived'])
    state = ModmailState(None, None, None)
    for a in mod_actions:
        if a.action_type_id == 0:
            state = state._replace(highlighted=datetime.fromisoformat(a.date))
        elif a.action_type_id == 1:
            state = state._replace(highlighted=None)
        elif a.action_type_id == 2:
            state = state._replace(archived=datetime.fromisoformat(a.date))
        elif a.action_type_id == 3:
            state = state._replace(archived=None)

    return state


def modmail_id_from_url(url):
    o = urlparse(url)
    id = o.path.rpartition('/')[2]
    return id

