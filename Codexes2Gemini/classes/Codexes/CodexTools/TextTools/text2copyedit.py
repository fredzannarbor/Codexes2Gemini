# performs copyediting tasks given *text* input (not docx)

import re


def findall_acronyms(text):
    acronyms = re.findall(r'\b[A-Z]+-[A-Z]+\b|\b[A-Z]+(?!-)\b', text)
    # exclude acronyms shorter than 2 letters
    acronyms = [word for word in acronyms if len(word) > 1]
    acronyms = sorted(set(acronyms))
    print(acronyms)
    return acronyms


def change_hyphens_to_endashes_in_text(text):
    text = str.decode("utf-8")
    text = re.sub(r"[^{]{1,4}(-)", "–", str).encode("utf-8")
    return text
