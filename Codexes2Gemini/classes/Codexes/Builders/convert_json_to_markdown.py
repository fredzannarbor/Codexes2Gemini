import json

with open('/Users/fred/bin/nimble/stable_c2g/processed_data/33303.json', 'r') as f:
    data = json.load(f)

markdown_text = ""

for result in data["results"]:
    markdown_text += result + "\n\n"

print(markdown_text)
