import argparse
import os
import re
import uuid
from os import path

import fitz
import pandas as pd
import spacy
# from cv2 import add
import streamlit as st
import yake
from nameparser import HumanName as hn
from numeral import int2roman

from app.utilities.gpt3complete import chatcomplete
# rom pdf2pages2text import tokenize_text_removing_new_lines_inside_sentences
from app.utilities.text2spacyner import extract_NER_from_text


# currently relies on hard-coded list of index terms

def find_named_entities(pdf_file_path, pages_limit=1200):
    entities = find_entities_as_candidate_index_terms(pdf_file_path, pages_limit)
    entities_found = str(len(entities)) + " total entities found"
    st.write(entities_found)
    left, middle, right, far_right = st.columns([3, 3, 3, 4])
    df_entities = pd.DataFrame(entities)
    df_entities.columns = ["text", "label_", "explanation"]
    # st.write(df_entities.describe())
    left.markdown("""*Entities by label_ type*""")
    left.write(df_entities["label_"].value_counts())
    df_entities.to_csv("output/entities.csv")

    # select rows with label_ == 'PERSON'
    df_entities_person = df_entities[df_entities["label_"] == "PERSON"]
    # get unique values from text column

    persons_list = df_entities_person["text"].unique()
    print(type(persons_list))

    persons = "\n".join(persons_list)
    return


def create_keyword_list_yake(filename, output_dir):
    text = ""
    word_count = 100000  # reasonable default
    number_of_pages = 300  # reasonable default
    index_entries_per_printed_index_page = 50  # landscape 11 x 8.5
    index_pages_per_text_page_divisor = 50  # reasonable default, 1/50th of pages
    doc = fitz.open(filename)  #
    print(f"Pages in document {filename}: {doc.page_count}")

    try:
        print("successfully opened pdf in create_yake", pdf_file_path)

    except Exception as e:
        print("error opening pdf", e)
    try:
        # print(doc.page_count)
        for page in doc:
            # print(page.get_text())
            text += page.get_text()
        # length of doc in pages
        number_of_pages = len(doc)

        print("successfully extracted text to single file")
        word_list = text.split()  #
        word_count = len(word_list)
        print(f"found {word_count} words in {number_of_pages} pages")
    except Exception as e:
        print("error in extracting text to single file", e)

    # MIT Press Indexing Instructions for Authors
    # https://mitpress.mit.edu/sites/default/files/quicklinks/2017-08/indexing_instructions_for_authors_0.pdf
    # p.3  says between 1/50 and 1/20 index pages per text page

    if index_pages_per_text_page_divisor == 0:
        print("Error: index_pages_per_text_page_divisor cannot be zero.")
    else:
        target_number_of_pages = number_of_pages / index_pages_per_text_page_divisor

        target_number_of_index_entries = round(
            (target_number_of_pages * index_entries_per_printed_index_page)
        )
        print(f"Target number of pages: {target_number_of_pages}")

        print(f"Target number of index entries: {target_number_of_index_entries}")

    language = "en"
    max_ngram_size = 3
    deduplication_thresold = 0.9
    deduplication_algo = "seqm"
    windowSize = 1
    numOfKeywords = target_number_of_index_entries
    keyword_list = []
    print("creating keyword extractor")
    custom_kw_extractor = yake.KeywordExtractor(
        lan=language,
        n=max_ngram_size,
        dedupLim=deduplication_thresold,
        dedupFunc=deduplication_algo,
        windowsSize=windowSize,
        top=numOfKeywords,
        features=None,
    )
    print("extracting keywords")
    keywords = custom_kw_extractor.extract_keywords(text)
    for count, kw in enumerate(keywords):
        print(kw)
        if count % 100 == 0:
            print("created ", count, "keywords")
        keyword_list.append(kw)
    # save keyword list of tuples to file as strings
    with open(output_dir + "/" + "keyword_list.txt", "w") as f:
        # each kw on one line
        for item in keyword_list:
            kw = item[0]
            print(kw)
            f.write("%s\n" % kw)
    # print(keyword_list)
    # sleep(5)
    return keyword_list


