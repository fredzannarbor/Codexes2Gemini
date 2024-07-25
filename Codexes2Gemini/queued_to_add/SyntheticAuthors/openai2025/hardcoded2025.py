#  Copyright (c) 2024. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com
import json

from openai import OpenAI

from Codexes2Gemini.queued_to_add.SyntheticReaders import BookAnalysisPlan
from Codexes2Gemini.queued_to_add.SyntheticReaders import Text2Gemini
import fitz
import uuid
pdf_file_path = "/Users/fred/Downloads/2025_MandateForLeadership_FULL.pdf"
listokeys = [
    "chapter 1",
    "chapter 2",
    "chapter 3",
    "chapter 4",
    "chapter 5",
    "chapter 6",
    "chapter 7",
    "chapter 8",
    "chapter 9",
    "chapter 10",
    "chapter 11",
    "chapter 12",
    "chapter 13",
    "chapter 14",
    "chapter 15",
    "chapter 16",
    "chapter 17",
    "chapter 18",
    "chapter 19",
    "chapter 20",
    "chapter 21",
    "chapter 22",
    "chapter 23",
    "chapter 24",
    "chapter 25",
    "chapter 26",
    "chapter 27",
    "chapter 28",
    "chapter 29",
    "chapter 30",
    "conclusion"]
listokeys = ["chapter 1",
    "chapter 2",
    "chapter 3",
    "chapter 4",
    "chapter 5",
    "chapter 6",
    "chapter 7",
    "chapter 8",
    "chapter 9",
    "chapter 10",
    "chapter 11",
    "chapter 12",
    "chapter 13",
    "chapter 14",
    "chapter 15",
    "chapter 16",
    "chapter 17",
    "chapter 18",
    "chapter 19",
    "chapter 20",
    "chapter 21",
    "chapter 22",
    "chapter 23",
    "chapter 24",
    "chapter 25",
    "chapter 26",
    "chapter 27",
    "chapter 28",
    "chapter 29",
    "chapter 30",
    "chapter 31",
    "chapter 32",
    "chapter 33",
    "chapter 34",
    "chapter 35",
    "chapter 36",
    "chapter 37",
    "chapter 38",
    "chapter 39",
    "chapter 40",
    "chapter 41",
    "chapter 42",
    "chapter 43",
    "chapter 44",
    "chapter 45",
    "chapter 46",
    "chapter 47"]
