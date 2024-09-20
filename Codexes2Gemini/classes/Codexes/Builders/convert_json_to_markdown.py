import json

with open('/Users/fred/bin/nimble/stable_c2g/output/Tonkin.json', 'r') as f:
    data = json.load(f)

markdown_text = ""

for index, result in enumerate(data[0]):
    markdown_text += result[index] + "\n\n"

print(markdown_text)

with open('output/results.md', 'w') as f:
    f.write(markdown_text)