def find_new_mwes_by_regex_rules(filename, lookaheadlimit):
    print(type(lookaheadlimit))
    lookaheadlimit = int(lookaheadlimit)
    recommended_mwes_untokenized = (
        []
    )  # list of string multiple word index phrases: ["AKAGI MARU","air superiority"]
    count = 0
    print(filename)
    doc = fitz.open(filename)  #
    print(doc.page_count)
    try:
        print("successfully opened pdf in mwe", pdf_file_path)

        text = ""
        # rules = ["[A-Z]* MARU", "(USS [A-Z]+\s?\\b [A-Z]+)", "(USS [A-Z]{2,})", "(HMS [A-Z]+\s?\\b [A-Z]+)",
        #  "(HMS [A-Z]{2,})"]  # type: ignore
        rules = ["(space [A-Z]+\s?\\b [A-Z]+)", "(space [A-Z]{2,})", "(space [A-Z]{3,})"]  # type: ignore
        # rules = ["[A-Z]* MARU", "(USS [A-Z]+\s?\\b [A-Z]+)"]
        print("hardcoded regexes to find recommended multiword expressions in text")
        print(rules)

        for count, page in enumerate(doc, 1):
            # print("page", page)
            text = page.get_text()
            # print("converting page", count, "to text")
            # print(text)
            for rule in rules:
                # print(rule)
                result = re.compile(rule).findall(text)
                # print('result for searching page', count, 'for rule', rule, result)
                if result:
                    # get unique items from result list
                    for item in result:
                        if item not in recommended_mwes_untokenized:
                            recommended_mwes_untokenized.append(item)

            if count == lookaheadlimit:
                break
        print("completed regex-based search for multiword expressions")
    except Exception as e:
        print("error in find_new_mwes_by_regex_rule", e)

    # save lookahead terms to file
    with open(output_dir + "/" + "recommended_mwes_untokenized.txt", "w") as f:
        for item in recommended_mwes_untokenized:
            f.write("%s\n" % item)

    return recommended_mwes_untokenized


def identify_mwe_terms(pdf_file_path=None, mwe_terms_filepath=None):
    st.info("arrived in identify_mwe_terms")
    mwe_search_terms = []
    if mwe_terms_filepath is not None:
        if os.path.exists(mwe_terms_filepath):
            st.info("found mwe_terms_filepath")
            with open(mwe_terms_filepath, "r") as f:
                print("reading mwe terms file", mwe_terms_filepath)
                for line in f:
                    mwe_search_terms.append(line.strip())
                # print('mwe terms specific to this book are', mwe_search_terms)
            st.write("mwe terms specific to this book are", mwe_search_terms)
            return mwe_search_terms
        else:
            print("no prepared mre_terms file, building list")

            mwe_search_terms = find_new_mwes_by_regex_rules(
                pdf_file_path, lookaheadlimit=10
            )
            print("mwe terms found by regex search are", mwe_search_terms)
    return mwe_search_terms


