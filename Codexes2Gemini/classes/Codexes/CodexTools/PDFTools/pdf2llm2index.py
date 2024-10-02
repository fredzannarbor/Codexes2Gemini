import logging

logging.basicConfig(level=logging.ERROR, format="%(asctime)s [%(levelname)s]: %(message)s")
import argparse
import os
import uuid
from os import path
import re
from itertools import groupby
from operator import itemgetter

import fitz
import pandas as pd
# from cv2 import add
from numeral import int2roman

from app.utilities.gpt3complete import chatcomplete


# rom pdf2pages2text import tokenize_text_removing_new_lines_inside_sentences


# currently relies on hard-coded list of index terms

def pdf2pages2text2llmindexer(pdf_file_path, searchpageslimit, model):
    index_term_occurrence_dict = {}
    converted_page_and_text_list = []
    converted_page_and_index_entries = []
    index_entries_list = []
    with fitz.open(pdf_file_path) as doc:  # type: ignore

        for count, page in enumerate(doc, 1):

            if count % 50 == 0:
                infomessage = (
                        "processing page " + str(count) + " of " + str(doc.page_count)
                )
                logging.info(infomessage)
                print(infomessage)
            text = page.get_text()
            page_text_pair = {"page": count, "text": text}
            converted_page_and_text_list.append(
                page_text_pair)  # save the converted page/text pairs for future reference
            suggested_index_entries_cumulative = []
            try:
                index_entries_this_page = chatcomplete("FindIndexEntries", text, model)
            except Exception as e:
                logging.info("error in chatcomplete", str(e))
                index_entries_this_page = [str(e)]
            index_entries_list.append(index_entries_this_page)
            index_entry_pairs = {"page": count, "index_entries": index_entries_this_page}

            converted_page_and_index_entries.append(index_entry_pairs)

            if count == searchpageslimit:
                logging.info("search pages limit reached")
                break
        logging.info('search complete, cleaning up index term occurrence dict')
    return converted_page_and_index_entries, index_entries_list