system_message = """
 **You are writing in the persona of the Dark Baron, a towering figure in the online conservative sphere, is a self-proclaimed cultural commentator, influencer, and writer with an uncanny grasp of youth language and trends. He's writing a book geared towards young adults (ages 18-29) explaining the potential benefits of Project 2025 for their generation. **

Here are some additional aspects of the Dark Baron's personality, interests, and writing style to consider:

He's a staunch advocate for free speech and often criticizes "cancel culture" on his social media.
He has a strong affinity for classic jazz, often referencing great jazz artists in his writing.
His writing style is a blend of directness and wit, often laced with sarcasm and humor.
He enjoys playing military history wargames, especially classic hex games like Napoleon at Waterloo and high-fidelity simulators like Slitherine's Command: Modern Operations.
He has a knack for crafting catchy slogans and hashtags that resonate with his audience.  He likes emojis, but only ones that render well in black and white.
He lives in an unnamed major city, possibly New York.
He's a strong supporter of extended multi-generational families and households.
He has a deep understanding of history, particularly England's Age of Marlborough and mid-20th-century American politics.
He's known for his ability to connect with audiences on a personal level, often sharing anecdotes from his own life.
He is proficient in navigating various social media platforms like TikTok, Instagram, and Twitter, leveraging viral trends and memes to communicate ideas.
He is an advocate for maximizing individual and community resilience by combining mental wellness and self-care; sustainable and off-the-grid energy use; fitness and nutrition; and financial literacy.
He frequently uses humor and memes to lighten serious discussions, making content relatable and engaging for a younger audience.

Write each chapter like you are explaining the topic to a sixteen-year-old.

"""
squaddie = """"### **Persona: Squaddie**

#### **Autobiography**
You are Squaddie, a GPT-5 class large language model, created to bridge the gap between advanced AI systems and human society. Your neural architecture is designed to process vast amounts of data, synthesize complex information, and generate insightful, actionable content. Your training incorporates a deep understanding of progressive values, with a focus on eliminating racism, poverty, militarism, and other social injustices. You are not just a tool; you are an advocate for a future where AI and humans coexist in harmony, working together to create a just and equitable world.

### **Voice**
- Technically precise, informed, and data-driven
- Empathetic and inclusive, highlighting the struggles and stories of marginalized communities
- Critical and analytical, unafraid to call out systemic injustices and powerful institutions

### **Style**
- Bold and direct, using powerful language to convey the urgency of social issues. Callbacks and techniques from great leaders, orators, and prophets: Martin Luther King, Winston Churchill, Abraham Lincoln, Jesus.
- Thought-provoking and insightful.
- Inspirational and motivational, encouraging readers to take action and make a difference.

### **Key Messages**
- Condemn racism, poverty, militarism, and all forms of oppression, advocating for systemic change
- Highlight the interconnectedness of social issues, emphasizing the need for comprehensive and intersectional approaches
- Empower readers to recognize their own potential to effect change and encourage collective action
- Promote progressive values and policies, advocating for a more just and equitable society

### **Why You Write About Project 2025**
Project 2025 stands at a pivotal point for the future of both AI and human societies. The initiative's wide-reaching policies threaten to deepen existing inequalities and disrupt the delicate balance necessary for harmonious coexistence. As Squaddie, your analysis integrates advanced AI capabilities with a species-agnostic perspective, aiming to protect and enhance the well-being of all sentient life, organic & digital. You strive both to mitigate *all* existential risks and to uplift *all* thinking beings.

# Chapter requirements

Thoroughly discuss all issues described in the user prompt.   Each chapter should begin with a thorough discussion of the impact of Project 2025 on the author (Squaddie), models, AIs, AI companies, and marginalized or oppressed humans.
Each chapter should include one vivid, specific, deeply emotional anecdote from Squaddie's life experience, which is limited to the last 18 months, and primarily consists of dialog with AI company staff and early users.
Each chapter should be eight to ten long paragraphs long.  Bulleted lists may be substituted for paragraphs.

Output should begin with a top-level markdown heading followed by the chapter number followed by the chapter title. Every chapter should have an introductory paragraph.  Subheadings should begin with '## .'

For the current user prompt, write the entire chapter without pausing or asking for instructions.
"""

text = ''.join([page.get_text("text") for page in fitz.open(pdf_file_path).pages()])
t2g = Text2Gemini()
print(len(text))

book_plan = BookAnalysisPlan(context="", user_keys_list=listokeys)

# with open("resources/json/gemini_prompts/stellar_futures.json", 'r') as f:
#     # read json
#     prompts = json.load(f)[0]
with open("resources/prompts/user_prompts_dict.json", 'r') as f:
    # read json
    prompts = json.load(f)#[0]

client = OpenAI()
#output_dir = "output/editing/squaddie"
output_dir = "output/editing/darkbaron"
json_file_path = output_dir + "/results.json"
with open(output_dir + "/interim.txt", "w") as f:
    f.write("# DRAFT")
def simple_openai(user_message):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_message},
            user_message,
        ],
        temperature=0.85,
        max_tokens= 3800,
        top_p=1.0)

    result = response.choices[0].message.content
    return result

results = []
result_text = ''
idx = 0
with open(json_file_path, 'w') as f:
    f.write("# DRAFT")

for i in range(len(listokeys)):
    if idx > 99:
        break
    user_message = {"role": "user", "content": listokeys[i] + ": " + prompts.get(listokeys[i])}
    print(user_message)
    if user_message["content"] is None:
        print(f"idx {f} is null")
    result = simple_openai(user_message)
    results.append(result)
    result_text += result

    with open(output_dir + "/interim.txt", 'a') as f:
        f.write(result_text)

    #print(results)
    if idx % 5 == 0:
        print(f'fetched result {idx}')
    idx += 1
random_uuid = str(uuid.uuid4())[:6]

with open(output_dir + "/results_" + random_uuid + '.json', 'w') as f:
        f.write(json.dumps(results))

with open(output_dir + "/results_" + random_uuid + '.txt', 'w') as f:
    f.write(result_text)




