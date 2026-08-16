import re
import unicodedata


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = unicodedata.normalize("NFKC", text)

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    text = re.sub(r"[ \t]+", " ", text)

    text = re.sub(r"\n[ \t]+", "\n", text)

    text = re.sub(r"\n{3,}", "\n\n", text)

    text = re.sub(r"[^\S\n]+", " ", text)

    return text.strip()
