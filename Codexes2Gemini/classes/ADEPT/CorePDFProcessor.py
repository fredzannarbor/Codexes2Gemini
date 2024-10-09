#  Copyright (c) 2023. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com

import csv
import json
import logging
import os
import re
import shutil
import statistics
import traceback
from collections import OrderedDict
from pathlib import Path
from string import ascii_lowercase

import pandas as pd
import streamlit as st
from fitz import fitz
from isbnlib import desc

from app.utilities.RecursiveSummarizer import recursively_summarize
# from app.utilities.bulkprocesspdfs import create_midjourney_images
# from app.utilities.bulkprocesspdfs import create_midjourney_images
from app.utilities.catalog_analysis import check_if_titles_are_in_isbnlib
from app.utilities.gpt3complete import count_tokens, presets_parser, chatcomplete
from app.utilities.metadata2lsicoverspecs import calculate_spinewidth
from app.utilities.pdf2pages2text import pdf_pages_to_list_of_text_strings
from app.utilities.pdfmetadata2all import analyze_page_dimensions, pdfmetadata2dict, pdfgetlistoftoc, \
    pdfpagedimensions2list
from app.utilities.text2DALLE2 import create_DALLE2_images, save_all_DALLE2_images
from app.utilities.text2isbnmeta import text2goom2isbnmetadict
from app.utilities.text2metadata_using_openai import common_presets_for_metadata, get_token_counts_for_presets, \
    create_title_metadata_using_openai
from app.utilities.text2midjourney_clone import run_midjourney_clone
from app.utilities.text2replicate_model import run_replicate_model
from app.utilities.text2sumy_summarize import chunking_sumy_summarize
from app.utilities.text2unsupervised_keyword_extraction import create_keyword_list_yake
from app.utilities.texts2match import texts2fuzzymatch, texts2exactmatch, texts2caseinsensitivematch
from app.utilities.utilities import create_safe_dir_from_file_path, detect_languages, smart_print


