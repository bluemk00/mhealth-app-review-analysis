import html
import re

# Zero-width joiner (U+200D) and variation selector-16 (U+FE0F) — kept as chr()
# so the source stays plain ASCII (these code points are otherwise invisible).
_ZWJ = chr(0x200D)
_VS16 = chr(0xFE0F)


def strip_emoji(text):
    """Remove emoji/pictographs and collapse whitespace. Returns None for None input."""
    if text is None:
        return None
    s = html.unescape(str(text))
    try:
        # `regex` (if installed) handles Unicode pictographs more accurately
        import regex
        s = regex.sub(r'\p{Extended_Pictographic}|' + _VS16 + '|' + _ZWJ, '', s)
    except Exception:
        # Fallback for the stdlib `re`: cover the main emoji blocks
        emoji_re = re.compile(
            "["
            "\U0001F600-\U0001F64F"   # emoticons
            "\U0001F300-\U0001F5FF"   # symbols & pictographs
            "\U0001F680-\U0001F6FF"   # transport & map
            "\U0001F700-\U0001F77F"
            "\U0001F780-\U0001F7FF"
            "\U0001F800-\U0001F8FF"
            "\U0001F900-\U0001F9FF"
            "\U0001FA00-\U0001FA6F"
            "\U0001FA70-\U0001FAFF"
            "\U00002702-\U000027B0"   # dingbats
            "\U000024C2-\U0001F251"   # enclosed
            "\U0001F1E6-\U0001F1FF"   # flags
            + _ZWJ + _VS16 +
            "]+", flags=re.UNICODE
        )
        s = emoji_re.sub('', s)
    s = re.sub(r"[\r\n]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s
