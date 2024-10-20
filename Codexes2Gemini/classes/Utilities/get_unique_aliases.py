import json


def extract_unique_aliases(json_file):
    """Extracts unique aliases from a JSON file and writes them to a text file.

    Args:
      json_file: Path to the JSON file.
    """

    with open(json_file, 'r') as f:
        data = json.load(f)

    unique_aliases = set()  # Use a set to store unique aliases
    for item in data:
        for alias in item['aliases']:
            unique_aliases.add(alias)

    with open('unique_aliases.txt', 'w') as outfile:
        for alias in unique_aliases:
            outfile.write(alias + '\n')


if __name__ == '__main__':
    json_file = '/Users/fred/bin/nimble/Codexes2Gemini/resources/json/github_emoji_names'
    extract_unique_aliases(json_file)