class CorePDFProcessor:
    def __init__(self, filename, pdf_directory=".", output_dir="output", list2string=False,
                 cumulative_file_name="cumulative_test", page_limit=10, working_dir="working",
                 profiling=False, payservices=False, engine="gpt-4o", run_recursive=True,
                 single_file_path="/dev/null", run_page_by_page=False, generate_narrative_metadata=True,
                 create_interior_postscript=False, mode="assess", batch_limit=1,
                 production_specs_filepath="resources/sources_of_truth/current_specs.csv", add_to_final=True,
                 skip_llama_entirely=True, production_specs_df=None):
        self.filename = filename
        self.pdf_directory = pdf_directory
        self.filepath = self.filename
        self.output_dir = output_dir
        self.list2string = list2string
        self.cumulative_file_name = cumulative_file_name
        self.page_limit = page_limit
        self.working_dir = working_dir
        self.profiling = profiling
        self.payservices = payservices
        self.engine = engine
        self.run_recursive = run_recursive
        self.single_file_path = single_file_path
        self.run_page_by_page = run_page_by_page
        self.generate_narrative_metadata = generate_narrative_metadata
        self.create_interior_postscript = create_interior_postscript
        self.mode = mode
        self.batch_limit = batch_limit
        self.production_specs_filepath = production_specs_filepath
        self.add_to_final = add_to_final
        self.skip_llama_entirely = skip_llama_entirely
        interim_this_doc = create_safe_dir_from_file_path(filename, output_dir)
        # get first item from tuple interim_this_doc
        self.thisdoc_dir = interim_this_doc[0]
        self.destination = self.thisdoc_dir
        # self.destination = self.output_dir + "/" + thisdoc_dir + '/' + sp.filenamesp.destination = sp.output_dir + "/" + thisdoc_dir + '/' +  sp.filename
        self.text_word_count = 0
        self.kdp_metadata_df = pd.DataFrame()
        self.df_row = pd.DataFrame()
        self.metadata_csv_file_path = self.thisdoc_dir + "/" + "metadata.csv"
        self.production_specs_df = None
        self.run_recursive = True
        self.run_page_by_page = True
        self.generate_narrative_metadata = True

    def list_attributes(self):
        return [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]

    def set_attributes(self, custom_dict):
        for key, value in custom_dict.items():
            setattr(self, key, value)

    def get_attributes(self):
        return {attr: getattr(self, attr) for attr in dir(self) if
                not callable(getattr(self, attr)) and not attr.startswith("__")}

    def set_attribute(self, name, value):
        setattr(self, name, value)

    def get_attribute(self, name):
        return getattr(self, name)

    def get_all_attributes(self):
        return {attr: getattr(self, attr) for attr in dir(self) if
                not callable(getattr(self, attr)) and not attr.startswith("__")}

    def delete_attribute(self, name):
        delattr(self, name)

    def delete_all_attributes(self):
        for attr in dir(self):
            delattr(self, attr)

    def reset_attributes(self):
        self.__init__()

    def update_attribute(self, name, value):
        setattr(self, name, value)

    def report_empty_attributes(self):
        return [attr for attr in dir(self) if
                not callable(getattr(self, attr)) and not attr.startswith("__") and getattr(self, attr) == ""]

    def report_nonempty_attributes(self):
        return [attr for attr in dir(self) if
                not callable(getattr(self, attr)) and not attr.startswith("__") and getattr(self, attr) != ""]

    def check_for_results_cache(self, thisdoc_dir):
        # look to see if thisdoc_dir already contains results_list.json
        results_file_path = Path(thisdoc_dir, "results_list.json")

    def pagebypage2aiservices(self, metadatas, presets=None, model="gpt-4o", temperature=0.5, max_tokens=100):
        text_df = metadatas.get_attribute('text_df')
        thisdoc_dir = metadatas.get_attribute('thisdoc_dir')

        if presets is None:
            presets = ['PageByPageSummary', 'PageByPageNotableQuotes']
        logging.info(f"presets passed to text_df_to_ai are {presets}")
        metadatas.set_attribute('page_by_page_presets', presets)
        results_for_all_presets = []
        results_df = pd.DataFrame()
        for preset in presets:
            preset_values_df = presets_parser(preset)[0]
            responses_archive = []
            page_results_for_current_preset = []
            this_preset_result_dicts = []
            for index, row in text_df.iterrows():
                if index % 20 == 0:
                    index_message = "processing page: " + str(index)
                    logging.info(index_message)
                    st.info(index_message)
                row_text = row['text']  # page corresponds to row in dataframe
                row_text_tokens = count_tokens(row_text)
                # print("^^^ok to ignore this GPT2 warning ^^^")
                if row_text_tokens < 3000:
                    try:
                        response = chatcomplete(preset, row_text, model, temperature,
                                                max_tokens)  # send this page off to the AI
                    except Exception as e:
                        errormessage = str(e) + "error in chatcomplete @168"
                        st.error(e)
                        response = errormessage
                    try:
                        responses_archive.append(response)
                        result_pair = [f"BODY-{index + 1}", response]
                        # result_dict = {index: response['choices'][0]['message']['content']}
                        # st.write(result_pair)
                        this_preset_result_dicts.append(result_pair)
                    except Exception as e:
                        errormessage = str(e) + "error in chatcomplete"
                        # st.error(e)
                        st.error(errormessage)
                else:  # big page with > 3000 tokens
                    # breaking page into chunks
                    row_text_chunks = [row_text[i:i + 3000] for i in range(0, len(row_text), 3000)]
                    number_chunks = len(row_text_chunks)
                    chunked_page_result = []
                    thischunknumber = 1
                    for chunk in row_text_chunks:
                        # st.write("chunk", chunk)
                        chunkmessage = "this chunk is " + str(thischunknumber) + " of " + str(number_chunks)
                        # smart_print(chunkmessage, both=True)
                        logging.info(chunkmessage)

                        try:
                            response = chatcomplete(preset, chunk, model, temperature, max_tokens)
                            # print(response)
                        except Exception as e:
                            errormessage = str(e) + "error in chatcomplete"
                            print(errormessage)
                            logging.info(errormessage)

                        responses_archive.append(response)
                        if thischunknumber == 1:
                            logmsg = str(response)
                            logging.info(logmsg)
                            chunk_result = [f"BODY-{index + 1}", response]
                        else:
                            chunk_result = [f"BODY-{index + 1}", response]
                            chunked_page_result.append(chunk_result)
                        thischunknumber += 1
                        # st.info(chunk_result)
                        page_results_for_current_preset.append(chunk_result)
                    chunked_list_of_lists = [item for sublist in chunked_page_result for item in sublist]
                    chunked_dict = {index: chunked_list_of_lists}
                    this_preset_result_dicts.append(chunked_dict)

                metadatas.set_attribute(preset, this_preset_result_dicts)
                this_preset_result_df = pd.DataFrame(this_preset_result_dicts, columns=[preset, "Text"])
            st.info(f"completed processing all pages with {preset}")
            metadatas.set_attribute(preset, this_preset_result_dicts)
            results_df = pd.concat([this_preset_result_df, results_df], axis=1)
            # results_df = results_df.drop_duplicates()
            results_df.to_csv(thisdoc_dir + "/page_by_page_results_df.csv", index=False)

        results_for_all_presets = [item for sublist in results_for_all_presets for item in sublist]
        metadatas.set_attribute("results for all presets", results_for_all_presets)
        return metadatas

    def metadatas2aiservices(self, metadatas, presets=None, model="gpt-4o", temperature=0.7, verbose=False):
        ''' calls create_title_metadata_using_openai() and returns a metadatas object with the results added as attributes'''
        filename = metadatas.get_attribute('filepath')
        thisdoc_dir = metadatas.get_attribute('thisdoc_dir')
        # st.info(metadatas.get_attribute('run_recursive'))
        # self.run_recursive(metadatas)
        if not metadatas.get_attribute('generate_narrative_metadata'):
            smart_print("not generating narrative metadata using AI", both=True)
        else:
            # smart_print('generating narrative metadata using AI', both=True)
            logging.info(f"generating narrative metadata using AI {model}")
        # st.write("presets", presets)
        if presets is None:
            presets_this_run = common_presets_for_metadata()
        else:
            presets_this_run = presets
        logging.info("presets_this_run", presets_this_run)
        presets_token_budget = get_token_counts_for_presets(presets_this_run)
        metadatas.set_attribute('presets token budget', presets_token_budget)
        logging.info('presets_token_budget {presets_token_budget}')

        try:
            submit_synopsis = metadatas.get_attribute('submit_synopsis')
            # if empty string
            if submit_synopsis == "":
                submit_synopsis = metadatas.get_attribute('extractive_summary')
                submit_synopsis = "Following are the ten most relevant sentences from the document selected by an extractive summarizer.  Base your analysis on what this tells you about the full text of the document.  Restrict your answers to the following portion of the prompt.\n\n" + submit_synopsis
            st.info(f'going to AI with submit_synopsis')
            st.write({submit_synopsis})

            data = create_title_metadata_using_openai(submit_synopsis, thisdoc_dir=thisdoc_dir,
                                                      presets=presets_this_run, model=model, temperature=temperature,
                                                      verbose=verbose)
            st.json(data, expanded=False)
            for item in data:
                metadatas.set_attribute(item[0], item[1])

        except Exception as e:
            metadatas.set_attributes_to_values({'Suggested Titles': 'foo'})
            errormessage = f"error in adding openai results to metadatas object {e}"
            errormessage += traceback.print_exc()
            st.error(errormessage)
            traceback.print_exc()

        return metadatas

    def run_recursive(self, metadatas):
        if metadatas.get_attribute('run_recursive'):
            submit_synopsis = metadatas.get_attribute('submit_synopsis')
            extractive_result = metadatas.get_attribute('extractive_summary')
            st.info("extractive_result", extractive_result)
            recursive_result = recursively_summarize.loop_until_floor_and_ceiling_satisfied(extractive_result)
            st.info('recursive_result', recursive_result)
            recursive_synopsis = recursive_result[0][-1]  # second to last result
            tokens_in_recursive_synopsis = count_tokens(recursive_synopsis)
            metadatas.set_attributes_to_values({'recursive_synopsis': recursive_synopsis,
                                                'recursive_synopsis_tokens': tokens_in_recursive_synopsis,
                                                'recursive_summary': recursive_result[0],
                                                'recursive_summary_stats': recursive_result[1]})
        else:
            submit_synopsis = metadatas.get_attribute('extractive_synopsis')

    # Consider extracting 'metadatas2docx', 'calculate_spinewidth' functions properly if not available globally.

    def create_front_matter(self, filename, metadatas, thisdoc_dir):
        # doc_production_df, document = None, None
        deliverables_target_dir = "output/deliverables/"
        st.write(deliverables_target_dir)
        frontmatterfilename = None

        try:
            # doc_production_df, document = metadatas2docx(metadatas, thisdoc_dir)
            ISBN = metadatas.get_attribute("ISBN")
            if ISBN:
                ISBN_safe = re.sub("-", "_", ISBN)
                frontmatterfilename = f"{ISBN_safe}_frontmatter.docx"
            else:
                frontmatterfilename = f"ISBN_TK_frontmatter.docx"
        except Exception as e:
            logging.error(f"error creating frontmatter tuple in 2docx: {filename}\n{str(e)}")
            traceback.print_exc()

        if not os.path.exists(deliverables_target_dir):
            os.makedirs(f"output/deliverables/{thisdoc_dir}")

        return metadatas

    def merge_front_matter_with_body(self, filename, metadatas, thisdoc_dir, front_matter_file_path):
        try:
            destination = os.path.join(thisdoc_dir, os.path.basename(filename))
            metadatas.set_attribute('destination', destination)
            doc1 = fitz.Document()
            doc1.insert_pdf(fitz.Document(os.path.join(thisdoc_dir, front_matter_file_path)), show_progress=10,
                            start_at=0)
            doc2 = fitz.Document(os.path.join(thisdoc_dir, "footered.pdf"))
            doc2.insert_pdf(doc1, show_progress=10, start_at=0)
            doc2.save(destination)
            ISBN = metadatas.get_attribute('ISBN')
            if ISBN is not None:
                ftp2lsi_filename = 'ftp2lsi/' + ISBN + '_interior.pdf'
                doc1.save(ftp2lsi_filename)
            finalpagecount = doc1.page_count
            doc1.close()
            if finalpagecount % 2 == 1:
                finalpagecount = finalpagecount + 1
            finalpagecount = finalpagecount + 4
            metadatas.set_attribute('final_page_count', finalpagecount)
            metadatas.set_attribute('papercolor', 'white')
            metadatas.set_attribute('paperweight', '50')
            sheetname = 'Standard Color 50 Perfect'
            metadatas.set_attribute('sheetname', sheetname)
            metadatas.set_attribute('spinewidth', calculate_spinewidth(sheetname, finalpagecount))
            logging.info("successfully merged footered pdf and front matter")
        except Exception as e:
            logging.error(traceback.format_exc())
            logging.error(f"error merging front matter and body pdfs {str(e)}")
        return metadatas

    def create_back_matter(self, filename, metadatas, thisdoc_dir):
        metadatas_dict = metadatas.get_all_attributes()
        # 1. collect text data for back matter
        # 2. create Indexes bu entities
        # 3. create notable quotes appendix
        # 4. create bibliography

        return metadatas

    def extract_values(data):
        result = {}
        for key, value in data.items():
            if isinstance(value, dict):
                result[key] = list(value.values())
            else:
                result[key] = [value]
        return result

    def print_pdf_process_parameters(ai_metadata, config, create_interior_postscript, filecount, filename,
                                     force_payservices, limit, list2string, mode, output_dir, payservices,
                                     production_specs_df, run_page_by_page, run_recursively, skip_spec_check,
                                     text2images_generate_images, text2images_generate_prompts, timestamped_filename):
        # log all these parameters using logging.info
        logging.info("ai_metadata" + str(ai_metadata))

        return

    def create_text2image_prompts_and_images(metadatas, thisdoc_dir):
        logging.info('text2image prompt')
        logging.info(metadatas['Text2CoverImage Prompt'])
        text2images_generate_images = True
        if text2images_generate_images:
            try:
                mj_response_url = create_midjourney_images(metadatas)
            except Exception as e:
                logging.error('error creating midjourney-style images: ' + str(e))
                mj_response = []
            metadatas['midjourney_response'] = str(mj_response_url)

            try:
                DALLE2_response = create_DALLE2_images(metadatas['Text2CoverImage Prompt'][1], n=3,
                                                       dimensions="256x256",
                                                       helicone_proxy=True)
            except Exception as e:
                logging.error('error creating DALLE2 images: ' + str(e))
                DALLE2_response = []
            try:
                save_all_DALLE2_images(DALLE2_response, thisdoc_dir)
            except Exception as e:
                logging.error('error saving DALLE2 images: ' + str(e))
                DALLE2_response = []
            metadatas['DALLE2_response'] = str(DALLE2_response)
        try:
            DALLE2_response = create_DALLE2_images(metadatas['Text2CoverImage Prompt'][1], n=3, dimensions="256x256",
                                                   helicone_proxy=True)
        except Exception as e:
            logging.error('error creating DALLE2 images: ' + str(e))
            DALLE2_response = []
        try:
            save_all_DALLE2_images(DALLE2_response, thisdoc_dir)
        except Exception as e:
            logging.error('error saving DALLE2 images: ' + str(e))
            DALLE2_response = []
        metadatas['DALLE2_response'] = str(DALLE2_response)

        try:
            DALLE2_Mood_response = create_DALLE2_images(metadatas['Text2MoodImagePrompt'][1], n=3, dimensions="256x256",
                                                        helicone_proxy=True)
        except Exception as e:
            logging.error('error creating DALLE2 Mood images: ' + str(e))
            DALLE2_Mood_response = []
            try:
                DALLE2_Mood_response = create_DALLE2_images(metadatas['Text2MoodImagePrompt'][1], n=3,
                                                            dimensions="256x256", helicone_proxy=True)
            except Exception as e:
                logging.error('error creating DALLE2 Mood images: ' + str(e))
                DALLE2_Mood_response = []

        try:
            save_all_DALLE2_images(DALLE2_Mood_response, thisdoc_dir)
        except Exception as e:
            logging.error('error saving DALLE2 Mood images: ' + str(e))
            DALLE2_Mood_response = []
        metadatas['Text2MoodImagePrompt_response'] = DALLE2_Mood_response

        try:
            stable_diffusion_response = run_replicate_model(metadatas['Text2CoverImage Prompt'][1], )
        except Exception as e:
            logging.error('error creating stable diffusion images: ' + str(e))
            stable_diffusion_response = []
        return metadatas

    def add_ai_generated_data_to_metadatas(data, metadatas):
        metadatas['Suggested Titles'] = data[0]
        metadatas['Book Description'] = data[2]
        metadatas['Bibliographic Keyword Phrases'] = data[1]
        metadatas['Recommended BISAC Categories'] = data[3]
        metadatas['Book Cover Blurb'] = data[4]
        metadatas['ELI5'] = data[5]
        metadatas['TLDR'] = data[6]
        metadatas['TLDR (one word)'] = data[7]
        metadatas['Formal Dissent'] = data[8]
        metadatas['Hostile MAGA Perspective'] = data[9]
        metadatas['Red Team Critique'] = data[10]
        metadatas['Suggested Action Items'] = data[11]
        metadatas['Scientific Style'] = data[12]
        metadatas['Cover Illustration Designer'] = data[13]
        metadatas['Text2CoverImage Prompt'] = data[14]
        metadatas['Text2CoverImage Prompt (Stable Diffusion)'] = data[15]
        metadatas['Text2MoodImagePrompt'] = data[16]

    def run_recursive_summarizer(extractive_summary, filename, metadatas):
        try:
            # print('extractive summary', extractive_summary)
            recursive_result = recursively_summarize(extractive_summary)
            logging.info("recursive_result", recursive_result)
            recursive_synopsis = recursive_result[0][-1]  # second to last result
            tokens_in_recursive_synopsis = count_tokens(recursive_synopsis)
            metadatas['Recursive Summaries'] = recursive_result[0]
            recursion_stats = recursive_result[1]
            metadatas['Recursive Summarizer Statistics'] = recursion_stats
            metadatas['tokens in recursive_synopsis'] = tokens_in_recursive_synopsis
        except Exception as e:
            logging.error('error in adding recursive info to metadatas ' + filename + '\n' + str(e))
        return recursive_result

    def add_generated_metadata_to_metadatas(deduped_keywords, deduped_keywords_with_scores, extractive_summary,
                                            extractive_synopsis, keywords_text_list, metadata_extractableness,
                                            metadatas,
                                            pagesize_analysis_results, submit_synopsis, text, text_extractableness,
                                            tokens):
        metadatas['tokens in text'] = len(tokens)
        metadatas['text_extractableness'] = text_extractableness
        metadatas['metadata_extractableness'] = metadata_extractableness
        metadatas['keywords'] = "; ".join(keywords_text_list)
        metadatas['deduped_keywords'] = "; ".join(deduped_keywords)
        # force all deduped keywords to lowercase
        converted_deduped_keywords = [x.lower() if x.isupper() else x for x in deduped_keywords]
        metadatas['alpha_sorted_deduped_keywords'] = "; ".join(
            sorted(converted_deduped_keywords, key=lambda x: x[0].lower()
            if x[0].lower() in ascii_lowercase else 'z'))
        metadatas['deduped_keywords_with_scores'] = str(deduped_keywords_with_scores)
        metadatas['extractive_summary'] = extractive_summary
        metadatas['extractive_synopsis'] = extractive_synopsis
        metadatas['submit synopsis'] = submit_synopsis
        metadatas['word length extracted pages'] = len(text.split())
        metadatas['pagecount'] = pagesize_analysis_results[3]

    @staticmethod
    def check_if_index_dir_exists(thisdoc_dir, metadatas):
        """Check if the index directory exists and create it if it doesn't.

        Parameters:
        - thisdoc_dir (str): The directory of the current document.

        Returns:
        - Tuple[Dict[str, Any], bool]: A tuple containing the metadata dictionary and a boolean indicating whether the index directory exists or not.
        """
        index_dir = thisdoc_dir + "/index/"
        if os.path.exists(index_dir):
            logging.info(f'Index directory {index_dir} exists')
            metadatas['index_dir'] = index_dir
            logging.info(f"self['index_dir'] is {metadatas['index_dir']}")
            metadatas['index_dir_status'] = 'Created'
            logging.info(f"self['index_dir_status'] is {metadatas['index_dir_status']}")
            return metadatas, True
        else:
            logging.warning('Index directory does not exist, creating it')
            try:
                os.mkdir(index_dir)
                metadatas['index_dir'] = index_dir
                logging.info(f"self['index_dir'] is {metadatas['index_dir']}")
                metadatas['index_dir_status'] = 'created'
                logging.info(f"self['index_dir_status'] is {metadatas['index_dir_status']}")
            except Exception as e:
                st.error(e)
                metadatas['index_dir'] = str(e)
                metadatas['index_dir_status'] = 'not created'
                logging.info(f"self['index_dir_status'] is {metadatas['index_dir_status']}")
                return metadatas, False
        return metadatas, True

    @staticmethod
    def check_if_text_json_exists(thisdoc_dir):
        """
        Check if the 'text.json' file exists in the specified directory.

        Args:
            thisdoc_dir (str): The directory to check.

        Returns:
            bool: True if the 'text.json' file exists, False otherwise.
        """
        if os.path.exists(thisdoc_dir + '/text.json'):
            logging.info(f'Loading from cached text.json in {thisdoc_dir}')
            try:
                text_json = pd.read_json(thisdoc_dir + '/text.json')
            except Exception as e:
                logging.info("Exception is", e)
                return False
        else:
            logging.info(f'No text.json in {thisdoc_dir}')
            return False
        return True

    def infer_additional_metadata_about_pdf(self, metadatas):
        text = metadatas.get_attribute('text')
        word_count = len(text.split())
        languages = detect_languages(text)
        subject = ''
        color_interior = False
        publisher = 'Nimble Books LLC'  # sensible default
        imprint = 'Nimble Books LLC'  # sensible default
        metadatas.set_attributes_to_values({'word_count': word_count, 'languages': languages, 'subject': subject,
                                            'color_interior': color_interior, 'publisher': publisher,
                                            'imprint': imprint})
        return metadatas

    def check_if_titles_are_in_isbnlib(text):
        catalog_results = text2goom2isbnmetadict(text)
        return catalog_results

    def process_pdf_save_results(self, filename, metadatas, metadatas_df, thisdoc_dir):
        # housekeeping: write out previously created result files
        with open(thisdoc_dir + "/" + "pagedimensions.csv", "w") as m:
            # convert list of lists to csv
            writer = csv.writer(m)
            writer.writerows(pdfpagedimensions2list(filename))
        with open(thisdoc_dir + "/" + "keywords.json", "w") as m:
            json.dump(metadatas['alpha_sorted_deduped_keywords'], m)
        try:
            metadatas_df.to_csv(thisdoc_dir + "/" + "metadatas_df.csv")
            metadatas_df.to_json(thisdoc_dir + "/" + "metadatas_df.json")
        except Exception as e:
            logging.error("error saving metadatas_df: " + filename + "\n" + str(e))

    def process_production_specs_df(self, metadatas, production_specs_df):
        filename = metadatas.get_attribute('filepath')
        specs_matches = ""
        if production_specs_df is not None:
            # find the row in the production specs that matches the filename that we're working on
            working_doc_row = production_specs_df.loc[production_specs_df['filename'] == filename]
            specs_matches = f"{len(working_doc_row)} matches in specs file for {filename}"
            if working_doc_row is None:
                logging.info('no match found in production specs file')
                specs_matches = f"No matching info in specs file for {filename}"
            # test if working_doc_row has any content:
            if working_doc_row.any().any():
                logging.info('found a match in production specs file')
                # make a copy of the row and fill in any missing cells
                working_doc_row_copy = working_doc_row.copy().fillna('')
                # add any missing metadata from the production specs file to the metadatas dict
                specs_matches = f"{len(working_doc_row_copy)}"
                if len(working_doc_row_copy) > 0:
                    specs_matches = f"Found matching info in specs file for {filename}"
                    for key2 in working_doc_row_copy.keys():
                        # logging.info(key2)
                        if key2 != 'filename':
                            metadatas.set_attribute(key2, working_doc_row_copy[key2].values[0])
                            # logging.info(f'setting metadata {key2} to working_doc_row_copy[{key2}].values[0]')
                else:
                    specs_matches = f"length of working row <1 {filename}, there is no matching info in specs file for {filename}"
                    if metadatas.get_attribute('title') is None:
                        native_title = metadatas.pdf_native_metadata.get('title', 'TK')
                        metadatas.set_attribute('title', native_title)
        if production_specs_df is None:
            keys = ['subtitle', 'ISBN', 'contributing editor', 'Publisher-supplied Keywords',
                    'Publisher-supplied synopsis', 'select', 'source', 'flags']
            # set metadatas to empty strings
            for key in keys:
                metadatas.set_attribute(key, '')
            specs_matches = f"No matching info in specs file for {filename}"
        # specs_matches = "foo"
        metadatas.set_attributes_to_values({'specs_matches': specs_matches})
        return metadatas

    def create_midjourney_images(self, metadatas):
        midjourney_style_image = ''
        try:
            midjourney_prompt = metadatas['Text2CoverImage Prompt'][1]
            metadatas['midjourney prompt'] = midjourney_prompt
            midjourney_style_image_url = run_midjourney_clone(
                {"prompt": midjourney_prompt,
                 "negative_prompt": "text",
                 "width": 768,
                 "height": 1024,
                 "prompt_strength": 0.8,
                 "num_outputs": 1,
                 "num_inference_steps": 100,
                 "guidance_scale": 7.5,
                 "scheduler": "DDIM",
                 "seed": 0,
                 "outfilename": "midjourney_style_image.png"})
        except Exception as e:
            logging.error('error creating midjourney results' + str(e))
            metadatas['text2image_results'] = []
        return midjourney_style_image_url

    def create_contributing_editor_slug(self, metadatas):
        if 'contributing editor' in metadatas:
            metadatas['contributing editor slug'] = metadatas['contributing editor']
        else:
            metadatas['contributing editor slug'] = 'an AI on the Nimble Books staff'
        ce_slug = metadatas['contributing editor slug']
        return ce_slug

    def create_page_size_analysis(filename, metadatas, pagesize_analysis_results):
        try:
            pagedimensionslist = pdfpagedimensions2list(filename)
            pagesize_analysis_results = analyze_page_dimensions(pagedimensionslist)
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
            # logging.info(pagesizemedianwidth, pagesizemedianheight)
            # logging.info("pagesize_analysis_results", pagesize_analysis_results)
            metadatas['pageresizingneeded'] = pagesize_analysis_results[2]
            metadatas['pageheights'] = pagesizemedianheight
            metadatas['pagewidths'] = pagesizemedianwidth
            metadata_extractableness = True

        except Exception as e:
            logging.error("can't extract metadata from PDF file: " + filename, e)
            metadata_extractableness = False
        return metadata_extractableness, pagesize_analysis_results

    def metadatas2keywordlists(self, metadatas, thisdoc_dir):

        logging.info("starting keyword analysis")
        text = metadatas.get_attribute("text")
        keyword_results = create_keyword_list_yake(
            text, calculate_number_of_target_keywords=True
        )
        metadatas.set_attributes_to_values({"keywords": keyword_results[0], "keywords_text_list": keyword_results[1],
                                            "deduped_keywords": str(keyword_results[2]),
                                            "deduped_keywords_with_scores": keyword_results[3]})
        # print(type(thisdoc_dir))
        pd.DataFrame(keyword_results[1]).to_csv(
            thisdoc_dir + "/" + "keywords.csv", index=False
        )
        # print(deduped_keywords_with_scores)
        deduped_keywords_df = pd.DataFrame(keyword_results[3], index=[0])
        deduped_keywords_df.to_json(thisdoc_dir + "/" + "deduped_keywords.json")
        return metadatas

    def create_and_save_extractive_summaries(self, metadatas, thisdoc_dir):
        sentences_count = 20  # default
        # logging.info(type(metadatas))
        try:
            logging.info('starting summary')
            text = metadatas.get_attribute('text')
            summarizingmsg = "Summarizing " + str(len(text)) + " characters of text"
            smart_print(summarizingmsg, both=True)
            extractive_summary = chunking_sumy_summarize(text, sentences_count)
            extractive_summary_chunks = extractive_summary[1]
            extractive_summary = extractive_summary[0]
            smart_print("starting synopsis", both=True)
            extractive_synopsis = chunking_sumy_summarize(text, sentences_count=5)[0]
            extractive_synopsis_chunks = chunking_sumy_summarize(text, sentences_count=5)[1]

        except Exception as e:
            logging.error("error in extractive summary", str(e))

        with open(thisdoc_dir + '/' + 'extractive_summary.txt', 'w') as f:
            f.write(extractive_summary)
        with open(thisdoc_dir + '/' + 'extractive_synopsis.txt', 'w') as f:
            f.write(extractive_synopsis)
        submit_synopsis = extractive_synopsis
        metadatas.set_attributes_to_values(
            {'extractive_summary': extractive_summary, 'extractive_synopsis': extractive_synopsis,
             'sentences_count': sentences_count, 'submit_synopsis': submit_synopsis})
        return metadatas

    def pdf2text2df(self, filepath, page_limit, thisdoc_dir):
        text = ""
        try:
            text = pdf_pages_to_list_of_text_strings(filepath, page_limit, thisdoc_dir)  # text is list of strings
            text_df = pd.DataFrame(text, columns=["text"])
            text_df.to_json(thisdoc_dir + "/" + "text.json", orient="records")
            text = " ".join(text)  # text is now a string
            # text total word count
            text_word_count = len(text.split())
            logging.warning("text word count is " + str(text_word_count))
            with open(thisdoc_dir + "/" + "text.txt", "w") as f:
                f.write(text)
            text_extractableness = True
        except Exception as e:
            error_message = "can't extract text from PDF file: " + filepath + str(e)
            logging.error(error_message)
            text = ""
            text_df = pd.DataFrame()
        return text, text_df, text_extractableness

    def setup_process_pdf(filepath, output_dir):
        thisdoc_dir = create_safe_dir_from_file_path(filepath, output_dir)[0]
        destination = thisdoc_dir + '/' + os.path.basename(filepath)
        shutil.copy2(filepath, destination)
        text_word_count = 0
        kdp_metadata_df = pd.DataFrame()
        # create ordered dict metadatas
        metadatas = OrderedDict()
        # initialize variables
        df_row = pd.DataFrame()
        smart_print("starting process_pdf", "...")
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
        # create safe filename for each document and corresponding directory
        metadata_csv_file_path = thisdoc_dir + "/" + "metadata.csv"
        setup_variables = thisdoc_dir, destination, text_word_count, kdp_metadata_df, df_row, text_extractableness, metadata_extractableness, pagesizeanalysis, text, keywords, keywords_text, keywords_text_list, extractive_summary, extractive_summary2df, extractive_synopsis, deduped_keywords, deduped_keywords_with_scores, exactmatch, fuzzymatch, caseinsensitivematch, pagesize_analysis_results, synopsisplus, submit_synopsis, metadata_csv_file_path
        return setup_variables

    def metadata2externalcataloginfo(check_external_catalogs, caseinsensitivematch, exactmatch, filename, fuzzymatch,
                                     keywords_text_list, metadatas,
                                     thisdoc_dir):
        if check_external_catalogs == False:
            return {'catalog_titles': None,
                    'catalog_description': None,
                    'similar titles found by isbnlib': None,
                    'goom terms': None,
                    'fuzzymatchscore': None,
                    'caseinsensitivematch': None,
                    'exactmatch': None,
                    'catalogs_checked': False}

        else:
            # catalog lookup begins here
            # decide how to search for title matches
            # if there is no title, author or subject, use keywords
            if (
                    metadatas['title'] == ""
                    and metadatas['author'] == ""
                    and metadatas['subject'] == ""
            ):
                goom_terms = " ".join(keywords_text_list[0:4])

                # else use title + author + subject
            else:
                goom_terms = ""
                logging.info('passing on goom search for now')
            catalog_results_list_of_dicts = {}
            metadatas['goom terms'] = goom_terms
            try:
                catalog_results_list_of_dicts = check_if_titles_are_in_isbnlib(goom_terms)
                # metadatas['catalog_results_list_of_dicts'] = catalog_results_list_of_dicts
            except Exception as e:
                logging.error("error submitting goom terms to isbnlib: " + str(e))
            # go through similar books found in catalog and save three titles
            catalog_titles = []
            if catalog_results_list_of_dicts != []:
                for count, result in enumerate(catalog_results_list_of_dicts):
                    if result is not None:  # get title from catalog result
                        result_info = result['Title']
                        catalog_titles.append(result['Title'])
                        # stop after 3 results
                        if count >= 2:
                            break
            metadatas['catalog_titles'] = catalog_titles
            # logging.info('catalog titles are: ', catalog_titles)
            similar_titles = []
            if catalog_results_list_of_dicts:
                for l in catalog_results_list_of_dicts:
                    logging.info("l", l)
                    authors = ", ".join(l['Authors'])
                    item_citation = (
                            l['Title'][0]
                            + ". "
                            + authors
                            + ". "
                            + l['Publisher'][0]
                            + ": "
                            + l['Year'][0]
                            + "\n"
                            + l['ISBN-13'][0]
                            + "."
                            + "\nDescription: "
                            + desc(l['ISBN-13'][0])
                    )
                    # logging.info("item citation", item_citation)
                    similar_titles.append(item_citation)
                similar_titles_candidates = "\n".join(similar_titles)

            else:
                pass
                # metadatas['Similar Titles Research'] = ""
            try:
                for c in catalog_titles:
                    logging.info(metadatas['title'], c)
                    exactmatch = texts2exactmatch(metadatas['title'], c)
                    if exactmatch:
                        flipexactmatch = True
                for c in catalog_titles:
                    # logging.info(metadatas['title'], c)
                    caseinsensitivematch = texts2caseinsensitivematch(metadatas['title'], c)
                    if caseinsensitivematch:
                        break
                for c in catalog_titles:
                    logging.info((metadatas['title'], c))
                    try:
                        fuzzymatch = texts2fuzzymatch(metadatas['title'], c)
                        logging.info("fuzzymatch", fuzzymatch)
                        if fuzzymatch[0]:  # if fuzzymatch is not empty
                            metadatas['fuzzymatch'] = fuzzymatch[0]
                            metadatas['fuzzymatchscore'] = fuzzymatch[1]
                            fuzzymatch = True
                        else:  # if fuzzymatch is empty
                            fuzzymatch = False
                            metadatas['fuzzymatch'] = False
                            metadatas['fuzzymatchscore'] = ""
                    except Exception as e:
                        logging.warning("can't calculate fuzzymatch for: " + metadatas['title'] + str(e))
                        metadatas['fuzzymatch'] = ""
                        metadatas['fuzzymatchscore'] = ""


            except Exception as e:
                logging.error("can't connect to catalog: " + filename, e)
            metadatas['exactmatch'] = exactmatch
            metadatas['caseinsensitivematch'] = caseinsensitivematch
            # logging.info(catalog_results_list_of_dicts)
            catalog_results_df = pd.DataFrame(catalog_results_list_of_dicts)
            catalog_results_df.T.to_json(thisdoc_dir + "/" + "isbnlib_matches.json")
            # logging.info('catalog_results_df', catalog_results_df)
            metadatas['similar titles found by isbnlib'] = str(catalog_titles)
            # metadatas['catalog_series'] = catalog_series
            if exactmatch or caseinsensitivematch or fuzzymatch:
                metadescription = desc(metadatas['catalog_titles'][0])
                metadatas['catalog_description'] = metadescription
                with open(thisdoc_dir + "/" + "metadescription.json", "w") as f:
                    json.dump(metadescription, f)

            else:
                metadatas['catalog_description'] = ""

            # return only metadata keys specifically created in this function
            return {
                'exactmatch': exactmatch,
                'caseinsensitivematch': caseinsensitivematch,
                'fuzzymatch': fuzzymatch,
                'fuzzymatchscore': metadatas['fuzzymatchscore'],
                'catalog_titles': catalog_titles,
                'catalog_description': metadatas['catalog_description'],
                'similar titles found by isbnlib': metadatas['similar titles found by isbnlib'],
                'goom terms': goom_terms,
                'catalog_results_list_of_dicts': catalog_results_list_of_dicts,
                'checked_catalogs': True
            }

    @staticmethod
    def get_toc(filepath):
        toc = []
        try:
            toc = pdfgetlistoftoc(filepath)
        except Exception as e:
            logging.warning("can't extract toc from pdf: " + str(e))
        return toc

    @staticmethod
    def pdfpagedimensions2list(filepath):
        pagedimensionslist = []
        try:
            pagedimensionslist = pdfpagedimensions2list(filepath)
        except Exception as e:
            logging.warning("can't extract page dimensions from pdf: " + str(e))
        return pagedimensionslist

    @staticmethod
    def analyze_page_dimensions_df(page_dimensions_df):

        heightsallequal, widthsallequal, pageresizingneeded = False, False, False
        unique_heights = page_dimensions_df[2].nunique()
        # If this number is 1, then all values are the same
        heightsallequal = (unique_heights == 1)
        unique_widths = page_dimensions_df[3].nunique()
        widthsallequal = (unique_widths == 1)
        pageresizingneeded = not (heightsallequal and widthsallequal)
        pagecount = len(page_dimensions_df)
        logging.info(f"Number of pages: {pagecount}")
        logging.info(f"Number of unique heights: {unique_heights}")
        logging.info(f"Number of unique widths: {unique_widths}")
        logging.info(f"Page resizing needed: {pageresizingneeded}")
        return heightsallequal, widthsallequal, pageresizingneeded, pagecount

    @staticmethod
    def count_tokens(text):
        tokens = []
        try:
            tokens = count_tokens(text)
        except Exception as e:
            logging.error("can't count tokens: " + str(e))
        return tokens

    def main(sp):

        os.makedirs(sp.output_dir)
        os.makedirs(sp.thisdoc_dir)
        # shutil.copy2(sp.filepath, sp.destination)

        filepath = sp.filepath

        filename = filepath.split("/")[-1]
        production_specs_df = sp.read_production_specs_df()
        # metadatas = Metadatas()
        sp2metadatas = sp.get_all_attributes()
        metadatas.set_attributes_to_values(sp2metadatas)
        filename = sp.filename

        thisdoc_dir = sp.thisdoc_dir

        try:
            text, text_df, text_extractableness = sp.pdf2text2df(
                filepath,
                page_limit=10,
                thisdoc_dir=sp.thisdoc_dir)
        except Exception as e:
            st.write(os.getcwd())
            st.error("can't extract text from pdf: " + str(e))
            text_extractableness = False

        metadata_extractableness = sp.pdfnativemetadata(metadatas)

        pdf_inferred_metadata = sp.infer_additional_metadata_about_pdf(metadatas)
        metadatas.set_attributes_to_values({'pdf_inferred_metadata': pdf_inferred_metadata})

        toc = pdfgetlistoftoc(filepath)
        metadatas.set_attributes_to_values({'toc': toc})

        production_spec_overides = sp.process_production_specs_df(metadatas, production_specs_df)

        metadatas = sp.create_and_save_extractive_summaries(metadatas, sp.output_dir)
        metadatas = sp.metadatas2keywordlists(metadatas, thisdoc_dir)
        pagedimensionslist = pdfpagedimensions2list(filepath)
        metadatas.set_attribute('pagedimensionslist', pagedimensionslist)
        page_size_analysis_results = analyze_page_dimensions(pagedimensionslist)
        metadatas.set_attribute('page_size_analysis_results', page_size_analysis_results)

        tokens = count_tokens(text)
        metadatas.set_attribute('tokens', tokens)
        st.info(tokens)
        check_external_catalogs = False

        if not metadata_extractableness and not text_extractableness:
            logging.error("unable to extract metadata or text from " + filepath)
            smart_print("unable to extract metadata or text from " + filepath)
            exit()

        sp.set_attribute('mode', 'produce')
        if sp.mode == 'assess':
            st.info("mode is assess, exiting function")
            metadatas_df = pd.DataFrame.from_dict([metadatas], orient="columns")
            return metadatas, metadatas_df
        elif sp.mode == 'produce':
            st.info("mode is produce, continuing")
        else:
            raise Exception("mode must be assess or produce", 'exiting')

        if sp.payservices:
            metadatas = sp.metadatas2aiservices(metadatas)

        if sp.run_page_by_page and text_extractableness:
            pass
            # metadatas = sp.metadatas2p

        # if sp.international_edition:
        # metadatas = sp.metadatas2international_edition(metadatas)

        # all book content assembled

        metadatas_attributes = metadatas.get_all_attributes()
        # replace bojects that are dataframes with string placeholder
        for k, v in metadatas_attributes.items():
            if isinstance(v, pd.DataFrame):
                metadatas_attributes[k] = "dataframe"
        for k, v in metadatas_attributes.items():
            if isinstance(v, object):
                metadatas_attributes[k] = str(v)
        st.write(metadatas_attributes)
        with open(thisdoc_dir + "/" + "metadatas.txt", "w") as f:
            f.write(str(metadatas_attributes))
        with open(thisdoc_dir + "/" + "metadatas.json", "w") as f:
            json.dump(metadatas_attributes, f)

    @staticmethod
    def pdfnativemetadata(metadatas):
        try:
            native_metadata_from_pdf = pdfmetadata2dict(metadatas.filepath)
            metadatas.set_attributes_to_values({'pdf_native_metadata': native_metadata_from_pdf})
            metadatas.set_attributes_to_values({'metadata_extractableness': True})
        except Exception as e:
            st.error("can't extract native metadata from pdf: " + str(e))
            metadatas.set_attributes_to_values({'metadata_extractableness': True})
        return metadatas

    def read_production_specs_df(self, production_specs_df):
        if production_specs_df is not None:
            try:
                production_specs_df = pd.read_csv(production_specs_df)
            except Exception as e:
                st.error("can't read production specs csv: " + str(e))
                production_specs_df = None
                st.stop()
        else:
            st.error("production_specs_df is None, need to create one")
            production_specs_df = self.create_new_production_specs_df()
        return production_specs_df

    def create_new_production_specs_df(self):
        production_specs_df_columns = ["select", "title", "subtitle", "author", "motivation",
                                       "Publisher-supplied synopsis", "Publisher-supplied Keywords" "ISBN",
                                       "contributing editor", "filename",
                                       "fully_built", "source", "flags", "pageresizingneeded"]
        production_specs_df = pd.DataFrame(columns=production_specs_df_columns)
        return production_specs_df

    def save_production_specs_df(self, production_specs_df, specs_filepath):
        production_specs_df.to_csv(specs_filepath)

    def incorporate_page_by_page_results(self, metadatas):

        print("no page by page results found to incorporate in front matter")
        return

    def update_specs_df_with_algorithmic_info(self, production_specs_df, metadatas):
        metadatas = metadatas.get_all_attributes()
        if production_specs_df is None:
            st.error("production_specs_df is None, need to create one")
            st.stop()
        else:
            specs_df_columns = ["select", "title", "subtitle", "author", "Publisher-supplied Keywords",
                                "Publisher-supplied synopsis", "ISBN", "contributing editor", "filename", "fully_built",
                                "source", "flags", "pageresizingneeded"]
            new_specs_row = {
                "select": False,
                "title": metadatas['title'],
                "subtitle": metadatas['subtitle'],
                "author": metadatas['author'],
                "Publisher-supplied Keywords": str(metadatas['keywords']),
                "Publisher-supplied synopsis": "",
                "ISBN": "",
                "contributing editor": "",
                "filename": metadatas['filepath'],
                "fully_built": False,
                "source": "self-help form",
                "flags": "P",
                "pageresizingneeded": metadatas['pageresizingneeded']
            }
            # if title is empty
            if metadatas['title'] == "":
                # use filename as title
                # take basneame first
                new_specs_row['title'] = os.path.basename(metadatas['filepath'])
                # new_specs_row['title'] = metadatas['filepath']
            if metadatas['subtitle'] == "":
                new_specs_row['subtitle'] = "TBD"

            new_specs_df = pd.DataFrame.from_dict(new_specs_row, orient="index").T
            st.write('new_specs_df', new_specs_df)

            production_specs_df = pd.concat([production_specs_df, new_specs_df])
            production_specs_df.to_csv(self.production_specs_df)
            # metadatas is unchanged
            return production_specs_df

    def close(self):
        del self
