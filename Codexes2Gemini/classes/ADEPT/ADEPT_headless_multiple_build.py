import argparse
import logging
import os
import re
import traceback
from datetime import datetime
import numpy as np
import pandas as pd
import streamlit as st
from pypandoc import convert_file

import classes.ADEPT.ADEPT_utilities as Au
import classes.Codexes.Metadata.Metadatas as MDS
from app.utilities import pdf2resizedpdf, pdf2pdfwithfooter
from app.utilities.metadatas2outputformats import metadatas2bookjson, metadatas2markdown
from app.utilities.text2metadata_using_openai import common_presets_for_metadata
from app.utilities.utilities import directory_contains_subdirectory, configure_logger
from classes.ADEPT.CorePDFProcessor import CorePDFProcessor
from classes.Codexes.Metadata.Distributors.LSI.create_LSI_ACS_spreadsheet import create_LSI_ACS_spreadsheet
from classes.SyntheticReaders.gemini2syntheticreaders.BookAnalysisPlan import BookAnalysisPlan
from classes.SyntheticReaders.gemini2syntheticreaders.text2gemini import Text2Gemini

logger = configure_logger('info')
# from classes.ADEPT.ADEPT_Multiple_File_Self_Serve import pages_to_process_limit
# from classes.ADEPT.ADEPT_Multiple_File_Self_Serve import autils

autils = Au.ADEPTUtilities()


def parse_doc_ranges(range_str):
    """
    Parses a string containing page ranges into a list of individual page numbers.

    Parameters:
        range_str (str): The string containing page ranges.

    Returns:
        list: A list of individual page numbers.

    Note:
        If no page ranges are provided, None is returned.

    Example:
        range_str = "1-5, 7, 10-15"
        parse_doc_ranges(range_str)  # Output: [1, 2, 3, 4, 5, 7, 10, 11, 12, 13, 14, 15]

    """
    if not range_str: return None
    ranges = []
    for part in range_str.split(','):
        x = list(map(int, part.split('-')))
        ranges.extend(range(x[0], x[-1] + 1)) if len(x) == 2 else ranges.append(x[0])
    logging.debug(f"returning page list {ranges}")
    return ranges


def headless_scan(root_dir, pages_to_process_limit, move_files, llama_indexing_on):
    all_results_pairs = []
    logging.info('beginning headless scan')
    logging.info(f"root dir is {root_dir}")
    logging.info(f"move files is {move_files}")
    logging.info(f"llama_indexing_on is {llama_indexing_on}")
    metadatas = MDS.Metadatas()
    print(f"metadatas is {metadatas}")
    logging.info(f"metadatas: {metadatas}")
    # Three steps:

    # 1. Process PDF files directly in the root_dir

    results_pairs = autils.addPDFs2specsfile(directory=root_dir, pages_to_process_limit=pages_to_process_limit,
                                             move_files=move_files, llama_indexing_on=llama_indexing_on,
                                             thisdoc_dir=None)
    all_results_pairs.append(results_pairs)
    # 2. check if a directory contains subdirectories
    if directory_contains_subdirectory(root_dir):
        logging.info('now doing directories')
        # Existing code to process subdirectories
        # 3. Process each subdirectory
        for dirpath, dirnames, files in os.walk(root_dir):
            for dirname in dirnames:
                logging.info(dirname)
                try:
                    results_pairs_below = autils.addPDFs2specsfile(directory=root_dir + '/' + dirname,
                                                                   pages_to_process_limit=pages_to_process_limit,
                                                                   move_files=move_files,
                                                                   llama_indexing_on=llama_indexing_on)
                    all_results_pairs.append(results_pairs_below)
                except Exception as e:
                    logging.info("Builds failed:")
                    traceback.print_exc()
    # 3. Combine all dataframes
    if len(all_results_pairs) > 0:
        return all_results_pairs
    else:
        return None


