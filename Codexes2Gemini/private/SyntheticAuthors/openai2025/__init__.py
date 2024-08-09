#  Copyright (c) 2024. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com
from Codexes2Gemini.private.SyntheticReaders import BookAnalysisPlan
from Codexes2Gemini.private.SyntheticReaders import Text2Gemini
from app.utilities.pdf2pages2text import pdf_pages_to_list_of_text_strings
pdf = "Users/fred/Downloads/2025_MandateForLeadership_FULL.pdf"
text = pdf_pages_to_list_of_text_strings(pdf, 1000, "output/gemini")
t2g = Text2Gemini()
book_plan = BookAnalysisPlan(context=text, user_keys_list=[
    "ADEPT2-abstracts",
    "mnemonics",
])

book_plan.set_attribute("thisdoc_dir", thisdoc_dir)

# Add prompt plans
for key in book_plan.list_of_user_keys_to_use:
    book_plan.add_prompt_plan([key])

results = book_plan.execute_plans(t2g, metadatas)

print(results)