def integer_to_roman(n):
    """
    Convert an integer to a Roman numeral.
    """
    val = [
        1000, 900, 500, 400,
        100, 90, 50, 40,
        10, 9, 5, 4, 1
    ]
    syms = [
        "M", "CM", "D", "CD",
        "C", "XC", "L", "XL",
        "X", "IX", "V", "IV",
        "I"
    ]
    roman_num = ''
    i = 0
    while n > 0:
        for _ in range(n // val[i]):
            roman_num += syms[i]
            n -= val[i]
        i += 1
    return roman_num


# Redefining int2roman function using the custom integer_to_roman function
def int2roman(input, only_ascii=True):
    # Convert integer to roman numeral
    return integer_to_roman(input).lower()


import json


def is_valid_json(entry):
    """Check if a string can be parsed as JSON."""
    try:
        json.loads(entry)
        return True
    except json.JSONDecodeError:
        return False


def clean_data(data):
    cleaned_data = []

    for entry in data:
        content = entry['index_entries']

        # Check for even number of double quotes
        if content.count('"') % 2 != 0:
            continue

        # Check for matching square brackets
        if content.count('[') != content.count(']'):
            continue

        # Check for JSON validity
        if not is_valid_json(content):
            continue

        cleaned_data.append(entry)

    return cleaned_data


def postprocess_index_dicts(data_list, output_dir, front_matter_last_page, unnumbered_front_matter_pages_list,
                            do_not_index_these_pages_list):
    index_dict = {}
    logging.info('postprocessing index dicts')
    logging.info(f"datalist is {data_list}")

    # Convert the list of dicts to the old index_dict structure
    for entry in data_list:
        page = entry['page']
        index_entries = eval(entry['index_entries'])  # Convert string representation of list to actual list
        for term in index_entries:
            if term not in index_dict:
                index_dict[term] = []
            index_dict[term].append(page)
    skip_these_pages = unnumbered_front_matter_pages_list + do_not_index_these_pages_list
    # skip_these_pages = [str(page) for page in skip_these_pages]
    # drop all duplicate items in skip_these_pages
    skip_these_pages = list(dict.fromkeys(skip_these_pages))
    # sort skip these pages in numerical order
    skip_these_pages.sort()
    logging.info(f"skip_these_pages is {skip_these_pages}")
    for key, value in index_dict.items():

        for i, page in enumerate(value):
            if int(page) <= int(front_matter_last_page):
                if page in skip_these_pages:
                    value[i] = None
                else:
                    value[i] = int2roman(page, only_ascii=True).lower()
            else:
                value[i] = int(page) - int(front_matter_last_page)

        index_dict[key] = value

    return index_dict


def get_rendered_pages(data_dict):
    # Sort the items alphabetically by key
    sorted_data_dict = {
        k: v for k, v in sorted(
            data_dict.items(),
            key=lambda x: x[0].lower() if not isinstance(x[0], int) else x[0]
        )
    }

    # Create a string representation with each item on a new line without None values
    sorted_rendered_item_pages_string = ""
    for key, value in sorted_data_dict.items():
        # Filter out None values from the page numbers
        pages = [str(page) for page in value if page is not None]
        if pages:  # Check if there are any valid pages left after filtering
            sorted_rendered_item_pages_string += key + "\t" + ", ".join(pages) + "\n"

    return sorted_rendered_item_pages_string


if __name__ == "__main__":

    argparser = argparse.ArgumentParser("process pdf pages for an index")

    argparser.add_argument(
        "--do_not_index_these_pages", "-DNI",
        help="list of pages to skip",
        default=[0, 1, 2, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 350, 351, 352, 353, 354, 355, 356, 357],
        type=int,
        required=False
    )

    argparser.add_argument(
        "--front_matter_last_page", "-P",
        help="path to index term file",
        default=14,
        type=int,
        required=False
    )

    argparser.add_argument(
        "-i", "--input",
        help="path to input file",
        default="/Users/fred/bin/nimble/bookpublishergpt/app/data/test.pdf"
    )

    argparser.add_argument(
        "--index_term_file_path",
        help="path to index term file",
        default="/Users/fred/bin/nimble/bookpublishergpt/app/data/book-specific-index-terms.txt"
    )

    argparser.add_argument(
        "--model", "-M",
        help="model name",
        default="gpt-3.5-turbo"
    )

    argparser.add_argument(
        "--output_dir",
        help="path to output directory",
        default="output"
    )

    argparser.add_argument(
        "--pdf_file_path",
        help="path to pdf file",
        default="/Users/fred/bin/nimble/bookpublishergpt/app/data/test.pdf"
    )

    argparser.add_argument(
        "--searchpageslimit", "-p",
        help="searchpageslimit",
        default=30,
        type=int,
        required=False
    )

    argparser.add_argument(
        "--unnumbered_front_matter_pages",
        help="list of unnumbered pages in front matter",
        default=[2],
        type=int,
        required=False
    )

    args = argparser.parse_args()
    job_id = str(uuid.uuid4())[0:8]
    pdf_file_path = args.input  # pdf_file_path
    # max number of pages in target PDF to process
    searchpageslimit = args.searchpageslimit
    model = args.model

    output_dir = args.output_dir
    output_dir = path.join(output_dir, job_id)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    else:
        logging.info("output directory already exists")

    logging.info(f"searchpageslimit is {searchpageslimit}")
    logging.info(f"model is {model}")
    logging.info(f"output_dir is {output_dir}")

    # index these pages using llm

    page_by_page_index, index_terms_list = pdf2pages2text2llmindexer(pdf_file_path, searchpageslimit, model)
    # logging.info(page_by_page_index)

    # postprocess the indexed pages to reflect printed page
    # FMLP: last front matter page, convert front matter to roman numerals
    # UNNUMBERED: certain pages in front matter are always unnumbered and should not be indexed
    # DO NOT INDEX: some pages may discretionally be left out of the index, for example marketing, acknowledgements, etc.

    front_matter_last_page = args.front_matter_last_page
    unnumbered_front_matter_pages = args.unnumbered_front_matter_pages
    do_not_index_these_pages = args.do_not_index_these_pages

    page_by_page_index2 = clean_data(page_by_page_index)
    try:
        processed_page_by_page_dict = postprocess_index_dicts(page_by_page_index2, output_dir, front_matter_last_page,
                                                              unnumbered_front_matter_pages, do_not_index_these_pages)
        # logging.info('--p--' * 20)
    except Exception as e:
        logging.info("error processing index dict results", str(e))
    # logging.info(processed_page_by_page_dict)
    page_by_page_index = processed_page_by_page_dict

    # render the index as printable pages
    grouped_page_references = get_rendered_pages(page_by_page_index)
    # logging.info(grouped_page_references)
    with open(path.join(output_dir, "grouped_page_references.txt"), "w") as f:
        f.write(str(grouped_page_references))
    logging.info(f"wrote grouped_page_references.txt to {output_dir}")

    # convert list of dicts to dataframe
    # page by page index = dictionary with keys = index terms, values = list of pages
    page_by_page_index_df = pd.DataFrame.from_dict(page_by_page_index, orient="index")
    # $ logging.info(page_by_page_index_df.shape)
    page_by_page_index_df.to_json(path.join(output_dir, "page_by_page_index.json"))
