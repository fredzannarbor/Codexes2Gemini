import csv
import json
import logging
import os
import shutil
import statistics
from collections import OrderedDict
from string import ascii_lowercase

import streamlit as st

st.info('initializing')
st.info(os.getcwd())
import pandas as pd
import streamlit as st
from fitz import fitz
from isbnlib import desc

from app.utilities.RecursiveSummarizer import recursively_summarize
from app.utilities.bulkprocesspdfs import create_midjourney_images
from app.utilities.catalog_analysis import check_if_titles_are_in_isbnlib
# from app.utilities.files2llamaindex import check_if_index_dir_exists
from app.utilities.gpt3complete import count_tokens, presets_parser, chatcomplete
from app.utilities.metadata2lsicoverspecs import calculate_spinewidth

from app.utilities.metadatas2outputformats import metadatas2docx
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
from classes.ADEPT.ADEPT_utilities import ADEPT_utilities as au
from classes.Codexes.Metadata import Metadatas


class SinglePDFProcess:
    def __init__(self, filename, pdf_directory, output_dir="output", list2string=False,
                 cumulative_file_name="cumulative_test", page_limit=10, working_dir="working",
                 profiling=False, payservices=True, engine="gpt-3.5-turbo", run_recursive=True,
                 single_file_path="/dev/null", run_page_by_page=False, generate_narrative_metadata=True,
                 create_interior_postscript=False, mode="assess", batch_limit=1,
                 production_specs_filepath="working/traffic_cop/current_specs.csv", add_to_final=True,
                 skip_llama_entirely=True, production_specs_df=None):
        self.filename = filename
        self.pdf_directory = pdf_directory
        self.filepath = self.pdf_directory + "/" + self.filename
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

    # def create_LSI_ACS_metadata(metadatas_df, thisdoc_dir):
    #     if bp.payser
    #     df = LSI_ACS_df.reset_index(drop=True)
    #         LSI_ACS_df.to_csv(thisdoc_dir + "/" + "LSI_ACS_df.csv", index=False)
    #         LSI_ACS_df.T.to_csv(thisdoc_dir + "/" + "convenience_LSI_ACS_df.csv", index=False)
    #         LSI_ACS_df.to_json(thisdoc_dir + "/" + "LSI_ACS.json", orient="records")
    #
    #     book_metadata_objects = book_metadata_json2distributor_format_targets("LST", thisdoc_dir)
    #     LSI_ACS_required_fields = book_metadata_objects[2]
    #     LSI_ACS_df = create_LSI_ACS_spreadsheet(metadatas_df, LSI_ACS_required_fields)
    #     # remove index from LSI_ACS_df
    #     LSI_ACS_df = LSI_ACS_df.reset_index(drop=True)
    #     LSI_ACS_df.to_csv(thisdoc_dir + "/" + "LSI_ACS_df.csv", index=False)
    #     LSI_ACS_df.T.to_csv(thisdoc_dir + "/" + "convenience_LSI_ACS_df.csv", index=False)
    #     LSI_ACS_df.to_json(thisdoc_dir + "/" + "LSI_ACS.json", orient="records")
    #     if os.path.exists(output_dir + "/job_results/" + "thisjob_LSI_ACS.csv"):
    #         # add LSI_ACS_df as row
    #         LSI_ACS_df.to_csv(output_dir + "/job_results/" + "thisjob_LSI_ACS.csv", mode='a', header=False)
    #         print("successfully added a row to thisjob_LSI_ACS.csv")
    #     else:
    #         LSI_ACS_df.to_csv(output_dir + "/job_results/" + "thisjob_LSI_ACS.csv", index=False)
    #         print("successfully created thisjob_LSI_ACS.csv")
    #     return

    def pagebypage2aiservices(self, metadatas, presets=None):
        text_df = metadatas.get_attribute('text_df')
        st.write("text_df", text_df.head())
        st.write("columns", text_df.columns)
        if presets is None:
            presets = ['page_by_page_batch1']
        logging.warning(f"presets passed to text_df_to_ai are {presets}")
        results_for_all_presets = []
        for preset in presets:
            preset_values_df = presets_parser(preset)[0]
            # print(preset_values_df)
            # print('now looping through pages for this preset')
            responses_archive = []
            page_results_for_current_preset = []
            for index, row in text_df.iterrows():

                if index % 20 == 0:
                    index_message = "processing page: " + str(index)
                    smart_print(index_message, both=True)
                # st.write(row)
                row_text = row['text']  # page corresponds to row in dataframe
                # st.write(row_text)
                row_text_tokens = count_tokens(row_text)
                # print("^^^ok to ignore this GPT2 warning ^^^")
                if row_text_tokens < 3000:
                    # print("page is ok, less than 3000 token")
                    try:
                        response = chatcomplete(preset, row_text, "gpt-3.5-turbo")  # send this page off to the AI
                        responses_archive.append(response)
                        result_pair = [index + 1, response[0]['choices'][0]['text']]
                        # st.write(result_pair)
                        page_results_for_current_preset.append(result_pair)
                    except Exception as e:
                        errormessage = str(e) + "error in chatcomplete"
                        # st.error(e)
                        smart_print(errormessage, both=True)
                else:
                    # breaking page into chunks

                    row_text_chunks = [row_text[i:i + 3000] for i in range(0, len(row_text), 3000)]
                    number_chunks = len(row_text_chunks)
                    chunked_page_result = []
                    thischunknumber = 1
                    for chunk in row_text_chunks:
                        chunkmessage = "this chunk is " + str(thischunknumber) + " of " + str(number_chunks)
                        smart_print(chunkmessage, both=True)
                        response_text = chatcomplete(preset, chunk, "gpt-3.5-turbo")
                        responses_archive.append(response_text)
                        if thischunknumber == 1:
                            chunk_result = [index + 1, response_text]
                        else:
                            chunk_result = [index + 1, response_text]

                        chunked_page_result.append(chunk_result)

                        thischunknumber += 1
                        # st.write(chunk_result)
                    page_results_for_current_preset.append(chunked_page_result)
            results_for_all_presets.append(page_results_for_current_preset)

        # flatten results_for_all_presets into a single list
        results_for_all_presets = [item for sublist in results_for_all_presets for item in sublist]
        return results_for_all_presets

    def metadatas2aiservices(self, metadatas, presets=None):
        filename = metadatas.get_attribute('filename')
        thisdoc_dir = metadatas.get_attribute('thisdoc_dir')
        if metadatas.get_attribute('run_recursive'):
            smart_print("running recursive", both=True)
            try:
                submit_synopsis = metadatas.get_attribute('submit_synopsis')
                # print('extractive summary', extractive_summary)
                extractive_result = metadatas.get_attribute('extractive_summary')
                recursive_result = recursively_summarize.loop_until_floor_and_ceiling_satisfied(extractive_result)
                smart_print("recursive_result", recursive_result)
                recursive_synopsis = recursive_result[0][-1]  # second to last result
                tokens_in_recursive_synopsis = count_tokens(recursive_synopsis)
                metadatas.set_attributes_to_values({'recursive_synopsis': recursive_synopsis,
                                                    'recursive_synopsis_tokens': tokens_in_recursive_synopsis,
                                                    'recursive_summary': recursive_result[0],
                                                    'recursive_summary_stats': recursive_result[1]})
            except Exception as e:
                smart_print('error in adding recursive info to metadatas ' + filename + '\n' + str(e))

        else:
            submit_synopsis = metadatas.get_attribute('extractive_synopsis')
            smart_print("using extractive synopsis, no recursive")
        # st.write('metadatas', metadatas)

        # if llama_synopsis is not None:
        #     submit_synopsis = llama_synopsis

        if not metadatas.get_attribute('generate_narrative_metadata'):
            smart_print("not generating narrative metadata using AI", both=True)
        else:
            smart_print('generating narrative metadata using AI', both=True)

        presets_this_run = common_presets_for_metadata()
        presets_token_budget = get_token_counts_for_presets(presets_this_run)
        metadatas.set_attribute('presets token budget', presets_token_budget)
        smart_print('presets_token_budget', presets_token_budget)

        try:
            submit_synopsis = metadatas.get_attribute('submit_synopsis')
            data = create_title_metadata_using_openai(submit_synopsis, thisdoc_dir=thisdoc_dir)
            # metadatas['openai_metadata'] = data
            # print(data, 'data')

            metadatas.set_attributes_to_values({'Suggested Titles': data[0],
                                                'Book Description': data[2],
                                                'Bibliographic Keyword Phrases': data[1],
                                                'Recommended BISAC Categories': data[3],
                                                'Book Cover Blurb': data[4],
                                                'ELI5': data[5],
                                                'TLDR': data[6],
                                                'TLDR (one word)': data[7],
                                                'Formal Dissent': data[8],
                                                'Hostile MAGA Perspective': data[9],
                                                'Red Team Critique': data[10],
                                                'Suggested Action Items': data[11],
                                                'Scientific Style': data[12],
                                                'Cover Illustration Designer': data[13],
                                                'Text2CoverImage Prompt': data[14],
                                                'Text2CoverImage Prompt (Stable Diffusion)': data[15],
                                                'Text2MoodImagePrompt': data[16]})
        except Exception as e:
            smart_print(
                "error in adding openai info to metadatas " + filename + "\n" + str(e)
            )
        return metadatas

    def create_front_matter(filename, metadatas, thisdoc_dir):
        try:
            metadatas2docx(metadatas, thisdoc_dir, "LSI")
        except Exception as e:
            print("error creating frontmatter: " + filename + "\n" + str(e))
        try:
            pass
            # backmatter = texts2docx(backparts, "backmatter.docx", thisdoc_dir, ".")
        except Exception as e:
            print("error creating backmatter: " + filename + "\n" + str(e))
        try:
            destination = thisdoc_dir + '/' + os.path.basename(filename)
            doc1 = fitz.Document(destination)
            doc1.insert_pdf(fitz.Document(thisdoc_dir + '/frontmatter.pdf'), show_progress=1, start_at=0)
            ISBN = metadatas.get_attribute('ISBN')
            if ISBN is not None:
                ftp2lsi_filename = 'ftp2lsi/' + ISBN + '_interior.pdf'
                doc1.save(ftp2lsi_filename)
            finalpagecount = doc1.page_count
            doc1.close()
            # force final page count to be even
            if finalpagecount % 2 == 1:
                finalpagecount = finalpagecount + 1
            # safety pages
            finalpagecount = finalpagecount + 4
            metadatas.set_attribute('final page count', finalpagecount)
            metadatas.set_attribute({'papercolor': 'white', 'paperweight': '50'})
            # sheetname = calculate_sheetname(papercolor, color_interior, paperweight, binding, cover_finish )
            sheetname = 'Standard Color 50# White'
            metadatas.set_attribute('sheetname', sheetname)
            metadatas.set_attribute('spinewidth', calculate_spinewidth(sheetname, finalpagecount))

            print("successfully saved complete.pdf")
        except Exception as e:
            print("error creating complete pdf including front matter " + str(e))
        st.write(metadatas)
        return metadatas

    def print_pdf_process_parameters(ai_metadata, config, create_interior_postscript, filecount, filename,
                                     force_payservices, limit, list2string, mode, output_dir, payservices,
                                     production_specs_df, run_page_by_page, run_recursively, skip_spec_check,
                                     text2images_generate_images, text2images_generate_prompts, timestamped_filename):
        # #print('filename is', filename, '\n'
        #       , 'output_dir is', output_dir
        #       , 'limit is', limit
        #       , 'list2string is', list2string
        #       , 'filecount is', filecount
        #       , 'timestamped_filename is', timestamped_filename
        #
        #       , 'payservices is', payservices
        #
        #       , 'config is', config
        #       , 'run_recursively is', run_recursively
        #       , 'run_page_by_page is', run_page_by_page
        #       , 'ai_metadata is', ai_metadata
        #       , 'create_interior_postscript is', create_interior_postscript
        #       , 'mode is', mode
        #       , 'production_specs_df is', production_specs_df
        #       , 'text2images_generate_prompts is', text2images_generate_prompts
        #       , 'text2images_generate_images is', text2images_generate_images
        #       , 'skip_spec_check is', skip_spec_check
        #
        #       , 'force_payservices is', force_payservices
        #       )
        return

    def create_text2image_prompts_and_images(metadatas, thisdoc_dir):
        print('text2image prompt')
        print(metadatas['Text2CoverImage Prompt'])
        text2images_generate_images = True
        if text2images_generate_images:
            try:
                mj_response_url = create_midjourney_images(metadatas)
            except Exception as e:
                print('error creating midjourney-style images: ' + str(e))
                mj_response = []
            metadatas['midjourney_response'] = str(mj_response_url)

            try:
                DALLE2_response = create_DALLE2_images(metadatas['Text2CoverImage Prompt'][1], n=3,
                                                       dimensions="256x256",
                                                       helicone_proxy=True)
            except Exception as e:
                print('error creating DALLE2 images: ' + str(e))
                DALLE2_response = []
            try:
                save_all_DALLE2_images(DALLE2_response, thisdoc_dir)
            except Exception as e:
                print('error saving DALLE2 images: ' + str(e))
                DALLE2_response = []
            metadatas['DALLE2_response'] = str(DALLE2_response)
        try:
            DALLE2_response = create_DALLE2_images(metadatas['Text2CoverImage Prompt'][1], n=3, dimensions="256x256",
                                                   helicone_proxy=True)
        except Exception as e:
            print('error creating DALLE2 images: ' + str(e))
            DALLE2_response = []
        try:
            save_all_DALLE2_images(DALLE2_response, thisdoc_dir)
        except Exception as e:
            print('error saving DALLE2 images: ' + str(e))
            DALLE2_response = []
        metadatas['DALLE2_response'] = str(DALLE2_response)

        try:
            DALLE2_Mood_response = create_DALLE2_images(metadatas['Text2MoodImagePrompt'][1], n=3, dimensions="256x256",
                                                        helicone_proxy=True)
        except Exception as e:
            print('error creating DALLE2 Mood images: ' + str(e))
            DALLE2_Mood_response = []
            try:
                DALLE2_Mood_response = create_DALLE2_images(metadatas['Text2MoodImagePrompt'][1], n=3,
                                                            dimensions="256x256", helicone_proxy=True)
            except Exception as e:
                print('error creating DALLE2 Mood images: ' + str(e))
                DALLE2_Mood_response = []

        try:
            save_all_DALLE2_images(DALLE2_Mood_response, thisdoc_dir)
        except Exception as e:
            print('error saving DALLE2 Mood images: ' + str(e))
            DALLE2_Mood_response = []
        metadatas['Text2MoodImagePrompt_response'] = DALLE2_Mood_response

        try:
            stable_diffusion_response = run_replicate_model(metadatas['Text2CoverImage Prompt'][1], )
        except Exception as e:
            print('error creating stable diffusion images: ' + str(e))
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
            print("recursive_result", recursive_result)
            recursive_synopsis = recursive_result[0][-1]  # second to last result
            tokens_in_recursive_synopsis = count_tokens(recursive_synopsis)
            metadatas['Recursive Summaries'] = recursive_result[0]
            recursion_stats = recursive_result[1]
            metadatas['Recursive Summarizer Statistics'] = recursion_stats
            metadatas['tokens in recursive_synopsis'] = tokens_in_recursive_synopsis
        except Exception as e:
            print('error in adding recursive info to metadatas ' + filename + '\n' + str(e))
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

    # def run_pdf_through_llama_index(self, thisdoc_dir):
    #     llama_synopsis = None
    #     try:
    #         index_exists = check_if_index_dir_exists(self, thisdoc_dir)
    #         if index_exists:
    #             index_dir = thisdoc_dir + '/index'
    #         self, list_index = load_or_create_gptlistindex(self, thisdoc_dir)
    #         try:
    #             self, llama_response = summarize_index(self, list_index)
    #         except Exception as e:
    #             print(e, 'error is in summarize index')
    #         print(llama_response)
    #         llama_synopsis = llama_response
    #     except Exception as e:
    #         print('error in llama summary', e)
    #     vector_index_info = load_or_create_simplevectorindex(self, thisdoc_dir)
    #     vquestion = "What is this about?"
    #     try:
    #         self['vector_response'] = query_simple_vector_index(self, vector_index_info[1], vquestion)
    #     except Exception as e:
    #         print(e, 'error is in vector index')
    #     return llama_synopsis, self

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
            print("error saving metadatas_df: " + filename + "\n" + str(e))

    def process_production_specs_df(self, metadatas, production_specs_df):
        filename = metadatas.get_attribute('filename')
        if production_specs_df is not None:
            # find the row in the production specs that matches the filename that we're working on
            working_doc_row = production_specs_df.loc[production_specs_df['filename'] == filename]
            # test if working_doc_row has any content:
            if working_doc_row.any().any():
                print('found a match in production specs file')
            # make a copy of the row and fill in any missing cells
            working_doc_row_copy = working_doc_row.copy().fillna('')
            # add any missing metadata from the production specs file to the metadatas dict
            if len(working_doc_row_copy) > 0:
                for key2 in working_doc_row_copy.keys():
                    if key2 != 'filename':
                        metadatas.set_attribute(working_doc_row_copy[key2].values[0])
                        print(f'setting metadata {key2} to working_doc_row_copy[{key2}].values[0]')
        if production_specs_df is None:
            keys = ['subtitle', 'ISBN', 'contributing editor', 'Publisher-supplied Keywords',
                    'Publisher-supplied synopsis', 'select', 'source', 'flags']
            # set metadatas to empty strings
            for key in keys:
                metadatas.set_attribute(key, '')
        return metadatas

        # st.write(metadatas)
        LSI_ACS_df.to_csv(bp.output_dir + "/job_results/" + "thisjob_LSI_ACS.csv", index=False)
        print("successfully created thisjob_LSI_ACS.csv")

        return metadatas, metadatas_df  # , LSI_ACS_df

    # def run_llama_index(llama_synopsis, metadatas, thisdoc_dir):
    #     try:
    #         index_exists = check_if_index_dir_exists(metadatas, thisdoc_dir)
    #         if index_exists:
    #             index_dir = thisdoc_dir + '/index'
    #         metadatas, list_index = load_or_create_gptlistindex(metadatas, thisdoc_dir)
    #         try:
    #             metadatas, llama_response = summarize_index(metadatas, list_index)
    #         except Exception as e:
    #             print(e, 'error is in summarize index')
    #         print(llama_response)
    #         llama_synopsis = llama_response
    #     except Exception as e:
    #         print('error in llama summary', e)
    #     vector_index_info = load_or_create_simplevectorindex(metadatas, thisdoc_dir)
    #     vquestion = "What is this about?"
    #     try:
    #         metadatas['vector_response'] = query_simple_vector_index(metadatas, vector_index_info[1], vquestion)
    #     except Exception as e:
    #         print(e, 'error is in vector index')
    #     return llama_synopsis, metadatas
    #
    # def create_llama_summary(metadatas, thisdoc_dir):
    #     if check_if_index_dir_exists(metadatas, thisdoc_dir):
    #         # if dir doesn't exist, will create it
    #         index_info = load_or_create_gptlistindex(thisdoc_dir)
    #         index = index_info[0]
    #         summary = summarize_index(index)
    #         metadatas['summary_response'] = summary

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
            print('error creating midjourney results' + str(e))
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
            # print(pagesizemedianwidth, pagesizemedianheight)
            # print("pagesize_analysis_results", pagesize_analysis_results)
            metadatas['pageresizingneeded'] = pagesize_analysis_results[2]
            metadatas['pageheights'] = pagesizemedianheight
            metadatas['pagewidths'] = pagesizemedianwidth
            metadata_extractableness = True

        except Exception as e:
            print("can't extract metadata from PDF file: " + filename, e)
            metadata_extractableness = False
        return metadata_extractableness, pagesize_analysis_results

    def metadatas2keywordlists(self, metadatas, thisdoc_dir):

        print("starting keyword analysis")
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
        # print(type(metadatas))
        try:
            print('starting summary')
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
            print("error in extractive summary", str(e))

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
            text = pdf_pages_to_list_of_text_strings(filepath, page_limit,
                                                     output_dir="output")  # text is list of strings
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
            smart_print(error_message, both=True)
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
                print('passing on goom search for now')
            catalog_results_list_of_dicts = {}
            metadatas['goom terms'] = goom_terms
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
                        result_info = result['Title']
                        catalog_titles.append(result['Title'])
                        # stop after 3 results
                        if count >= 2:
                            break
            metadatas['catalog_titles'] = catalog_titles
            # print('catalog titles are: ', catalog_titles)
            similar_titles = []
            if catalog_results_list_of_dicts:
                for l in catalog_results_list_of_dicts:
                    print("l", l)
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
                    # print("item citation", item_citation)
                    similar_titles.append(item_citation)
                similar_titles_candidates = "\n".join(similar_titles)

            else:
                pass
                # metadatas['Similar Titles Research'] = ""
            try:
                for c in catalog_titles:
                    print(metadatas['title'], c)
                    exactmatch = texts2exactmatch(metadatas['title'], c)
                    if exactmatch:
                        flipexactmatch = True
                for c in catalog_titles:
                    # print(metadatas['title'], c)
                    caseinsensitivematch = texts2caseinsensitivematch(metadatas['title'], c)
                    if caseinsensitivematch:
                        break
                for c in catalog_titles:
                    print((metadatas['title'], c))
                    try:
                        fuzzymatch = texts2fuzzymatch(metadatas['title'], c)
                        print("fuzzymatch", fuzzymatch)
                        if fuzzymatch[0]:  # if fuzzymatch is not empty
                            metadatas['fuzzymatch'] = fuzzymatch[0]
                            metadatas['fuzzymatchscore'] = fuzzymatch[1]
                            fuzzymatch = True
                        else:  # if fuzzymatch is empty
                            fuzzymatch = False
                            metadatas['fuzzymatch'] = False
                            metadatas['fuzzymatchscore'] = ""
                    except Exception as e:
                        print("can't calculate fuzzymatch for: " + metadatas['title'] + str(e))
                        metadatas['fuzzymatch'] = ""
                        metadatas['fuzzymatchscore'] = ""


            except Exception as e:
                print("can't connect to catalog: " + filename, e)
            metadatas['exactmatch'] = exactmatch
            metadatas['caseinsensitivematch'] = caseinsensitivematch
            # print(catalog_results_list_of_dicts)
            catalog_results_df = pd.DataFrame(catalog_results_list_of_dicts)
            catalog_results_df.T.to_json(thisdoc_dir + "/" + "isbnlib_matches.json")
            # print('catalog_results_df', catalog_results_df)
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

    def main(sp):
        st.info('entering main')
        st.info(sp.filepath)

        au.make_directories(sp.output_dir, sp.thisdoc_dir)
        # shutil.copy2(sp.filepath, sp.destination)
        st.info(os.getcwd())
        # smart_print("hello wordl")
        filepath = sp.filepath
        # st.info(sp.filepath)
        # st.info(filepath)
        filename = filepath.split("/")[-1]
        if sp.production_specs_df is not None:
            try:
                sp.production_specs_df = pd.read_csv(sp.production_specs_df)
            except Exception as e:
                st.error("can't read production specs csv: " + str(e))
                sp.production_specs_df = None
        production_specs_df = sp.production_specs_df
        metadatas = Metadatas()
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
        metadatas.set_attributes_to_values({'text': text})
        metadatas.set_attributes_to_values({'text_df': text_df})
        metadatas.set_attributes_to_values({'text_extractableness': text_extractableness})
        try:
            native_metadata_from_pdf = pdfmetadata2dict(sp.filepath)
            metadatas.set_attributes_to_values({'pdf_native_metadata': native_metadata_from_pdf})
            metadata_extractableness = True
        except Exception as e:
            st.error("can't extract native metadata from pdf: " + str(e))
            metadata_extractableness = False

        pdf_inferred_metadata = sp.infer_additional_metadata_about_pdf(metadatas)
        metadatas.set_attributes_to_values({'pdf_inferred_metadata': pdf_inferred_metadata})

        toc = pdfgetlistoftoc(filepath)
        metadatas.set_attributes_to_values({'toc': toc})

        production_spec_overides = sp.process_production_specs_df(metadatas, production_specs_df)
        # llama_synopsis, metadatas = self.run_pdf_through_llama_index(metadatas, thisdoc_dir)
        # metadatas.set_attributes_to_values({'llama_synopsis': llama_synopsis})

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
            print("unable to extract metadata or text from " + filepath)
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