def find_entities_as_candidate_index_terms(filename, pages_limit=1200):
    # print(type(lookaheadlimit))

    entities = (
        []
    )  # list of string multiple word index phrases: ["AKAGI MARU","air superiority"]
    count = 0
    print(filename)

    try:
        doc = fitz.open(filename)  #
        print(doc.page_count)
        message = "opened " + pdf_file_path + \
                  " successfully"
        print(message)
        # st.info(message)
    except Exception as e:
        print("error opening pdf", e)

    for count, page in enumerate(doc, 1):
        text = page.get_text()
        result = extract_NER_from_text(text)
        if result:

            for item in result:
                if item.text not in entities:
                    explanation = str(spacy.explain(item.label_))
                    appendthis = {
                        "text": item.text,
                        "label": item.label_,
                        "explanation": explanation,
                    }
                    entities.append(appendthis)
                else:
                    pass
        if count == pages_limit:
            # st.info("breaking")
            break
    df_entities = pd.DataFrame(entities)
    df_entities.columns = ["text", "label_", "explanation"]
    df_entities.to_csv("output/entitiesinfx.csv")
    df_entities_person = df_entities[df_entities["label_"] == "PERSON"]
    persons_list = df_entities_person["text"].unique().tolist().sort()
    new_persons_list = []
    print(persons_list)
    if persons_list:
        for person in persons_list:
            search_list_for_person = expand_person_to_search_term_list(person)
            # st.write("for person", person, "found search term list", search_list_for_person)
            new_persons_list.append(search_list_for_person)

    return df_entities  # , new_persons_list


def expand_person_to_search_term_list(fullname):
    name = hn(fullname)
    namedict = name.as_dict(False)
    st.write(namedict)
    lastname = name.last
    titlename = name.title + " " + name.last
    nminame = name.last + " " + name.first
    st.write(fullname, lastname, titlename, nminame)
    search_term_list = [fullname, titlename, nminame, lastname]
    return search_term_list


def search_pdf_pages_with_list_of_search_synonyms(pdf_file_path, search_terms_list, searchpageslimit):
    index_term_occurrence_dict = {}
    converted_page_and_text_list = []
    with fitz.open(pdf_file_path) as doc:  # type: ignore

        for count, page in enumerate(doc, 1):

            if count % 50 == 0:
                infomessage = (
                        "processing page " + str(count) + " of " + str(doc.page_count)
                )
                print(infomessage)
            text = page.get_text()
            page_text_pair = {"page": count, "text": text}
            converted_page_and_text_list.append(
                page_text_pair)  # save the converted page/text pairs for future reference

            # tokenizer = MWETokenizer()
            # mwetext = tokenizer.tokenize(text.split())
            # displayinfo = "tokenized text is " + str(mwetext)

            addentry = []
            for term in search_terms_list:
                # list_status = str(list[0])
                # print('processing list of search synonyms beginning with index entry ' + list_status)
                # make search case-insensitive
                if str(term).lower() in text.lower():  # mwetext

                    termfound = 'search term ' + term + ' found in text on page ' + str(count)
                    if term not in index_term_occurrence_dict:
                        addpage = [count]
                        addentry = {term: addpage}
                        index_term_occurrence_dict.update(addentry)
                    else:
                        current_pages_in_index_entry_root = index_term_occurrence_dict[term]
                        current_pages_in_index_entry_root.append(count)
                else:
                    pass

            if count == searchpageslimit:
                print("search pages limit reached")
                break
        print('search complete, cleaning up index term occurrence dict')
    index_term_occurrence_dict_clean = {}
    for key, value in index_term_occurrence_dict.items():
        index_term_occurrence_dict_clean[key.replace("_", " ")] = value
    print('reach end of search_pdf_pages_with_list_of_search_synonyms')
    return index_term_occurrence_dict_clean, converted_page_and_text_list


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
                print(infomessage)
            text = page.get_text()
            page_text_pair = {"page": count, "text": text}
            converted_page_and_text_list.append(
                page_text_pair)  # save the converted page/text pairs for future reference
            suggested_index_entries_cumulative = []
            index_entries_this_page = chatcomplete("FindIndexEntries", text, model)
            index_entries_list.append(index_entries_this_page)
            index_entry_pairs = {"page": count, "index_entries": index_entries_this_page}

            print()
            converted_page_and_index_entries.append(index_entry_pairs)

            if count == searchpageslimit:
                print("search pages limit reached")
                break
        print('search complete, cleaning up index term occurrence dict')
    return converted_page_and_index_entries, index_entries_list


