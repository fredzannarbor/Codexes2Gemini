import csv
import io
import json
import logging
import os
import random
from importlib import resources
from textwrap import shorten

from Codexes2Gemini.ui.ui_utilities import flatten_and_stringify

from Codexes2Gemini.classes.Codexes.Metadata.metadatas2distributor_reqts import process_acrobat_toc, \
    calculate_min_max_age_grade, get_LSI_ACS_keywords, create_draft_book_description, calculate_pub_date

from Codexes2Gemini.classes.Codexes.Distributors.LSI.create_LSI_ACS_spreadsheet import create_LSI_ACS_spreadsheet

from Codexes2Gemini.classes.Utilities.classes_utilities import load_spreadsheet
from Codexes2Gemini.classes.Codexes.Builders.Codexes2Codexes import Codex2Plan2Codex
import fitz
import pandas as pd
from datetime import datetime

import pypandoc
import streamlit as st
import traceback
from Codexes2Gemini.classes.Codexes.Builders import Codexes2Parts
from Codexes2Gemini.classes.Codexes.Builders.PromptsPlan import PromptsPlan
from classes.Codexes.Metadata.Metadatas import Metadatas
from classes.Codexes.Builders.CodexBuilder import results2assembled_pandoc_markdown_with_latex, \
    create_publishing_information_block, results2assembled_pandoc_markdown_no_latex