def headless_multiple_build(all_results_pairs, presets_this_run, pages_to_process_limit,
                            number_of_front_matter_pages, spin, flags, temperature, model, llama_indexing_on,
                            documents_to_select):
    print("entering multiple build")
    logging.info(f"running model {model}")
    logging.info("entered multiple build")
    print(f"length of all_results_pairs is {len(all_results_pairs)}")
    cumulative_lsi_df = pd.read_csv("output/cumulative_lsi_df.csv")
    lsi_df = pd.DataFrame()
    for results_pair in all_results_pairs:
        print(results_pair)
        specs_df = results_pair['specs_input_df']
        metadatas = results_pair['metadatas']
        # print(f"length of metadatas on entering build is {len(metadatas)}")
        # print(metadatas)
        if isinstance(specs_df, pd.DataFrame):
            # specs_df = specs_file_path
            print(f"loaded specs_df object received from scan function with shape {specs_df.shape}")

        # print(specs_df.T)

        if presets_this_run == "Full":
            presets_this_run = common_presets_for_metadata()

        # if these columns are missing
        text_cols = ['title', 'subtitle', 'author', 'flags']
        # Ensure the DataFrame has all the required columns
        for column in text_cols:
            if column not in specs_df.columns:
                # If a column is missing, add it with default values as NaN
                specs_df[column] = np.nan

        if 'page-by-page-AI' in flags:
            pagebypage = True
        else:
            pagebypage = False
        if documents_to_select:
            logging.info("overriding specs file based on command line doc_ranges")
            docs_list = parse_doc_ranges(documents_to_select)
            logging.info(f"docs selected are {docs_list}")
            print(f"docs selected are rows {docs_list}")
            for doc in docs_list:
                specs_df.at[doc - 1, 'select'] = True
            logging.info(specs_df)
        specs_df['select'] = specs_df['select'].astype('bool')
        # print(f"post-adding select {specs_df.T}")
        logging.info(specs_df['select'])
        selected_titles = specs_df[specs_df['select'] == True]
        logging.debug(selected_titles)
        print(f"selected_titles are {selected_titles['title'].values}")
        if selected_titles['select'].count() == 0:
            logging.info('No titles selected, not building any books')
            return
        else:
            logging.info(f"Found {selected_titles['select'].count()} titles to process")
        selected_titles.to_csv("output/selectedtitles.csv")
        logging.debug(selected_titles)
        for index, row in selected_titles.iterrows():
            logging.debug(f"iterating through row {index}")
            core = CorePDFProcessor(f"{row['filename']}")
            autils = Au.ADEPTUtilities()
            if metadatas is None:
                logging.warning(f"No metadata found for {row['filename']}, creating new object")
                metadatas = MDS.Metadatas()

            max_tokens_default = metadatas.get_attribute("max_tokens_default")
            metadatas.set_attributes_to_values({'presets_this_run': presets_this_run})
            metadatas.set_attributes_to_values({"model_default": model})
            metadatas.set_attributes_to_values({'filepath': row['filename']})
            metadatas.set_attributes_to_values({'pages_to_process_limit': pages_to_process_limit})
            metadatas.set_attributes_to_values({'number_of_front_matter_pages': number_of_front_matter_pages})
            metadatas.set_attributes_to_values({'spin': spin})
            metadatas.set_attributes_to_values({'flags': flags})
            # create safe thisdoc_dir filename from base filename
            filename = row['filename']
            logging.info(filename)

            # gemini_summary = t2g.process_text(page)

            safedirname = row['title']
            print(row['title'])

            # check if these keys exist in dataframe
            needed_keys = ['title', 'filename', 'author', 'ISBN']
            for n in needed_keys:
                if n not in selected_titles.columns:
                    logging.info("dataframe is missing a required column heading` (key)")
                    exit()
            if len(safedirname) <= 4:
                if not isinstance(row["ISBN"], str):
                    row["ISBN"] = str(row["ISBN"])
                logging.info(f"length of ISBN {len(row['ISBN'])}")
                logging.info(row['ISBN'])

                if int(len(row["ISBN"]) >= 13):
                    safedirname = row["ISBN"]
                    logging.info('safedirname is based on ISBN')
                else:
                    if int(len(row['author'])) >= 4:
                        safedirname = row['author']
                        logging.info(f"row[author] is {row['author']}")
                        logging.info('safedirname is based on author')
                    else:
                        now = datetime.now()

                        # Convert the current datetime to string
                        time_string = now.strftime("%Y-%m-%d-%H:%M:%S")
                        safedirname = time_string
                        logging.info('safedirname is based on time')
                logging.info(f"safedirname is {safedirname}")

            safedirname = re.sub(r'\W', '_', safedirname)
            logging.info(f"safedirname is {safedirname}")

            # truncate thisdoc_dir at 30
            # thisdoc_dir = thisdoc_dir[:29]
            thisdoc_dir = autils.create_built_thisdoc_dir(safedirname)
            print(thisdoc_dir)
            metadatas.set_attributes_to_values({'thisdoc_dir': thisdoc_dir})
            # logging.info(f"thisdoc_dir is {thisdoc_dir}")
            file_to_read = autils.get_pages_limit_from_PDF(metadatas)
            logging.info(f"file_to_read is {file_to_read}")

            metadatas = autils.pdf2text_analysis(metadatas, file_to_read)

            text = metadatas.get("pages_strings")

            t2g = Text2Gemini()
            book_plan = BookAnalysisPlan(context=text, user_keys_list=[
                "ADEPT2-publishing-information",
                "ADEPT2-abstracts",
                "mnemonics",
                "most_important_passages",
                "glossary-lay-reader",
                "timeline-major",
                "index-of-persons",
                "index-of-places"
            ])

            book_plan.set_attribute("thisdoc_dir", thisdoc_dir)

            # Add prompt plans
            for key in book_plan.list_of_user_keys_to_use:
                book_plan.add_prompt_plan([key])

            # Execute all plans
            results = book_plan.execute_plans(t2g, metadatas)

            # Process results is now handled within execute_plans

            metadatas_dict = metadatas.get_all_attributes()
            save_metadatas_df(metadatas_dict, thisdoc_dir)

            logging.info(f"pagebypage is {pagebypage}")
            # logging.info(metadatas)
            if pagebypage:
                pagebypagepresets = ['PageByPageSummary', 'PageByPageNotableQuotes']
                metadatas.set_attributes_to_values({'page_by_page_presets': pagebypagepresets})
                try:
                    metadatas = core.pagebypage2aiservices(metadatas, presets=pagebypagepresets, model=model,
                                                           temperature=temperature, max_tokens=max_tokens_default)
                    logging.info(f"Created page by page analysis using {len(pagebypagepresets)} presets.")
                except Exception as e:
                    logging.info(f"An error occurred in pagebypage2aiservices while processing the PDF: {str(e)}")
                    traceback.print_exc()
            else:
                metadatas.set_attributes_to_values({'page_by_page_presets': ""})
                logging.info("Did not create any page by page metadata")

            try:
                logging.info("preparing PDF body for printing")
                metadatas = pdf2resizedpdf.calculate_target_dimensions(metadatas, target_width=8.5, target_height=11.0)
                pdf_file = metadatas.get_attribute("filepath")
                output_file = thisdoc_dir + "/resized.pdf"
                target_width = metadatas.get_attribute("target_width")
                target_height = metadatas.get_attribute("target_height")
                pdf2resizedpdf.two_step_landscape_to_portrait(pdf_file, output_file, target_width, target_height)
            except Exception as e:
                traceback.print_exc()

            try:
                logging.info("adding footer to body")
                footered_file_path = thisdoc_dir + "/footered.pdf"
                pdf2pdfwithfooter.add_footer(output_file, footered_file_path)
            except Exception as e:
                logging.info(f"An error occurred while adding footer: {str(e)}")
                traceback.print_exc()

            try:
                logging.info('creating front matter')
                print(f"metadatas right before creating fm {len(metadatas.keys())}")
                metadatas = core.create_front_matter(f"{row['filename']}", metadatas,
                                                     thisdoc_dir)  # docx commented out
            except Exception as e:
                logging.info(f"An error occurred in create_front_matter while processing the PDF: {str(e)}")
                traceback.print_exc()
            print(f"metadata keys after create fm {len(metadatas.keys())}")
            markdown_front_matter = metadatas2markdown(metadatas, thisdoc_dir)
            # metadatas.save_at_stage()
            with open(thisdoc_dir + "/front_matter.md", "w") as f:
                f.write(markdown_front_matter)

            # convert markdown to pdf

            convert_file(thisdoc_dir + "/front_matter.md", 'pdf', outputfile=thisdoc_dir + "/tex_front_matter.pdf",
                         extra_args=['--toc', '--toc-depth=2', '--pdf-engine=xelatex', '-V', 'mainfont=Skolar PE',
                                     '--pdf-engine=xelatex', ])

            ISBN = metadatas.get("ISBN")
            metadatas = core.merge_front_matter_with_body(f"{ISBN}_interior.pdf", metadatas, thisdoc_dir,
                                                          "tex_front_matter.pdf")

            try:
                logging.info(metadatas.get('shortuuid'))
                bookjson = metadatas2bookjson(metadatas, thisdoc_dir)
                logging.info('Successfully created bookjson for cover')
                # logging.info(bookjson)
            except Exception as e:
                logging.info(f"An error occurred in 2bookjson while processing the PDF: {str(e)}")
                bookjson = {f"error": {e}}
                traceback.print_exc()
            bookjson_df = pd.DataFrame.from_dict(bookjson, orient='index')
            # fill in missing values
            bookjson_df = bookjson_df.fillna('')
            bookjson_df.sort_index(inplace=True)

            # set up save of bookjson
            uuid = metadatas.get('uuid')
            if len(uuid) == 8:
                logging.info(f"uuid is {uuid}")
            else:
                logging.info(f"uuid is {uuid}")
            full_path = os.path.abspath(f'resources/bookjson/{metadatas.uuid}.json')
            logging.info(full_path)
            logging.info(f"bookjson saved to {full_path}")
            bookjson_df.to_json(full_path)

            try:
                lsi_df = create_LSI_ACS_spreadsheet(metadatas)
            except Exception as e:
                errormessage = f"error creating metadata for distributors in {e}"
                logging.info(errormessage)
                traceback.print_exc()
            metadatas = metadatas.get_all_attributes()
            ISBN = metadatas['ISBN']
            title = metadatas['title']
            if ISBN:
                # replace special characters with underscores in ISBN
                ISBN_safe = re.sub(r'\W+', '_', ISBN)
                LSI_ACS_filename = f"{ISBN_safe}_frontmatter.csv"
            else:
                title_safe = re.sub(r'\W+', '_', title)
                LSI_ACS_filename = f"{title_safe}_frontmatter.csv"

            lsi_df.to_csv(f"{thisdoc_dir}/{LSI_ACS_filename}")
            logging.info(f"wrote {LSI_ACS_filename} to {thisdoc_dir}")
            logging.info(lsi_df.head())

    cumulative_lsi_df = pd.concat([lsi_df, cumulative_lsi_df])
    try:
        cumulative_lsi_df.to_csv("output/cumulative_lsi_df.csv")
    except Exception as e:
        traceback.print_exc()
        st.error(e)

    return


