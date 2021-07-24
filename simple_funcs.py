import re

def clean(word: str) -> str:
    word = re.sub('[^+?!0-9a-zа-яё-]', '', word, flags=re.IGNORECASE)
    word = word.strip('-')
    return word