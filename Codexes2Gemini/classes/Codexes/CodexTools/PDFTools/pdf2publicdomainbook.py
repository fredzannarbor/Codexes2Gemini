import argparse
import csv
import json
import logging
import os
import shutil
import statistics
import subprocess
from collections import OrderedDict

import pandas as pd
from app.utilities.metadatas2manifest import metadatas2df, metadatas2bookjson, metadatas2internationaledition
from isbnlib import desc
from nltk.tokenize import sent_tokenize
from transformers.models.gpt2 import GPT2TokenizerFast

from app.utilities.OLD_metadatas_df2distributor_reqts import book_metadata_json2distributor_format_targets, \
    create_LSI_ACS_spreadsheet
from app.utilities.RecursiveSummarizer.recursively_summarize import \
    loop_until_floor_and_ceiling_satisfied as recursively_summarize
from app.utilities.pdf2pages2text import pdf_pages_to_list_of_text_strings
from app.utilities.pdfmetadata2all import (
    pdfmetadata2dict,
    pdfpagedimensions2list,
    analyze_page_dimensions,
    pdfgetlistoftoc
)
from app.utilities.text2foreword import create_foreword_in_one_step
from app.utilities.text2metadata_using_openai import (
    create_title_metadata_using_openai, get_token_counts_for_presets, common_presets_for_metadata
)
from app.utilities.text2spacyextractivesummary import spacy_summarize
from app.utilities.text2unsupervised_keyword_extraction import create_keyword_list_yake
from app.utilities.texts2match import texts2exactmatch, texts2fuzzymatch, texts2caseinsensitivematch
from app.utilities.utilities import (
    create_safe_dir_from_file_path,
    detect_languages
)


