#  Copyright (c) 2024. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com
from app.utilities import pdf2pages2text
from classes.Codexes.Metadata.Metadatas import Metadatas
from classes.SyntheticReaders.gemini2syntheticreaders.BookAnalysisPlan import BookAnalysisPlan
from classes.SyntheticReaders.gemini2syntheticreaders.text2gemini import Text2Gemini
from app.utilities.pdf2pages2text import pdf_pages_to_list_of_text_strings
import fitz
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


text = ''.join([page.get_text("text") for page in fitz.open(pdf_file_path).pages()])
print(len(text))
t2g = Text2Gemini()
metadatas = Metadatas()
# book_plan = BookAnalysisPlan(context=text, user_keys_list=[
#     "ADEPT2-abstracts",
#     "mnemonics",
# ])
book_plan = BookAnalysisPlan(context="", user_keys_list=listokeys)
# Add prompt plans


def simple_openai():
    response = client.chat.completions.create(
        model=prompt_plan.model,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        temperature=prompt_plan.generation_config.get("temperature", 0.85),
        max_tokens=prompt_plan.generation_config.get("max_output_tokens", 3800),
        top_p=prompt_plan.generation_config.get("top_p", 1.0),
    )
    results = results.append(response.choices[0].message.content)


simple_openai()
book_plan.set_attribute("thisdoc_dir", "output/gemini")
book_plan.set_attribute("system_instructions_dict_file_path", "resources/json/gemini_prompts/gemini_system_instructions.json")
book_plan.set_attribute("list_of_system_keys", "dark baron")

print(book_plan.to_dict())
book_plan.list_of_user_keys_to_use =
for key in book_plan.list_of_user_keys_to_use:
    book_plan.add_prompt_plan(key, provider="openai", model="gpt-3.5-turbo")

results, metadatas = book_plan.execute_plans(t2g, metadatas)

print(results)