def save_metadatas_df(metadatas_dict, thisdoc_dir):
    metadatas_df = pd.DataFrame.from_dict(metadatas_dict, orient='index')
    metadatas_df.sort_index(inplace=True)
    metadatas_df.to_json(f'{thisdoc_dir}/metadata.json')


def save_spec_file(specs_df):
    # create six-character-long uuid
    spec_file_path = "/tmp/specs_df.csv"
    if 'uuid' in specs_df.columns:
        uuid = specs_df['uuid'].values[0]
        # if uuid is string 4 characters or longer, ok
        if len(uuid) < 4:
            uuid = str(uuid.uuid4())[:6]
        spec_file_path = f"output/specs/{uuid}.csv"
        specs_df.to_csv(spec_file_path, index=False)
    logging.info(f"successfully saved new specs_file to {spec_file_path}")
    return spec_file_path


def start_build_process(args, results_dict):
    headless_multiple_build(results_dict,
                            presets_this_run=args.presets_this_run,
                            pages_to_process_limit=args.pages_to_scan,
                            number_of_front_matter_pages=args.number_of_front_matter_pages,
                            spin=args.spin,
                            flags=args.flags,
                            temperature=args.temperature,
                            model=args.model,
                            llama_indexing_on=args.llama_indexing_on,
                            documents_to_select=args.documents_to_select)


