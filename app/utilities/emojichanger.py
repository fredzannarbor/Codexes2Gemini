import re


def replace_emojis(text):
    def replace_emoji(match):
        return f"\\textemoji{{{match.group()}}}"

    # This pattern matches a wider range of emojis, including the ones mentioned
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
                               u"\U0001FA00-\U0001FA6F"  # Extended-A
                               u"\U0001FA70-\U0001FAFF"  # Extended-B
                               u"\U0001F004-\U0001F0CF"  # Additional emoticons
                               u"\U0001F170-\U0001F251"  # Additional transport and map symbols
                               "]+", flags=re.UNICODE)

    # Replace emojis with \textemoji{emoji}
    return emoji_pattern.sub(replace_emoji, text)


# Read the input file
with open('results_c81ef2.txt', 'r', encoding='utf-8') as file:
    content = file.read()

# Replace emojis
modified_content = replace_emojis(content)

# Write the modified content to a new file
with open('results_c81ef2_modified.txt', 'w', encoding='utf-8') as file:
    file.write(modified_content)

print("Emoji replacement complete. Modified content saved to 'results_c81ef2_modified.txt'.")