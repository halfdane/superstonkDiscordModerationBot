from disnake.utils import escape_markdown


def permalink(item):
    return f"https://new.reddit.com{getattr(item, 'permalink', item)}"

def user_page(redditor):
    return "https://new.reddit.com/u/{redditor}"

def make_safe(maybe_string):
    string = str(maybe_string)
    clipped = str(string[:100])
    clipped += '...' if len(string) > 100 else ''
    return escape_markdown(clipped).replace('\n', ' ')
