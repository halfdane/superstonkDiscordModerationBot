import re


def strikethrough(text, maxlength=None):
    return __surround(text, "~~", maxlength=maxlength)


def un_strikethrough(text):
    return __un_surround(text, "~~")


def e(text, maxlength=None):
    return __surround(text, "*", maxlength=maxlength)


def un_e(text):
    return __un_surround(text, "*")


def b(text, maxlength=None):
    return __surround(text, "**", maxlength=maxlength)


def un_b(text):
    return __un_surround(text, "**")


def underscore(text, maxlength=None):
    return __surround(text, "__", maxlength=maxlength)


def un_underscore(text):
    return __un_surround(text, "__")


def spoiler(text, maxlength=None):
    return __surround(text, "||", maxlength=maxlength)


def un_spoiler(text):
    return __un_surround(text, "||")


def blockquote(text, maxlength=None):
    return __surround(text, ">>> ", " \n\n\n", maxlength=maxlength)


def un_blockquote(text):
    return __un_surround(text, ">>> ", " \n\n\n")


def inline_code(text, maxlength=None):
    return __surround(text, "`", maxlength=maxlength)


def un_inline_code(text):
    return __un_surround(text, "`")


def code(text, maxlength=None):
    return __surround(text, "```", maxlength=maxlength)


def un_code(text):
    return __un_surround(text, "```")


def red(text, maxlength=None):
    return code(f"diff\n-{text}", maxlength=maxlength)


def green(text, maxlength=None):
    return code(f"diff\n+{text}", maxlength=maxlength)


def orange(text, maxlength=None):
    return code(f"css\n[{text}]", maxlength=maxlength)


def cyan(text, maxlength=None):
    return code(f'json\n"{text}"', maxlength=maxlength)


def blue(text, maxlength=None):
    return code(f"ini\n[{text}]", maxlength=maxlength)


def yellow(text, maxlength=None):
    return code(f"fix\n{text}", maxlength=maxlength)


def link(url, text=None, maxlength=None):
    if not text:
        text = url
    return f"[{cut(text, maxlength=maxlength)}]({url})"


def unlink(text):
    match = re.match(r'\[(.*)\]\((.*)\)', text)
    return match[1], match[2]


def cut(text="", maxlength=None):
    if not text:
        return ''
    if not maxlength or len(text) < maxlength:
        return text
    else:
        return f"{str(text[:maxlength]).strip()}..."


def __surround(text, surroundwith, endwith=None, maxlength=None):
    if not endwith:
        endwith = surroundwith
    return f"{surroundwith}{cut(text, maxlength=maxlength)}{endwith}"


def __un_surround(text, surroundwith, endwith=None):
    if not endwith:
        endwith = surroundwith
    if str(text).startswith(surroundwith) and str(text).endswith(endwith):
        return str(text)[len(surroundwith):-len(endwith)]
    else:
        return text