def guard_against_invalid_args():
    """
    guard against invalid arg values
    """
    if args.pages_to_scan <= 0:
        raise ValueError("Invalid value for pages_to_scan argument")
    if args.scan_only and args.build_only and args.scan_then_build:
        raise ValueError("Invalid combination of arguments")
    if args.number_of_front_matter_pages < 0:
        raise ValueError("Invalid value for number_of_front_matter_pages argument")
    if args.temperature < 0 or args.temperature > 2:
        raise ValueError("Invalid value for temperature argument")


if __name__ == "__main__":

    # Define additional functions to abstract duplicate code

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--documents_to_select", help="List of document ranges to  select, e.g. 1, 3-4",
                        default="1", type=str)
    parser.add_argument("-E", "--model", help="model (Engine) parameter", default="gpt-4o", type=str)
    parser.add_argument("--flags", help="flags parameter", default="ADEPT", type=str)
    parser.add_argument("--presets_this_run", type=str, default="Full",
                        help="Annotation presets to run")
    parser.add_argument("-I", "--scan_me", help="Scan this directory", default="working/public_domain/today")
    parser.add_argument('-l', '--log_level', default='info', help='Define logging level')
    parser.add_argument("-ll", "--llama_indexing_on", action="store_true",
                        help="Activate llama indexing, default is off")
    parser.add_argument("-m", "--move_files", help="Should move files from inbox to scanned folders",
                        action='store_true')
    parser.add_argument("-M", "--megacontext_text_analyzer", default="gemini-1.5-flash-001",
                        help='Choose text analysis method with large-context LLM')
    parser.add_argument('-nfm', '--number_of_front_matter_pages', type=int, default=0)
    parser.add_argument("-p", "--pages_to_scan", help="Number of pages to scan", default=10, type=int)
    parser.add_argument("--page_by_page", type=str, default="page-by-page-AI",
                        help="Specify which page-by-page options to execute")
    parser.add_argument("-i", "--specs_file_path", help="Path to the specs file", default="output/specs/test.csv")
    parser.add_argument('-sp', '--spin', help="Specify spin for this collection of documents", default="")
    parser.add_argument("-T", "--temperature", help="Specify temperature for llama indexing", default=1.0, type=float)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--scan_only", action='store_true', help="Scan folders for PDFs only")
    group.add_argument("--build_only", action='store_true', help="Build books from existing specs file")
    group.add_argument("--scan_then_build", action='store_true', help="Conduct scanning then building all in one step")
    parser.set_defaults(scan_then_build=True)
    args = parser.parse_args()
    guard_against_invalid_args()

    # numeric_level = getattr(logging, args.log_level.upper(), None)
    # if not isinstance(numeric_level, int):
    #     raise ValueError(f'Invalid log level: {args.log}')
    # logger = configure_logger(args.log_level)
    # logging.warning('WARN')

    if args.scan_then_build:
        logging.info('\n\n\n*** starting scan then build ***\n\n\n')
        results_dict = headless_scan(root_dir=args.scan_me,
                                     pages_to_process_limit=args.pages_to_scan,
                                     move_files=args.move_files,
                                     llama_indexing_on=args.llama_indexing_on)
        for r in results_dict:
            start_build_process(args, r)

    elif args.scan_only:
        logging.info('*** starting scan only ***')
        specs_df = headless_scan(root_dir=args.scan_me,
                                 pages_to_process_limit=args.pages_to_scan,
                                 move_files=args.move_files,
                                 llama_indexing_on=args.llama_indexing_on)

        exit()

    elif args.build_only:
        logging.info('*** starting build only ***')
        start_build_process(args, args.specs_file_path)

    logging.warning("completed")