class PG19FetchAndTrack:
    def __init__(self, metadata_file, data_dirs,
                 processed_csv='processed_metadata.csv',
                 output_dir='processed_data',
                 number_of_context_files_to_process=3, file_index={}):  # Default N to 3
        self.metadata_file_path = metadata_file
        self.data_dirs = data_dirs
        self.processed_csv = processed_csv
        self.output_dir = output_dir
        self.number_of_context_files_to_process = number_of_context_files_to_process
        self.load_processed_metadata()
        self.CODEXES2PARTS = Codexes2Parts()  # Initialize Codexes2Parts here
        self.file_index = file_index

    def load_processed_metadata(self):
        if os.path.exists(self.processed_csv):
            self.processed_df = pd.read_csv(self.processed_csv)
        else:
            self.processed_df = pd.DataFrame(columns=['textfilename', 'processed', 'processing_date', 'output_json'])

    # @st.cache_data  # Cache this for efficiency
    def create_file_index(_self):
        """Creates a file index for efficient lookup of text files."""
        file_index = {}
        # st.write(f"metadata file path: {_self.metadata_file_path}")
        try:
            with open(_self.metadata_file_path, "r") as f:
                reader = csv.reader(f)
                header = next(reader)  # Read the header row
                # st.write(f"Header columns: {header}")  # This will print the header columns

                for row in reader:
                    # st.write(row)
                    textfilename = row[0]
                    for data_dir in _self.data_dirs:
                        filepath = os.path.join(data_dir, f"{textfilename}.txt")

                        if os.path.exists(filepath):
                            file_index[textfilename] = filepath
                            break
        except FileNotFoundError:
            st.error(f"Metadata file not found: {_self.metadata_file_path}")
            # Handle the error appropriately, e.g., return an empty dictionary or raise an exception

        return file_index

    def fetch_pg19_data(self, skip_processed, markdown_results_no_latex=None):
        """Fetches PG19 data based on the provided metadata and processing options.

        Args:
            skip_processed (bool): Whether to skip already processed files.

        Returns:
            None
        """
        # TODO - allow user to upload any data set in correct format

        all_results = []
        file_index = self.create_file_index()
        # st.write(st.session_state.current_plan["selected_rows"])
        if not st.session_state.current_plan["selected_rows"]:
            st.error("fetch_pg19_data did not receive any rows")
            st.stop()

        for row in st.session_state.current_plan["selected_rows"]:
            textfilename = row['textfilename']
            metadata_this_row = Metadatas()

            # Check if file is already processed and skip_processed is on
            if skip_processed and self.processed_df[self.processed_df['textfilename'] == textfilename][
                'processed'].any():
                st.info(f"Skipping already processed file: {textfilename}")
                logging.info(f"Skipping already processed file: {textfilename}")
                continue

            filepath = file_index.get(textfilename)

            if filepath is None:
                logging.error(f"Error Could not find file for {textfilename}")
                st.error(f"Error: Could not find file for {textfilename}")
                continue

            with open(filepath, "r") as f:
                context = f.read()
            st.session_state.current_plan.update({"plan_type": "User"})

            # FIX - Browsable GLossary must be shorter
            # FIX - Timeline must be enforced to have double-new-lines

            results = self.process_single_context(context, row)

            publishing_info_block = f"""

# Publishing Information

(c) 2024 Nimble Books LLC

ISBN: "TK"

Nimble Books LLC ~ NimbleBooks.com

_Humans and models making books richer, more diverse, and more surprising._
"""

            results.insert(1, publishing_info_block)
            # create CondenserPlan
            c2c = Codex2Plan2Codex()
            condenser_results_string = self.create_condensed_matter_string(c2c, context, row, textfilename)
            # results.append(condenser_results_string)
            results.insert(-2, condenser_results_string)

            # Save results to JSON
            self.save_results_to_json(textfilename, results)
            try:
                markdown_results_with_latex = results2assembled_pandoc_markdown_with_latex(results)
                markdown_results = markdown_results_with_latex
            except Exception as e:
                st.error(f"error saving markdown results with latex preamble: {e}")
                markdown_results_no_latex = results2assembled_pandoc_markdown_no_latex((results))
                markdown_results = markdown_results_no_latex

            st.json(markdown_results, expanded=False)
            self.save_results_to_markdown(textfilename, markdown_results)


            pdf_creation_on = True
            # FIX graceful failure of latex textwidth]
            if pdf_creation_on:
                try:
                    result_pdf_file_name = self.save_markdown_results_with_latex_to_pdf(markdown_results, textfilename)
                except Exception as e:
                    logging.error(f"{e}: \n{traceback.format_exc()}")
                    st.error(f"error saving to PDF: {e}")
                    result_pdf_file_name = "processed_data/failed.pdf"

                if "collapsar" in st.session_state.current_plan["imprint"].lower():
                    ImprintText = "Collapsar Classic"
                    sheetname = "White B&W Perfect"  # "Standard 70 perfect"

                elif "adept" in st.session_state.current_plan["imprint"].lower():
                    ImprintText = "AI Lab for Book-Lovers"
                    sheetname = "White B&W Perfect"

                bookjson_this_book = self.create_simple_bookjson(textfilename, results, result_pdf_file_name,
                                                                 ImprintText=ImprintText, sheetname=sheetname)
                try:
                    self.save_bookjson_this_book(textfilename, bookjson_this_book)
                    st.session_state.current_plan.update({"plan_type": "Catalog"})
                except Exception as e:
                    self.logger.error(traceback.format_exc())

                catalog_results = self.generate_catalog_metadata(context, row)

                catalog_file_name = textfilename + "_catalog.json"
                catalog_results_df = pd.DataFrame(catalog_results)
                catalog_results_df.to_csv(f"{self.output_dir}/{textfilename}_catalog.csv")

            else:
                st.info(f"temporarily disabled PDF and bookjson file creation")

            # run headless lsicoverbuilder


            self.update_processed_metadata(textfilename)

            all_results.append(results)

        self.save_processed_metadata_to_cumulative_csv()

        return all_results

    def create_condensed_matter_string(self, c2c, context, row, textfilename):
        condenserPlan = c2c.create_condenserPlan(textfilename, context)
        # st.json(condenserPlan.to_dict, expanded=False)
        print("condenserPlan:")
        print(condenserPlan)
        condenser_prompts = self.process_single_context(context, row, plan=condenserPlan)
        print(condenser_prompts)

        # write condenser_promts list to file for checking
        with open(f"processed_data/{textfilename}" + "_condenser_prompts.json", "w") as f:
            data = json.dumps(condenser_prompts)
            f.write(data)


        condenser_results = c2c.run_condenser_prompts(condenser_prompts)
        with open(f"processed_data/{textfilename}" + "_condensed.json", "w") as f:
            data = json.dumps(condenser_results)
            f.write(data)
        st.write(condenser_results)
        condenser_results_string = flatten_and_stringify(condenser_results)
        with open(textfilename + "_condensed.md", "w") as f:
            f.write(condenser_results_string)
        condenser_results_string = f"# Condensed Matter\n\n{condenser_results_string}"
        return condenser_results_string

    def fetch_pg19_metadata(self, number_of_context_files_to_process, selection_strategy):
        """Fetches metadata for N random PG19 entries.

        Args:
            number_of_context_files_to_process (int): The number of random entries to fetch.

        Returns:
            list: A list of lists, where each inner list represents a row of metadata."""
        #st.info(selection_strategy)
        if selection_strategy == "Sample":
            with open(self.metadata_file_path, "r") as f:
                reader = csv.reader(f)
                next(reader)  # Skip header row
                rows = list(reader)
                return random.sample(rows, number_of_context_files_to_process)
        elif selection_strategy == "Sequential":
            #rows = st.session_state()
            return random.sample(rows, number_of_context_files_to_process)  # first random

    def process_single_context(self, context, row, plan=None):
        """Processes a single context and returns the results.

        Args:
            context (str): The text content of the context.
            row (list): The metadata row corresponding to the context.
            plan (PromptsPlan, optional): The PromptsPlan object to use.
                                          If None, it will use the current plan
                                          from the session state.

        Returns:
            list: A list of results from processing the context.
        """
        # Update the current plan in the session state with context and row
        st.session_state.current_plan.update({"context": context, "row": row})

        # Use the provided plan or create one from the session state
        if plan is None:
            plan = PromptsPlan(**st.session_state.current_plan)

        # Call process_codex_to_book_part from Codexes2Parts
        satisfactory_results = self.CODEXES2PARTS.process_codex_to_book_part(plan)
        return satisfactory_results

    def save_results_to_json(self, textfilename, results):
        """Saves results to a JSON file."""
        output_json_filename = f"{textfilename}.json"
        output_json_path = os.path.join(self.output_dir, output_json_filename)
        os.makedirs(self.output_dir, exist_ok=True)
        try:
            with open(output_json_path, 'w') as f:
                json.dump({
                    'textfilename': textfilename,
                    'processing_date': datetime.now().isoformat(),
                    'results': results
                }, f, indent=4)

            logging.info(f"Successfully saved results to JSON at {output_json_path}")
            st.toast(f"Successfully saved results to JSON at {output_json_path}")
        except Exception as e:
            print(f"Error saving results to JSON: {traceback.format_exc()}")
            st.error(f"Error saving results to JSON: {traceback.format_exc()}")
            logging.error(f"Error saving results to JSON: {traceback.format_exc()}")
            return

    def save_results_to_markdown(self, textfilename, results):
        """Saves results to a Markdown file."""
        output_markdown_filename = f"{textfilename}.md"
        output_markdown_path = os.path.join(self.output_dir, output_markdown_filename)
        os.makedirs(self.output_dir, exist_ok=True)
        try:
            with open(output_markdown_path, 'w') as f:
                if isinstance(results, list):
                    for item in results:
                        f.write(item)
                elif isinstance(results, str):
                    f.write(results)
                else:
                    f.write(str(results))

            logging.info(f"Successfully saved file to markdown at {output_markdown_path}")
            st.toast(f"Successfully saved file to markdown at {output_markdown_path}")
        except Exception as e:
            print(f"Error saving results to Markdown: {traceback.format_exc()}")
            st.error(f"Error saving results to Markdown: {traceback.format_exc()}")
            logging.error(f"Error saving results to Markdown: {traceback.format_exc()}")

    def update_processed_metadata(self, textfilename):
        """Updates the processed metadata DataFrame."""
        new_row = pd.DataFrame({
            'textfilename': [textfilename],
            'processed': [True],
            'processing_date': [datetime.now()],
            'output_json': [f"{textfilename}.json"]
        })
        self.processed_df = pd.concat([self.processed_df, new_row], ignore_index=True)

    def save_processed_metadata_to_cumulative_csv(self):
        """Saves the processed metadata to a CSV file."""
        self.processed_df.to_csv(self.processed_csv, index=False)

    def save_markdown_results_with_latex_to_pdf(self, md_result, textfilename, extra_args=None):
        """Saves markdown to PDF, handling Pandoc errors gracefully."""
        output_pdf_filename = f"{textfilename}.pdf"
        output_pdf_path = os.path.join(self.output_dir, output_pdf_filename)
        os.makedirs(self.output_dir, exist_ok=True)
        if extra_args is None:
            extra_args = ['--toc', '--toc-depth=2', '--pdf-engine=lualatex', '-V', 'mainfont=Miller Text',
                          '--lua-filter=/Users/fred/bin/nimble/Codexes2Gemini/resources/lua/reduce_heading.lua']
        try:
            # If md_result is a list, join the elements into a string
            if isinstance(md_result, list):
                md_result = ''.join(md_result)

            pypandoc.convert_text(md_result, 'pdf', format='markdown',
                                  outputfile=output_pdf_path, extra_args=extra_args)
            logging.info(f"PDF saved to {output_pdf_path}")
            st.toast(f"Successfully saved PDF to {output_pdf_path}")

        except Exception as e:  # Catch any exception here
            logging.error(f"Error saving to PDF: {e}\n{traceback.format_exc()}")
            st.error(f"Error saving to PDF: {e}\n{traceback.format_exc()}")
            return
            # TODO (optional):
            # 1. Attempt to sanitize the Markdown (e.g., remove problematic LaTeX)
            # 2. Retry the conversion with pypandoc
            # 3. If retry fails, save the problematic Markdown to a separate file

        return output_pdf_path  # Return the path even if there was an error

    def create_simple_bookjson(self, textfilename, results, result_pdf_file_name,
                               ImprintText="Collapsar Classics", sheetname=None):
        doc = fitz.open(result_pdf_file_name)
        pagecount = doc.page_count
        spinewidth, effective_page_count = self.calculate_spinewidth(sheetname, pagecount)
        # st.write(sheetname, pagecount, spinewidth)
        logging.info(f"Imprint: {st.session_state.current_plan['imprint']}")
        if "adept" in st.session_state.current_plan["imprint"].lower():
            trimsizeheight = 11
            trimsizewidth = 8.5
        if "collapsar" in st.session_state.current_plan["imprint"].lower():
            trimsizeheight = 6
            trimsizewidth = 4

        # st.write(st.session_state.current_plan.keys())
        book_json = dict(BookID="TBD", BookTitle=st.session_state.current_plan['gemini_title'],
                         SubTitle=st.session_state.current_plan['gemini_subtitle'],
                         Byline=st.session_state.current_plan['gemini_authors_no_latex_str'],
                         ImprintText=ImprintText, ImageFileName="", settings="duplex", distributor="LSI",
                         InvertedColor="White", DominantColor="Black", BaseFont="Skolar PE Regular",
                         trimsizewidth=trimsizewidth,
                         trimsizeheight=trimsizeheight, spinewidth=spinewidth,
                         effective_page_count=effective_page_count,
                         backtext=(st.session_state.current_plan['gemini_summary'] or "TBD"))
        st.write(book_json)
        with open("test.json", "w") as f:
            f.write(json.dumps(book_json))
        return book_json

    def calculate_spinewidth(self, sheetname, finalpagecount):

        # TO DO - add importlib resources link
        file_name = os.path.join("resources/data_tables/LSI", "SpineWidthLookup.xlsx")

        dict_of_sheets = pd.read_excel(file_name, sheet_name=None)

        # get the sheet matching sheetname and make it a dataframe with column names "Pages" and "SpineWidth"

        df = dict_of_sheets[sheetname]
        df.columns = ["Pages", "SpineWidth"]

        df["Pages"] = df["Pages"].astype(int)
        df["SpineWidth"] = df["SpineWidth"].astype(float)  # if the page count is not a number, return an error
        finalpagecount = int(finalpagecount)
        effective_page_count = finalpagecount + (finalpagecount % 2)

        if effective_page_count < df["Pages"].min():
            return "Error: page count is less than the smallest page count in the sheet", effective_page_count
        elif effective_page_count > df["Pages"].max():
            return "Error: page count is greater than the largest page count in the sheet", effective_page_count
        elif effective_page_count == df["Pages"].min():
            return df["SpineWidth"].min(), effective_page_count
        elif effective_page_count == df["Pages"].max():
            return df["SpineWidth"].max(), effective_page_count
        else:
            return df.loc[df["Pages"] == effective_page_count, "SpineWidth"].iloc[0], effective_page_count

        # spinewidth = df.loc[df["Pages"] == effective_page_count, "SpineWidth"].iloc[0]

    def save_bookjson_this_book(self, textfilename, bookjson_this_book):
        # validate that bookjson_this_book is valid
        output_json_filename = f"{textfilename}_book.json"
        output_json_path = os.path.join(self.output_dir, output_json_filename)
        os.makedirs(self.output_dir, exist_ok=True)
        try:
            with open(output_json_path, 'w') as f:
                json.dump(bookjson_this_book, f, indent=4)

            logging.info(f"Successfully saved bookjson results at {output_json_path}")
            st.toast(f"Successfully saved bookjson at {output_json_path}")
        except Exception as e:
            print(f"Error saving results to JSON: {traceback.format_exc()}")
            st.error(f"Error saving results to JSON: {traceback.format_exc()}")
            logging.error(f"Error saving results to JSON: {traceback.format_exc()}")
            return

    def save_LSI_metadata_to_ACS_spreadsheet(self, textfilename, metadata_this_row):

        lsi_df = create_LSI_ACS_spreadsheet(metadata_this_row)
        return

    def complete_LSI_metadata(self, textfilename, metadata_this_row):
        """Completes the LSI metadata for a given text file.

        Args:
            textfilename (str): The name of the text file.
            metadata_this_row (Metadatas): The metadata object for the current row.

        Returns:
            Metadatas: The completed metadata object.
        """
        # 1. Load book_json
        bookjson_filepath = os.path.join(self.output_dir, f"{textfilename}_book.json")
        with open(bookjson_filepath, 'r') as f:
            book_json = json.load(f)

        # 2. Extract necessary data from book_json
        metadata_this_row.ISBN = book_json['BookID']
        metadata_this_row.title = book_json['BookTitle']
        metadata_this_row.author = book_json['Byline']
        metadata_this_row['final page count'] = book_json['effective_page_count']

        # 3. Extract/generate other required metadata

        # 3.1 Publication Date
        metadata_this_row['publication date'] = calculate_pub_date()
        print(metadata_this_row['publication date'])

        # 3.2 Annotation/Summary
        metadata_this_row['Annotation / Summary'] = st.session_state.current_plan['gemini_summary']
        # create_draft_book_description(metadata_this_row))

        # 3.3 Keywords
        metadata_this_row = get_LSI_ACS_keywords(metadata_this_row, "Bibliographic Keyword Phrases")

        # 3.4 Audiences

        metadata_this_row['Audience'] = 'General/Trade'  # default
        # 3.4.1  Age and Grade Ranges

        metadata_this_row = calculate_min_max_age_grade(metadata_this_row)

        # 3.5 TLDR
        metadata_this_row['TLDR'] = shorten(metadata_this_row.get_attribute('extractive_summary'), 250)

        # 3.6 Table of Contents
        metadata_this_row['toc'] = process_acrobat_toc(metadata_this_row)

        # 3.7 Color Interior
        metadata_this_row['color_interior'] = book_json.get('color_interior', False)

        # 3.8 Recommended Price (already calculated in book_json)
        metadata_this_row['recommended price'] = book_json['US Suggested List Price']

        # 4. Set file paths (adjust based on your file structure)
        safeISBN = str(metadata_this_row['ISBN'].replace('-', '')[0])
        metadata_this_row['jacket_filepath'] = ''
        metadata_this_row['interior_filepath'] = os.path.join(self.output_dir, f"{safeISBN}_interior.pdf")
        metadata_this_row['cover_filepath'] = os.path.join(self.output_dir, f"{safeISBN}_cover.pdf")

        return metadata_this_row

    def generate_catalog_metadata(self, context: object, row: object) -> object:
        if st.session_state.current_plan["generate_catalog_metadata_for_upload"] or st.session_state.current_plan[
            "generate_catalog_metadata_for_manual_entry"]:
            st.info("creating catalog metadata")
            # should I morph catalog keys here?
            catalog_results = self.process_single_context(context, row)  # now handle Plan
            return catalog_results