def indexresults2indexentries(index_dict_results):
    terms2entries = {}
    terms2entries = {
        "terms": ["Nimitz", "Chester Nimitz", "Admiral Chester Nimitz"],
        "entries": "Nimitz, Admiral Chester",
    }
    return


def process_index_dict_results(
        index_dict, output_dir, front_matter_last_page, unnumbered_front_matter_pages_list=[0, 1, 3],
        do_not_index_these_pages_list=[0, 1, 2, 3]
):
    pages = 0

    # save index_dict to properly formatted text
    # note first step is to convert from logical page numbers in PDF
    # to physical page numbers as they would be printed in the book
    # this is the *only* output from this program that has printed book style numbering

    for key, value in index_dict.items():
        skip_these_pages = unnumbered_front_matter_pages_list + do_not_index_these_pages_list
        for i, page in enumerate(value):
            if int(page) <= int(front_matter_last_page):
                if page in skip_these_pages:
                    value[i] = None
                else:
                    value[i] = int2roman(page, only_ascii=True).lower()
            else:
                value[i] = int(page) - int(front_matter_last_page)
            # print(value[i])

        index_dict[key] = value

    with open(path.join(output_dir, "index_dict_physical_page_numbers.txt"), "w") as f:
        for key, value in sorted(index_dict.items()):
            pages = ", ".join(str(x) for x in value)
            f.write(key + "\t" + str(pages) + "\n")

    infomessage = "successfully indexed PDF document " + "after converting digital to printed page numbering " + " and saved to output directory " + str(
        output_dir)
    print(infomessage)
    return index_dict  # , pages


def extract_unique_terms(input_strings):
    all_terms = []

    # Extract terms using regex
    for string in input_strings:
        terms = re.findall(r'"([^"]+)"', string)
        all_terms.extend(terms)

    # Convert to set to ensure uniqueness and then back to list
    unique_terms = list(set(all_terms))
    # sort the list alphabetically
    unique_terms.sort()
    return unique_terms


def get_rendered_pages(data_list):
    import re
    from itertools import groupby
    from operator import itemgetter

    # Extract unique quoted items from the values
    unique_items = set()
    for entry in data_list:
        items = re.findall(r'\"(.*?)\"', entry['index_entries'])
        unique_items.update(items)

    # For each unique quoted item, list the pages on which it appears
    item_pages = {}
    for item in unique_items:
        pages = []
        for entry in data_list:
            if item in entry['index_entries']:
                pages.append(entry['page'])
        item_pages[item] = sorted(pages)

    # Render the pages such that if 3 or more adjacent pages are provided, they are displayed as a range
    def render_pages(pages):
        if not pages:
            return []

        # Helper function to get consecutive groups
        def get_consecutive_groups(lst):
            ranges = []
            for k, g in groupby(enumerate(lst), lambda ix: ix[0] - ix[1]):
                group = list(map(itemgetter(1), g))
                ranges.append((group[0], group[-1]))
            return ranges

        ranges = get_consecutive_groups(pages)
        rendered = []
        for start, end in ranges:
            if end - start >= 2:
                rendered.append(f"{start}-{end}")
            elif start == end:
                rendered.append(str(start))
            else:
                rendered.extend([str(start), str(end)])

        return rendered

    # Render the pages for each unique quoted item
    rendered_item_pages = {}
    for item, pages in item_pages.items():
        rendered_item_pages[item] = render_pages(pages)

    # Sort the items alphabetically and render the page numbers without brackets and quotes
    sorted_rendered_item_pages = {k.strip('\''): ", ".join(v) for k, v in
                                  sorted(rendered_item_pages.items(), key=lambda x: x[0].lower())}
    # render the dict as a string with each item on a new line and no quotes
    sorted_rendered_item_pages_string = ""
    for key, value in sorted_rendered_item_pages.items():
        sorted_rendered_item_pages_string += key + "\t" + value + "\n"

    return sorted_rendered_item_pages_string


