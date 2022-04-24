def cut(text="", maxlength=None):
    if not text:
        return ''
    if not maxlength or len(text) < maxlength:
        return text
    else:
        return f"{str(text[:maxlength]).strip()}..."
