import pandas as pd
import logging
from app.utilities.pdf2pages2text import pdf_pages_to_list_of_text_strings

logging.basicConfig(filename="app.log", level=logging.DEBUG)


def pdf2text2df(filepath, page_limit, thisdoc_dir):
    text = ""
    try:
        text = pdf_pages_to_list_of_text_strings(filepath, page_limit,
                                                 thisdoc_dir=thisdoc_dir)  # text is list of strings
        text_df = pd.DataFrame(text, columns=["text"])
        text_df.to_json(thisdoc_dir + "/" + "text.json", orient="records")
        text = " ".join(text)  # text is now a string
        # text total word count
        text_word_count = len(text.split())
        with open(thisdoc_dir + "/" + "text.txt", "w") as f:
            f.write(text)
        text_extractableness = True
    except Exception as e:
        error_message = "can't extract text from PDF file: " + filepath + str(e)
        logging.error(error_message)
        text = ""
        text_df = pd.DataFrame()
        text_extractableness = False
    return text, text_df, text_extractableness
