#  Copyright (c) 2024. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com


import glob
# Import necessary libraries for file handling and data processing
import os
import shutil
from datetime import datetime
from uuid import uuid4

import ebooklib
import pandas as pd
from bs4 import BeautifulSoup
from ebooklib import epub

import Codexes2Gemini.queued_to_add.SyntheticReaders.RatingUtilities as ru
from app.utilities.docx2text import docx2txt
from classes.Codexes.Tools.DocxCodex2Objects import DocxCodex2Objects as dx2obj
# from pages.Send_Books_to_Reader_Panels import extract_text_from_epub
from classes.Codexes.Tools.pdf2pages2df import pdf2text2df
from Codexes2Gemini.queued_to_add.SyntheticReaders.ReaderPanels import ReaderPanels

rps = ReaderPanels()
# Assuming the existence of utility functions for book sanity checks, and book evaluation
# These would need to be implemented based on specific criteria and logic
def is_book_sanity_passed(file_path, working_dir):
    """
    Perform a sanity check on the book to ensure it matches the expected format and length.
    Returns True if the book passes the sanity check, False otherwise.
    """
    if file_path.lower().endswith(".docx"):
        list_of_paras = docx2txt(file_path, working_dir)[0]
    elif file_path.lower().endswith(".pdf"):
        text_tuple = pdf2text2df(file_path, page_limit=30,
                                 thisdoc_dir="working/send2readers/working")  # ['para'].tolist()
        text = text_tuple[0]
        text_df = text_tuple[1]
        print(text_df.head())

    # convert list to text
    #text = " ".join(list_of_paras)
    # check number of words in text
    num_words = len(text.split())
    if num_words < 100:
        return False
    if num_words > 250000:
        return False
    return True


def extract_text_from_epub(file_path):
    book = epub.read_epub(file_path)
    paragraphs = []

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.content, 'html.parser')
        for p in soup.find_all('p'):
            paragraphs.append(p.get_text())
    return paragraphs

def evaluate_book(file_path, reader_or_panel):
    """
    Evaluate the book based on a specified reader or reader panel.
    Returns a dictionary of evaluation results.
    """
    # Placeholder for actual implementation

    if file_path.lower().endswith('.epub'):
        paras = extract_text_from_epub('working/' + file_path)
        paras_df = pd.DataFrame(paras, columns=['para'])
    if file_path.lower().endswith('.docx'):
        print(f"file is docx")
        paras = dx2obj().prepare4readerpanel(file_path)
        paras_df = pd.DataFrame(paras, columns=['para'])
        print(paras_df.head(5))
    if file_path.lower().endswith('.pdf'):
        paras_df = pdf2text2df(file_path, page_limit=30, thisdoc_dir="working/send2readers/working")[1]

        print(paras_df.head(5))
    panel_df = rps.get_saved_reader_panel("Test")
    print(panel_df.head(5))
    results_df = ru.rate_objects(paras_df, panel_df, ["EvaluateParasEnhance"], num_rows=99, model="gpt-3.5-turbo",
                                 object_key=object_key)

    # results_df = rate_paras(paras_df, panel_df, "EvaluateParaPointsOnly", 10)
    print(f"Completed {results_df.shape[0]} evaluations.")
    # spreadsheet(paras_df, key=(str(uuid4())[:6]))
    filename = "Reader_Panel_results_" + str(uuid4())[:6] + ".csv"
    # if results_df is not empty, then proceed
    if results_df.shape[0] > 0:
        results_df.to_json("working/send2readers/results/Reader_Panel_para_results.json", orient="records")
    return results_df


def main(ready_dir):
    # Step 0 (setup)

    # Define the path for the directories
    ready_dir = ready_dir  # "working/send2readers/ready"
    evaluated_dir = "working/send2readers/evaluated"
    results_dir = "working/send2readers/results"
    working_dir = "working/send2readers/working"
    test_dir = "working/send2readers/test"

    # Ensure necessary directories exist
    os.makedirs(ready_dir, exist_ok=True)
    os.makedirs(evaluated_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(working_dir, exist_ok=True)
    os.makedirs(test_dir, exist_ok=True)
    # Step 1: Scan for files
    book_files = glob.glob(f"{ready_dir}/*.docx") + glob.glob(f"{ready_dir}/*.epub") + glob.glob(f"{ready_dir}/*.pdf")
    print(f"Found {len(book_files)} book files")
    # Step 2: Sanity Check
    books_to_evaluate = [book for book in book_files if is_book_sanity_passed(book, working_dir)]
    print(f"Found {len(books_to_evaluate)} that passed sanity test")
    # Placeholder for initializing specified readers or reader panels
    # This would depend on the details within the Reader, Readers, and ReaderPanels classes

    readers_or_panels = ["Reader1", "ReaderPanel1"]  # Example placeholders
    readers_or_panels = [rps.get_saved_reader_panel(reader_panel_name="Test")]
    # Step 4: Evaluate each book
    evaluation_results = []

    for book in books_to_evaluate:
        for reader_or_panel in readers_or_panels:
            result = evaluate_book(book, reader_or_panel)
            evaluation_results.append({
                "book": os.path.basename(book),
                "reader_or_panel": reader_or_panel,
                **result
            })

    # Step 5: Create result dataframe
    df = pd.DataFrame(evaluation_results)

    # Step 6: Move evaluated books
    for book in books_to_evaluate:
        shutil.move(book, evaluated_dir)

    # Step 7: Save result dataframe
    uniq_name = datetime.now().strftime("%Y%m%d%H%M%S")
    results_file_path = f"{results_dir}/{uniq_name}_df.csv"
    df.to_csv(results_file_path, index=False)

    # Output path of the results file for confirmation
    print(f"Results file saved to: {results_file_path}")


if __name__ == "__main__":
    main("working/send2readers/test")