def process_pdf(
        filename,
        output_dir,
        limit,
        list2string,
        filecount,
        timestamped_filename,
        payservices,
        config,
        run_recursively, run_page_by_page, ai_metadata, create_interior_postscript, mode="assess"
):
    # open next pdf and create directory to house working materials
    thisdoc_dir = create_safe_dir_from_file_path(filename, output_dir)[0]
    destination = thisdoc_dir + '/' + os.path.basename(filename)
    print(filename, destination)
    # exit()
    shutil.copy2(filename, destination)
    text_word_count = 0
    kdp_metadata_df = pd.DataFrame()
    # create ordered dict metadatas
    metadatas = OrderedDict()
    #    #
    df_row = pd.DataFrame()
    text_extractableness, metadata_extractableness = False, False
    (
        pagesizeanalysis,
        text,
        keywords,
        keywords_text,
        keywords_text_list,
        extractive_summary,
        extractive_summary2df,
        extractive_synopsis,
        deduped_keywords,
    ) = ("", "", [], "", [], [], " ", "", [])
    deduped_keywords_with_scores = {}
    exactmatch, fuzzymatch, caseinsensitivematch = False, False, False
    pagesize_analysis_results = []
    synopsisplus, submit_synopsis = "", ""

    # creating safe filename for each document and corresponding directory
    metadata_csv_file_path = thisdoc_dir + "/" + "metadata.csv"

    try:
        text = pdf_pages_to_list_of_text_strings(filename, limit, output_dir="output")  # text is list of strings
        text_df = pd.DataFrame(text)
        text_df.to_json(thisdoc_dir + "/" + "text.json", orient="records")

        text = " ".join(text)  # text is now a stringls
        # text total word count
        text_word_count = len(text.split())
        with open(thisdoc_dir + "/" + "text.txt", "w") as f:
            f.write(text)
        logging.getLogger("models.gpt2.GPT2TokenizerFast").setLevel(logging.ERROR)
        tokens = GPT2TokenizerFast.from_pretrained("gpt2").encode(text)
        print(len(tokens))
        sentences = len(sent_tokenize(text))
        summary_target_token_length = 50
        percentage = int(summary_target_token_length) / len(tokens)
        # 3000 is 4096 max tokens for davinci - 1000 tokens wiggle room for prompt

        print(
            f"starting extractive summary, target token length is {summary_target_token_length}, number of sentences is {sentences}, percentage is {percentage}"
        )

        extractive_summary = spacy_summarize(text, percentage, output_dir=thisdoc_dir)

        print("starting synopsis", "...")
        extractive_synopsis = spacy_summarize(
            extractive_summary,
            percentage / 10,
            output_dir=thisdoc_dir,
            output_filename="synopsis.txt",
        )
        submit_synopsis = extractive_synopsis
        # count tokens using huggingface tokenizer

        metadatas["languages"] = detect_languages(text)

        print("starting keywords")
        keywords = create_keyword_list_yake(
            text, calculate_number_of_target_keywords=True
        )
        pd.DataFrame(keywords_text_list).to_csv(
            thisdoc_dir + "/" + "keywords.csv", index=False
        )
        keywords_text_list = keywords[1]
        deduped_keywords = keywords[2]
        deduped_keywords_with_scores = keywords[3]
        # print(deduped_keywords_with_scores)
        deduped_keywords_df = pd.DataFrame(deduped_keywords_with_scores, index=[0])
        deduped_keywords_df.to_json(thisdoc_dir + "/" + "deduped_keywords.json")

        text_extractableness = True

    except Exception as e:
        print("error in summary & keywords block: " + str(e))
        text_extractableness = False

    else:
        print("not using pay services   ")

    try:
        metadatas = pdfmetadata2dict(filename)
        metadatas["author_supplied_keywords"] = keywords
        metadatas["subtitle"] = ""
        metadatas["imprint"] = "Nimble Books LLC"
        metadatas["publisher"] = "Nimble Books LLC"
        metadatas['toc'] = pdfgetlistoftoc(filename)
        pagedimensionslist = pdfpagedimensions2list(filename)
        pagesize_analysis_results = analyze_page_dimensions(pagedimensionslist)
        print(pagedimensionslist)
        pagesizemedianheight = statistics.median([x[3] for x in pagedimensionslist]) / 72
        pagesizemedianwidth = statistics.median([x[2] for x in pagedimensionslist]) / 72
        if pagesizemedianheight % 1 == 0:
            pass
        else:
            pagesizemedianheight = round(pagesizemedianheight, 3)
        if pagesizemedianwidth % 1 == 0:
            pass
        else:
            pagesizemedianwidth = round(pagesizemedianwidth, 3)
        print(pagesizemedianwidth, pagesizemedianheight)

        print("pagesize_analysis_results", pagesize_analysis_results)

        metadatas["pageresizingneeded"] = pagesize_analysis_results[2]
        metadatas["pageheights"] = pagesizemedianheight
        metadatas["pagewidths"] = pagesizemedianwidth
        metadata_extractableness = True

    except Exception as e:
        print("can't extract metadata from PDF file: " + filename, e)
        metadata_extractableness = False

        if mode == "produce":
            specs_df = pd.read_csv('working/production_specs.csv')
            working_doc_row = specs_df[specs_df['filename'] == filename]
            metadatas['title'] = working_doc_row['title'].values[0]
            metadatas['subtitle'] = working_doc_row['subtitle'].values[0]
            metadatas['author'] = working_doc_row['author'].values[0]
            metadatas['ISBN'] = working_doc_row['ISBN'].values[0]
            metadatas['publisher-supplied keywords'] = working_doc_row['publisher-supplied keywords'].values[0]

    metadatas['tokens in text'] = len(tokens)
    metadatas["text_extractableness"] = text_extractableness
    metadatas["metadata_extractableness"] = metadata_extractableness
    metadatas["keywords"] = "; ".join(keywords_text_list)
    metadatas["deduped_keywords"] = "; ".join(deduped_keywords)
    metadatas["alpha_sorted_deduped_keywords"] = "; ".join(
        sorted(deduped_keywords, key=str.casefold)
    )
    metadatas["deduped_keywords_with_scores"] = str(deduped_keywords_with_scores)

    # metadatas['synopsisplus'] = str(synopsisplus)
    metadatas["extractive_summary"] = extractive_summary
    metadatas["extractive_synopsis"] = extractive_synopsis

    metadatas["custom synopsis"] = config.get("custom synopsis", None)

    metadatas["submit synopsis"] = submit_synopsis

    metadatas["word length extracted pages"] = len(text.split())
    metadatas["pagecount"] = pagesize_analysis_results[3]
    # print(metadatas)

    # decide how to search for title matches
    # if there is no title, author or subject, use keywords

    if (
            metadatas["title"] == ""
            and metadatas["author"] == ""
            and metadatas["subject"] == ""
    ):
        goom_terms = " ".join(keywords_text_list[0:4])

        # else use title + author + subject
    else:
        goom_terms = (
                metadatas["title"] + " " + metadatas["author"] + " " + metadatas["subject"]
        )
        print("goom terms", goom_terms)
    catalog_results_list_of_dicts = {}
    metadatas['goom terms'] = goom_terms
    # use external isbnlib service to check for similar titles
    # add similar titles found in catalog to catalog_results_list_of_dicts

    try:
        catalog_results_list_of_dicts = check_if_titles_are_in_isbnlib(goom_terms)
        # metadatas['catalog_results_list_of_dicts'] = catalog_results_list_of_dicts
    except Exception as e:
        print("error submitting goom terms to isbnlib: " + str(e))

    # go through similar books found in catalog and save three titles

    catalog_titles = []
    if catalog_results_list_of_dicts != []:
        for count, result in enumerate(catalog_results_list_of_dicts):
            if result is not None:  # get title from catalog result
                result_info = result["Title"]
                catalog_titles.append(result["Title"])
                # stop after 3 results
                if count >= 2:
                    break
    metadatas["catalog_titles"] = catalog_titles

    # print('catalog titles are: ', catalog_titles)
    similar_titles = []
    if catalog_results_list_of_dicts:
        for l in catalog_results_list_of_dicts:
            # print("l", l)
            authors = ", ".join(l["Authors"])
            item_citation = (
                    l["Title"]
                    + ". "
                    + authors
                    + ". "
                    + l["Publisher"]
                    + ": "
                    + l["Year"]
                    + "\n"
                    + l["ISBN-13"]
                    + "."
                    + "\nDescription: "
                    + desc(l["ISBN-13"])
            )
            # print("item citation", item_citation)
            similar_titles.append(item_citation)
        similar_titles_candidates = "\n".join(similar_titles)

    else:
        pass
        # metadatas["Similar Titles Research"] = ""

    try:
        for c in catalog_titles:
            print(metadatas["title"], c)
            exactmatch = texts2exactmatch(metadatas["title"], c)
            if exactmatch:
                flipexactmatch = True
        for c in catalog_titles:
            # print(metadatas['title'], c)
            caseinsensitivematch = texts2caseinsensitivematch(metadatas["title"], c)
            if caseinsensitivematch:
                break
        for c in catalog_titles:
            print((metadatas["title"], c))
            try:
                fuzzymatch = texts2fuzzymatch(metadatas["title"], c)
                print("fuzzymatch", fuzzymatch)
                if fuzzymatch[0]:  # if fuzzymatch is not empty
                    metadatas["fuzzymatch"] = fuzzymatch[0]
                    metadatas["fuzzymatchscore"] = fuzzymatch[1]
                    fuzzymatch = True
                else:  # if fuzzymatch is empty
                    fuzzymatch = False
                    metadatas["fuzzymatch"] = False
                    metadatas["fuzzymatchscore"] = ""
            except Exception as e:
                print("can't calculate fuzzymatch for: " + metadatas["title"] + str(e))
                metadatas["fuzzymatch"] = ""
                metadatas["fuzzymatchscore"] = ""


    except Exception as e:
        print("can't connect to catalog: " + filename, e)
    metadatas["exactmatch"] = exactmatch
    metadatas["caseinsensitivematch"] = caseinsensitivematch

    # print(catalog_results_list_of_dicts)
    catalog_results_df = pd.DataFrame(catalog_results_list_of_dicts)
    catalog_results_df.T.to_json(thisdoc_dir + "/" + "isbnlib_matches.json")
    # print('catalog_results_df', catalog_results_df)
    metadatas["similar titles foond by isbnlib"] = str(catalog_titles)
    # metadatas['catalog_series'] = catalog_series
    if exactmatch or caseinsensitivematch or fuzzymatch:
        metadescription = desc(metadatas["catalog_titles"][0])
        metadatas["catalog_description"] = metadescription
        with open(thisdoc_dir + "/" + "metadescription.json", "w") as f:
            json.dump(metadescription, f)

    else:
        metadatas["catalog_description"] = ""

    if not metadata_extractableness and not text_extractableness:
        print("unable to analyze file: " + filename)

        print("payservices: ", payservices)
    # finished gathering free info
    # now creating metadata df

    try:
        print("creating parts of the book list with free content")

        frontparts = [metadatas["title"], metadatas["author"]]
        backparts = [
            metadatas["alpha_sorted_deduped_keywords"],
            metadatas["deduped_keywords"],
            # metadatas["Similar Titles Research"],
        ]
    except Exception as e:
        print(
            "problem creating front and backparts using free info: "
            + filename
            + "\n"
            + str(e)
        )

    if payservices:

        print("creating metadata using paid content, engine = " + engine)

        # if run_recursively:
        #     print("running recursive")
        #     recursive_result = recursively_summarize(text)

        if run_recursive:
            print("running recursive")
            try:
                recursive_result = recursively_summarize(text)
                submit_synopsis = recursive_result[0][-1]  # second to last result
                tokens_in_submitsynopsis = len(GPT2TokenizerFast.from_pretrained("gpt2").encode(submit_synopsis))

                metadatas["Recursive Summaries"] = recursive_result[0]
                recursion_stats = recursive_result[1]
                metadatas["Recursive Summarizer Statistics"] = recursion_stats
                metadatas["tokens in submit_synopsis"] = tokens_in_submitsynopsis
            except Exception as e:
                print('error in adding recursive info to metadatas ' + filename + '\n' + str(e))
        if ai_metadata == False:
            print("not generating narrative metadata using AI")
        else:
            print('generating narrative metadata using AI')
            print('length of submit synopsis', len(submit_synopsis))
            presets_this_run = common_presets_for_metadata()
            presets_token_budget = get_token_counts_for_presets(presets_this_run)
            metadatas["presets_token_budget"] = presets_token_budget
            print('presets_token_budget', presets_token_budget)
            try:
                # get data from create_title_metadata_using_openai_api

                data = create_title_metadata_using_openai(submit_synopsis, thisdoc_dir=thisdoc_dir)
                # metadatas['openai_metadata'] = data

                metadatas["Suggested Titles"] = data[0]
                metadatas["Book Description"] = data[2]
                metadatas["Bibliographic Keyword Phrases"] = data[1]
                metadatas["Recommended BISAC Categories"] = data[3]
                metadatas["Book Cover Blurb"] = data[4]
                metadatas["ELI5"] = data[5]
                metadatas["TLDR"] = data[6]
                metadatas["TLDR one word"] = data[7]
                metadatas["Formal Dissent"] = data[8]
                metadatas["Hostile MAGA Perspective"] = data[9]
                metadatas["Red Team Critique"] = data[10]
                metadatas["Suggested Action Items"] = data[11]
                metadatas["Scientific Style"] = data[12]
                metadatas["AI-generated metadata"] = data


            except Exception as e:
                print(
                    "error in adding openai info to metadatas " + filename + "\n" + str(e)
                )

            try:
                final_word_count = len(recursive_result[1:])
                text_word_count = len(text.split())
                methods = f'Recursive, transecting, abstractive summary.\nReduced word count from {text_word_count} to {final_word_count} words by looping through the document in in chunks of 3000 tokens each for {len(recursive_result[0])} rounds until the number of words in the remaining text matches the target floor and ceiling. Each summary paragraph is an independent response to a corresponding chunk of text. Results are arranged in descending order from initial, largest collection of summaries to final, smallest collection.\nMachine-generated and unsupervised; use with caution.'

                # print(methods)

                metadatas["Methods"] = methods
            except Exception as e:
                print('error in adding methods info to metadatas ' + filename + '\n' + str(e))

            try:
                metadatas["Foreword"] = create_foreword_in_one_step(
                    metadatas["title"], metadatas["author"], submit_synopsis, thisdoc_dir
                )
            except Exception as e:
                print("error creating foreword" + str(e))
                metadatas["Foreword"] = ""

        if create_interior_postscript:
            try:
                subprocess.run(
                    ['gs', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4', '-dPDFSETTINGS=/prepress', '-dNOPAUSE',
                     '-dQUIET', '-dBATCH', '-sOutputFile=interior_postscript.pdf', 'interior.pdf'])
                # run ghostscript from command line
                subprocess.run(["gs", "-dNOPAUSE", "-dBATCH", "-sDEVICE=ps2write", "-sOutputFile=output.ps", filename])

            except Exception as e:
                print("error creating postscript" + str(e))
                metadatas["interior_postscript"] = ""
        extractive_summary = metadatas.pop("extractive_summary")
        metadatas["extractive_summary"] = extractive_summary
        if run_page_by_page:
            print('textdf', text_df)
            page_by_page_results = text_df_to_ai_services(text_df=text_df, service="openai",
                                                          presets=['recursive_summarizer_concise'])
            # list comprehension to fix bad unicode
            # page_by_page_results = [fix_escape_sequences_in_text(i) for i in page_by_page_results]
            metadatas["page_by_page_results"] = page_by_page_results
        else:
            metadatas["page_by_page_results"] = []

    else:

        print("not incorporating paid info")

    # now creating front and back parts of the book using frontparrts and backparts as defined above
    try:
        metadatas2df(metadatas, thisdoc_dir, "LSI")
        # frontmatter = texts2docx(frontparts, "frontmatter.docx", thisdoc_dir, ".")
        print('successfully created frontmatter')
    except Exception as e:
        print("error creating frontmatter: " + filename + "\n" + str(e))
    try:
        metadatas2bookjson(metadatas, thisdoc_dir, "LSI")
        print("successfully created bookjson files for Scribus")
    except Exception as e:
        print("error creating bookjson files for Scribus: " + filename + "\n" + str(e))
    try:
        metadatas2internationaledition(metadatas, thisdoc_dir, ["ch"], ["MotivateChineseEdition"])
    except Exception as e:
        print("error creating international edition: " + filename + "\n" + str(e))
    try:
        pass
        # backmatter = texts2docx(backparts, "backmatter.docx", thisdoc_dir, ".")
    except Exception as e:
        print("error creating backmatter: " + filename + "\n" + str(e))

    # now save all created metadatas
    # try:
    #     with open(thisdoc_dir + "/" + "metadatas.json", "w") as f:
    #         json.dump(metadatas, f)
    # except Exception as e:
    #     print("failed to write metadatas.json", e)

    with open(thisdoc_dir + "/" + "pagedimensions.csv", "w") as m:
        # convert list of lists to csv
        writer = csv.writer(m)
        writer.writerows(pdfpagedimensions2list(filename))

    with open(thisdoc_dir + "/" + "extractive_summary.txt", "w") as m:
        m.write(str(extractive_summary))

    with open(thisdoc_dir + "/" + "keywords.json", "w") as m:
        json.dump(metadatas["alpha_sorted_deduped_keywords"], m)

    try:  # creating metadatas_df
        metadatas_df = pd.DataFrame.from_dict([metadatas], orient="columns")
    except Exception as e:
        print("error creating metadatas_df: " + filename + "\n" + str(e))
    try:
        metadatas_df.to_csv(thisdoc_dir + "/" + "metadatas_df.csv")
        metadatas_df.to_json(thisdoc_dir + "/" + "metadatas_df.json")
    except Exception as e:
        print("error saving metadatas_df: " + filename + "\n" + str(e))

    # metadatas_docx = texts2docx(, "metadatas_df.docx", thisdoc_dir, ".")
    # save metadata for this book in LSI format
    # check to make sure I created all the necessary fields
    if payservices:
        book_metadata_objects = book_metadata_json2distributor_format_targets("LST", thisdoc_dir)
        LSI_ACS_required_fields = book_metadata_objects[2]
        LSI_ACS_df = create_LSI_ACS_spreadsheet(metadatas_df, LSI_ACS_required_fields)
        LSI_ACS_df.to_csv(thisdoc_dir + "/" + "LSI_ACS.csv", index=False)

    return metadatas, metadatas_df  # , LSI_ACS_df


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--filename", help="filename of pdf to be processed")
    argparser.add_argument("--thisdoc_dir", help="directory where all files for this book will be stored")
    argparser.add_argument("--payservices", help="whether to use paid services", default=False)
    argparser.add_argument("--run_page_by_page", help="whether to run page by page", default=False)
    argparser.add_argument("--output__dir", help="directory where all files for this book will be stored")
    argparser.add_argument("--limit", help="limit number of pages to process", default=10)
    argparser.add_argument("--list2string", help="whether to convert list to string", default=False)
    argparser.add_argument("--filecount", help="number of files to process", default=1)
    argparser.add_argument("--timestamped_filename", help="whether to use timestamped filename", default=False)
    argparser.add_argument("--config", help="config file", default="config.json")
    argparser.add_argument("--run_recursively", help="whether to run recursively", default=False)
    argparser.add_argument("--ai_metadata", help="whether to run ai metadata", default=False)
    argparser.add_argument("--create_interior_postscript", help="whether to create interior postscript", default=False)
    argparser.add_argument("--mode", help="mode", default="assess")

    args = argparser.parse_args()

    filename = args.filename
    thisdoc_dir = args.thisdoc_dir
    payservices = args.payservices
    run_page_by_page = args.run_page_by_page
    output_dir = args.output_dir
    limit = args.limit
    list2string = args.list2string
    filecount = args.filecount
    timestamped_filename = args.timestamped_filename
    config = args.config
    run_recursively = args.run_recursively
    ai_metadata = args.ai_metadata
    create_interior_postscript = args.create_interior_postscript
    mode = args.mode

    results = process_pdf(
        filename,
        output_dir,
        limit,
        list2string,
        filecount,
        timestamped_filename,
        payservices,
        config,
        run_recursively, run_page_by_page, ai_metadata, create_interior_postscript, mode="assess"
    )