if __name__ == "__main__":

    argparser = argparse.ArgumentParser("process pdf pages for an index")
    argparser.add_argument(
        "--pdf_file_path",
        help="path to pdf file",
        default="/Users/fred/bin/nimble/bookpublishergpt/app/data/test.pdf",
    )
    argparser.add_argument("-i", "--input", help="path to input file",
                           default="/Users/fred/bin/nimble/bookpublishergpt/app/data/test.pdf")
    argparser.add_argument(
        "--output_dir", help="path to output directory", default="output"
    )
    argparser.add_argument("--lookaheadlimit", help="limit", default=1000)
    argparser.add_argument("--searchpageslimit", "-p", help="searchpageslimit", default=30, type=int, required=False)
    argparser.add_argument(
        "--index_term_file_path",
        help="path to index term file",
        default="/Users/fred/bin/nimble/bookpublishergpt/app/data/book-specific-index-terms.txt",
    )
    argparser.add_argument(
        "--front_matter_last_page", "-P", help="path to index term file", default=12
    )
    argparser.add_argument(
        "--unnumbered_front_matter_pages",
        help="list of unnumbered pages in front matter",
        default=[2],
    )
    argparser.add_argument(
        "--mwe_terms_filepath",
        help="path to book-specific multiple word encodings file",
        default="/Users/fred/bin/nimble/bookpublishergpt/app/data/none.txt",
    )
    argparser.add_argument(
        "--rule_file_path",
        help="path to rule file",
        default="/Users/fred/bin/nimble/bookpublishergpt/app/data/rules.json",
    )
    argparser.add_argument("--final_search_terms", "-F", help="path to text file of final search terms", default=None)
    argparser.add_argument('--book_specific_search_terms', help='list of book specific search terms', default="")
    argparser.add_argument('--model', help='path to gpt3 model', default="gpt-3.5-turbo")
    args = argparser.parse_args()

    job_id = str(uuid.uuid4())[0:8]

    pdf_file_path = args.input  # pdf_file_path
    mwe_terms_filepath = args.mwe_terms_filepath
    output_dir = args.output_dir
    output_dir = path.join(output_dir, job_id)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    else:
        print("output directory already exists")

    # max number of pages in target PDF to process
    lookaheadlimit = args.lookaheadlimit
    searchpageslimit = args.searchpageslimit
    model = args.model

    print(f"lookaheadlimit is {lookaheadlimit}")
    print(f"searchpageslimit is {searchpageslimit}")

    index_term_file_path = args.index_term_file_path

    # last roman numbered front matter page, used for offsetting page values
    front_matter_last_page = args.front_matter_last_page

    # certain pages in front matter are always unnumbered and should not be included, this is a list of them
    unnumbered_front_matter_pages = args.unnumbered_front_matter_pages
    final_search_terms = args.final_search_terms
    #

    page_by_page_index, index_terms_list = pdf2pages2text2llmindexer(pdf_file_path, searchpageslimit, model)
    page_by_page_index_df = pd.DataFrame(page_by_page_index)
    print(page_by_page_index_df.shape)
    page_by_page_index_df.to_json(path.join(output_dir, "page_by_page_index.json"))
    unique_terms = extract_unique_terms(index_terms_list)
    unique_terms.sort()
    with open(path.join(output_dir, "unique_terms.txt"), "w") as f:
        for item in unique_terms:
            f.write("%s\n" % item)
    print(page_by_page_index)
    grouped_page_references = get_rendered_pages(page_by_page_index)
    # Convert the output of sorted_rendered_item_pages to a formatted string

    with open(path.join(output_dir, "grouped_page_references.json"), "w") as f:
        f.write(str(grouped_page_references))
    print(grouped_page_references)
    exit()

    # identify keywords that are candidates for indexing
    unsupervised_keyword_list = create_keyword_list_yake(pdf_file_path, output_dir)
    print(f"found {len(unsupervised_keyword_list)} unsupervised keywords")
    keywords = [x[0] for x in unsupervised_keyword_list]
    # write list of tuples to file with one item per line

    try:
        with open(path.join(output_dir, "unsupervised_keyword_list.txt"), "w") as f:
            for item in unsupervised_keyword_list:
                f.write(item[0] + "\t" + str(item[1]) + "\n")
                # exit()
    except Exception as e:
        print("error writing unsupervised keyword list to file", e)
        exit()

    # identify multi word expressions in the text
    mwe_search_terms = []
    if os.path.exists(mwe_terms_filepath):
        with open(mwe_terms_filepath, "r") as f:
            print("reading mwe terms file", mwe_terms_filepath)

            for line in f:
                try:
                    print(line.strip())
                    if line.strip() != "":
                        mwe_search_terms.append(line.strip())
                except Exception as e:
                    print("error reading line", line, e)
    else:
        print("no prepared mre_terms file, building list")
        mwe_search_terms = find_new_mwes_by_regex_rules(pdf_file_path, lookaheadlimit)
        print("mwe terms found by regex search are", mwe_search_terms)
    with open(path.join(output_dir, "mwe_search_terms.txt"), "w") as f:
        for item in mwe_search_terms:
            f.write("%s" % item)

    # identify named entities in the text
    entities = []
    try:
        entities_df = find_entities_as_candidate_index_terms(pdf_file_path, lookaheadlimit)
        # drop duplicate rows
        entities_df.drop_duplicates(inplace=True)

        # entities_df.to_csv(path.join(output_dir, "entities1.csv"))
        # print(entities_df.columns)
        selected_rows = entities_df[entities_df['label_'].isin(["PERSON", "PRODUCT", "ORG", "LOC", "EVENT", "FAC"])]
        print(selected_rows.sample(10))
        selected_rows.to_csv(path.join(output_dir, "entities2.csv"))
    except Exception as e:
        print("Exception while finding entities: " + str(e))

    # get all unique values of 'text' where label_ == PRODUCT
    products = entities_df[entities_df['label_'] == "PRODUCT"]['text'].unique().tolist()
    facilities = entities_df[entities_df['label_'] == "FAC"]['text'].unique().tolist()

    # union of unsupervised keywords, mwe terms and named entities
    # gprint("keywords", keywords)

    unified_search_terms = keywords + products + mwe_search_terms
    print(len(unified_search_terms))
    print("unified_search_terms", unified_search_terms)
    # save unified search terms to file, then edit
    with open(path.join(output_dir, "unified_search_terms.txt"), "w") as f:
        for item in unified_search_terms:
            f.write("%s\n" % item)

    if final_search_terms is not None:
        unified_search_terms = []
        with open(final_search_terms, "r") as f:
            for line in f:
                unified_search_terms.append(line.strip())
    else:
        final_search_terms = unified_search_terms

    page_search_results = search_pdf_pages_with_list_of_search_synonyms(
        pdf_file_path, final_search_terms, searchpageslimit
    )
    index_dict = page_search_results[0]
    index_list_of_pages = page_search_results[1]
    index_list_of_pages_df = pd.DataFrame(index_list_of_pages)
    index_list_of_pages_df.to_csv(path.join(output_dir, "index_list_of_pages.csv"))
    index_list_of_pages_df.to_json(path.join(output_dir, "index_list_of_pages.json"))
    print(index_list_of_pages_df.head())

    try:
        results = process_index_dict_results(index_dict, output_dir, front_matter_last_page)
    except Exception as e:
        print("Exception in processing index dict: " + str(e))

    with open(path.join(output_dir, "index_dict_results.txt"), "w") as f:
        for key, value in sorted(results.items()):
            pages = ", ".join(str(x) for x in value)
            f.write(key + "\t" + str(pages) + "\n")
