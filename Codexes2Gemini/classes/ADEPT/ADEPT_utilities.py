import glob
import json
import logging
import os
import shutil
import traceback
import uuid
from datetime import datetime

import fitz
import pandas as pd
import streamlit as st

from app.utilities.pdfpagerange2sample import extract_pages_from_pdf
from app.utilities.text2sumy_summarize import chunking_sumy_summarize, sumy_summarize
from app.utilities.utilities import configure_logger
from app.utilities.utilities import make_basename_safe, save_uploaded_file, remove_extension_from_filename
# from classes.ADEPT.ADEPT_headless_multiple_build import autils
from classes.ADEPT.CorePDFProcessor import CorePDFProcessor
from classes.Codexes.Metadata.Metadatas import Metadatas
# from classes.Codexes.Metadata.get_ISBN_from_my_Bowker_file import update_csv
from classes.Codexes.Tools.pdf2pages2df import pdf2text2df
from ..Codexes2Gemini.classes.Codexes.Codexes2PartsOfTheBook import Text2Gemini

logger = configure_logger('debug')


def check_if_number_of_files_less_than_minimum(number_of_files, target_search_path, minimum=1):
    if number_of_files < 1:
        logging.info(f"no PDF files found in directory {target_search_path}")
        exit()
    return


class ADEPTUtilities:

    def __init__(self):
        pass

    def truncate_values(self, dict, length):
        return dict((k, v[:length]) for k, v in dict.items())

    def make_directories(self, output_dir, thisdoc_dir):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        if not os.path.exists(thisdoc_dir):
            os.makedirs(thisdoc_dir)
        if not os.path.exists(output_dir + '/job_results'):
            os.makedirs(output_dir + '/job_results')
        if not os.path.exists(output_dir + '/payservice_results'):
            os.makedirs(output_dir + '/payservice_results')
        if not os.path.exists(output_dir + '/zotero'):
            os.makedirs(output_dir + '/zotero')
        if not os.path.exists('ftp2lsi'):
            os.makedirs('ftp2lsi')
        if not os.path.exists('ftp2lsi/covers'):
            os.makedirs('ftp2lsi/covers')
        if not os.path.exists('ftp2lsi/interiors'):
            os.makedirs('ftp2lsi/interiors')
        return

    def addPDFs2specsfile(self, directory="working/public_domain/today", output_dir="output",
                          single_file_path='/dev/null', files_to_process_limit=100, llama_indexing_on=False,
                          existing_specs_file=None, pages_to_process_limit=10, move_files=True, thisdoc_dir=None):
        scanned_dir = "working/public_domain/scanned_files"
        extension = "*.pdf"
        logging.info(f"move files is {move_files}")
        if not os.path.exists(scanned_dir):
            os.makedirs(scanned_dir)
        logging.info(f'directory to scan is {directory}')
        logging.info(f"llama indexing is {llama_indexing_on}")
        target_search_path = os.path.join(directory, extension)
        target_msg = f"{target_search_path}/{single_file_path}"
        logging.info(target_msg)
        if existing_specs_file is not None:
            exist_msg = f"file {existing_specs_file} exists"
            logging.info(exist_msg)
            try:
                specs_input_df = pd.read_csv(existing_specs_file)
            except Exception as e:
                logging.info("error reading existing_specs_file")
                logging.info(e)
                traceback.print_exc()
        else:
            specs_input_df = pd.DataFrame()
            logging.info(f"newly created specs_input_df is {specs_input_df.head()}")
        if not os.path.exists('output/specs/cumulative_specs_df.csv'):
            cumulative_specs_df = pd.DataFrame()
        else:
            try:
                cumulative_specs_df = pd.read_csv('output/specs/cumulative_specs_df.csv')
                logging.info('read cumulative specs dataframe')
                logging.info(cumulative_specs_df.head())
                # copy cum specs to backup
                backup_specs = cumulative_specs_df.copy()
                backup_specs.to_csv('output/specs/backup_cumulative.csv')

            except Exception as e:
                logging.info("problem reading and backing up cumulative specs")
                traceback.print_exc()
        # set defaults for function as a whole
        specs_add_row_df = pd.DataFrame()
        timestamped_filename = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")
        success, errors = 0, 0
        filecount = 0
        config_file_count = 0
        results = []
        config = {}
        # print(f"specs_input_df shape is {specs_input_df.shape}")

        # set defaults for analysis loop & check whether it is necessary to loop
        logging.info(f"looping over pdfs at path {target_search_path}")
        # print absolute path to target search path

        # list all pdf files in target search path
        list = glob.glob(target_search_path)
        # check if any pdf files were found
        if len(list) == 0:
            logging.error(f"no PDF files found in directory {target_search_path}")
            exit()
        # check if number of pdf files exceeds limit

        number_of_files = len(glob.glob(target_search_path))
        targetmessage = f"looping over {number_of_files} pdfs at path: {target_search_path}"
        print(logging.warning)
        logging.warning(targetmessage)

        statusbox = st.empty()
        statusbox.info(targetmessage)
        logging.warning(targetmessage)

        results_pairs = []
        for filename in glob.glob(target_search_path):
            # process each PDF as follows
            # statusbox.info("📄")
            # sleep(0.5)
            statusbox.info(f"processing {filename} {filecount + 1} of {len(list)}")
            filenamemsg = f"****** filename is {filename} ******"
            print(filenamemsg)
            logging.warning(filenamemsg)
            thisdoc_dir = self.create_scanned_thisdoc_dir(filename)
            metadatas = Metadatas()
            print(f"len metadatas {len(metadatas.keys())}")
            # st.write(metadatas)
            if pages_to_process_limit is not None:
                metadatas.set_attribute('pages_to_process_limit', pages_to_process_limit)
            metadatas.set_attribute('filepath', filename)
            metadatas.set_attribute('thisdoc_dir', thisdoc_dir)

            try:
                metadatas = self.pdf2text_analysis(metadatas, filename)
            except Exception as e:
                # logging.error("error running pdf2text_analysis")
                # logging.error(e)
                print(f"error processing {filename} {filecount + 1} of {len(list)}")
                traceback.print_exc()
                errors += 1
                continue

            print(f"len metadatas is {len(metadatas.keys())}")
            synopsisstring = ''
            system_instruction = "You are an editor working for Nimble Books LLC.  You are thoroughly familiar with every aspect of book publishing and with every market and genre. You have outstanding skills at reading comprension and are excellent at writing accurate, detailed, imaginative prose.  You are completely familiar with the 17th edition of the Chicago Manual of Style. In your communications with the user, you are professional. In your work product, you are accurate, meticulous, and consistent, but you also show wit and flair.  You are industrious, energetic, and proactive. You complete tasks without waiting for approval.\n\nAll responses should be plain text. Separate paragrphs by two returns.  Do not use bolding. Do not use underlining. Do not use header levels. \n\Please review the entire prompt content, from beginning to end, and do the following tasks in batch mode.\n\n- Identify the title of the provided document as a whole. Use title case. \n\n- Identify the author and provide in byline form with uc/lc. \n\n- Summarize the document in at least three paragraphs.  Keep going until you have three paragraphs.\n\n- Write a preface of one paragraph that provides an inspiring and energizing motivation why the reader should buy the book, connecting its content to both current events and fundamental human drives. The result must be valid JSON using this schema: {'gemini_title': 'title', 'gemini_authors': 'authors', 'gemini_summary': 'summary', 'gemini_motivation': 'motivation'}."
            # submit to gemini for summary
            t2g = Text2Gemini()
            gemini_summary_response = t2g.process_text(thisdoc_dir, t2g.model_name, t2g.safety_settings,
                                                       t2g.generation_config,
                                                       metadatas.get_attribute("pages_strings"),
                                                       system_instruction, "")
            logging.debug(gemini_summary_response)
            print(gemini_summary_response.prompt_feedback)
            logging.debug(gemini_summary_response.prompt_feedback)

            filtered_string = gemini_summary_response.text.translate(str.maketrans('', '', '\n\t\r'))

            try:
                gsr_json = json.loads(filtered_string, strict=False)
            except Exception as e:
                logging.errir(f"Error translating gemini text to json: {e}")

            try:
                metadatas.set_attribute('gemini_title', gsr_json["gemini_title"])
                metadatas.set_attribute('gemini_summary', gsr_json["gemini_summary"])
                metadatas.set_attribute('gemini_author', gsr_json["gemini_authors"])
                metadatas.set_attribute('gemini_motivation', gsr_json["gemini_motivation"])
            except Exception as e:
                logging.error("error processing gemini summary")
            logging.debug(metadatas.get_attribute('gemini_motivation'))

            output_file_name = thisdoc_dir + "gemini_output.docx"
            # python save dictionary as docx using pandoc

            metadatas.set_attribute('ISBN', 'TK')

            metadatas_df = pd.DataFrame.from_dict(metadatas.__dict__, orient='index').T
            titlestring = metadatas_df['title'].values[0]
            subtitlestring = metadatas_df['subtitle'].values[0]
            authorstring = metadatas_df['author'].values[0]
            extractive_summary_str = metadatas_df[('extractive_summary')][0]
            keywordstring = metadatas_df['keywords'].values[0]
            motivation = metadatas_df['motivation'].values[0]
            ai_motivation = metadatas.get_attribute('gemini_motivation')

            pagewidthsstring = metadatas_df['page_size_analysis_results'].values[0][0]
            pageheightsstring = metadatas_df['page_size_analysis_results'].values[0][1]
            resizingstring = metadatas_df['page_size_analysis_results'].values[0][2]
            pagecountstring = metadatas_df['page_size_analysis_results'].values[0][3]
            sheetname = metadatas_df['sheetname'].values[0]

            tokensintext = metadatas_df['tokens_in_text'].values[0]

            source = metadatas_df['source'].values[0]
            # read json resource file

            source_text = metadatas.get_attribute("source_text")
            #       print(f"length of metadatas after source text is {len(metadatas.keys())}")
            keywordstring = str(keywordstring)
            shortuuid = str(uuid.uuid4())[:4]
            try:
                specs_add_row_df = pd.DataFrame.from_dict(
                    {'select': False, 'title': gsr_json["gemini_title"], 'subtitle': subtitlestring,
                     'author': gsr_json["gemini_authors"],
                     "motivation": motivation, "ai_motivation": gsr_json["gemini_motivation"], "source": source,
                     'extractive_summary': extractive_summary_str,
                     'Publisher-supplied synopsis': gsr_json["gemini_summary"],
                     'Publisher-supplied Keywords': keywordstring, 'ISBN': 'ISBN TK',
                     'contributing editor': '',
                     'filename': str(filename), 'flags': 'ADEPT, page-by-page-AI',
                     'PDF needs resizing': resizingstring, 'pagewidths': pagewidthsstring,
                     'pageheights': pageheightsstring, 'pagecount': pagecountstring, 'sheetname': sheetname,
                     'tokens in text': tokensintext, 'uuid': shortuuid},
                    orient='index').T
                # specs_add_row_df.fillna('', inplace=True)
                # logging.info("specs_add_row_df: ", specs_add_row_df)
            except Exception as e:
                logging.error("error creating specs_add_row_df")
                logging.error(str(e))
                logging.error(traceback.print_exc())
            # print(f"length of metadatas at results pair is {len(metadatas.keys())}")
            results_pair = {"specs_input_df": specs_add_row_df, "metadatas": metadatas}
            results_pairs.append(results_pair)

            try:
                specs_input_df = pd.concat([specs_input_df, specs_add_row_df], ignore_index=True)
            except Exception as e:
                logging.info("error concatenating specs_input_df")
                logging.info(e)
                traceback.print_exc()
                errors += 1
                continue

            shortuuid = str(uuid.uuid4())[:6]

            try:
                specs_input_df.to_csv(metadatas.get_attribute("thisdoc_dir") + "/specs_" + shortuuid + ".csv",
                                      index=False, header=True)
            except Exception as e:
                logging.info("error writing specs_input_df")
                logging.info(e)

            try:
                metadatas_dict = metadatas.to_dict()
                '''
                save metadatas_dict to a json file
                '''
                json.dump(metadatas_dict, open(thisdoc_dir + "/metadatas.json", "w"), indent=4)
            except Exception as e:
                logging.error(f"error writing metadatas_dict: {e}")

            filecount += 1
            success += 1
            successmessage = f"successfully added {filename} to specs_input_df\n\nfilecount is {filecount} out of {number_of_files} total in directory"
            logging.info(successmessage)

            if move_files:
                self.move_file(filename, scanned_dir)

            if filecount == files_to_process_limit:
                logging.info("reached limit of files to process")
                break

        try:
            cumulative_specs_df = pd.concat([cumulative_specs_df, specs_input_df])
            # drop du
            cdf = cumulative_specs_df.copy()
            cdf_unique = ~cdf.drop('uuid', axis=1).duplicated(keep=False)
            cumulative_specs_df = cdf[cdf_unique]
            cumulative_specs_df.to_csv('output/specs/cumulative_specs_df.csv', index=False)
        except Exception as e:
            logging.info("trouble creating and saving cumulative df")
            traceback.print_exc()

        return results_pairs

    def move_file(self, filename, move_files, scanned_dir):
        basefilename = os.path.basename(filename)
        basefilebase = os.path.splitext(basefilename)[0]
        new_filename = os.path.join(scanned_dir, basefilebase + '.pdf')
        try:
            os.rename(filename, new_filename)
            logging.info(f"Renamed as {new_filename}.")
        except Exception as e:
            "renaming file to {scanned_dir} failed: "
            traceback.print_exc()

    def get_document_sources(self, metadatas, source):
        with open('resources/json/document_sources.json') as f:

            sources = json.load(f)
            try:
                # Iterate over the data and find the sourceText for New York Times
                for item in sources:
                    if item['source'] == source:
                        source_text = item[source]
                        break
                else:
                    source_text = "ad hoc"
                    logging.info("No document source description found, defaulting to ad hoc.")
            except Exception as e:
                logging.info(f"no source description found: {e}")
                source_text = "ad hoc"
            metadatas['source_text'] = source_text
            print(f"len metadatas = {len(metadatas.keys())}")
            return metadatas

    def pdf2text_analysis(self, metadatas, filename):
        # if metadatas.get('pdf2text_analysis_complete'):
        #     return
        pages_to_process_limit = metadatas.get_attribute('pages_to_process_limit')
        thisdoc_dir = metadatas.get_attribute('thisdoc_dir')
        filepath = metadatas.get_attribute('filepath')
        core = CorePDFProcessor(f"{filename}")
        # print(f"filepath, pages_to_process_limit: {pages_to_process_limit}, thisdoc_dir: {thisdoc_dir}")
        try:
            text, text_df, text_extractableness = pdf2text2df(filepath, pages_to_process_limit, thisdoc_dir)
            text_dict = text_df.to_dict()
            # convert text dict to string with page numbers at bottom
            pages_strings = ""
            for page_number, page_text in text_dict.items():
                logging.debug(page_number, page_text)

                page_text_str = json.dumps(page_text)
                pages_strings += "\nPage " + str(page_number) + "\n\n" + page_text_str + "\n\n--------------\n"
            logging.warning(f"length of pages_strings is {len(pages_strings)}")

            # st.write(text_df)
        except Exception as e:
            print("An error occurred while processing the PDF: {str(e)}")
            st.stop()
            # st.write(text_extractableness)
        tokens = core.count_tokens(text)

        print(f"tokens: {tokens}")

        if tokens < 100000:
            try:
                extractive_summary_str = sumy_summarize(text)
                # st.write(extractive_summary_str)
                chunked_extractive_summary_str = ""
            except Exception as e:
                traceback.print_exc()

        else:
            try:
                chunked_extractive_summary_str = ''.join(chunking_sumy_summarize(text, sentences_count=10)[2])

            except Exception as e:
                traceback.print_exc()

        if len(chunked_extractive_summary_str) > 0:
            extractive_summary_str = chunked_extractive_summary_str
            metadatas.set_attributes_to_values({'chunking_extractive_summary': chunked_extractive_summary_str})
        # convert extractive summary list to string
        logging.info(extractive_summary_str)
        extractive_summary_str = ''.join(extractive_summary_str)
        logging.info(extractive_summary_str)

        thisdoc_dir = metadatas.get_attribute('thisdoc_dir')

        metadatas.set_attributes_to_values({'tokens_in_text': tokens})
        metadatas.set_attributes_to_values({'text': text})
        metadatas.set_attributes_to_values({'text_df': text_df})
        metadatas.set_attributes_to_values({'text_dict': text_dict})
        metadatas.set_attributes_to_values({'pages_strings': pages_strings})
        metadatas.set_attributes_to_values({'text_extractableness': text_extractableness})
        metadatas.set_attributes_to_values({'extractive_summary': extractive_summary_str})

        metadatas.set_attributes_to_values({'submit_synopsis': extractive_summary_str})
        pdf_inferred_metadata = core.infer_additional_metadata_about_pdf(metadatas)
        metadatas.set_attributes_to_values({'pdf_inferred_metadata': pdf_inferred_metadata})
        toc = core.get_toc(filepath)
        logging.info("got toc")
        logging.info(toc)
        metadatas.set_attributes_to_values({'toc': toc})
        metadatas = core.metadatas2keywordlists(metadatas, thisdoc_dir)
        pagedimensionslist = core.pdfpagedimensions2list(filepath)
        metadatas.set_attribute('pagedimensionslist', pagedimensionslist)
        page_dimensions_df = pd.DataFrame(pagedimensionslist)
        logging.info(page_dimensions_df.head())

        page_size_analysis_results = core.analyze_page_dimensions_df(page_dimensions_df)
        metadatas.set_attribute('page_size_analysis_results', page_size_analysis_results)
        logging.info(page_size_analysis_results)

        tokens = core.count_tokens(text)
        metadatas.set_attribute('tokens', tokens)
        metadatas = core.pdfnativemetadata(metadatas)
        keylist = ["filepath", "pdf_native_metadata", "toc"]
        metadatas.set_attributes_to_values({'title': metadatas.get_attribute('pdf_native_metadata')['title']})
        metadatas.set_attributes_to_values({'author': metadatas.get_attribute('pdf_native_metadata')['author']})
        metadatas.set_attributes_to_values(
            {'Publisher_supplied_Keywords': metadatas.get_attribute('pdf_native_metadata')['keywords']})
        metadatas.set_attributes_to_values(
            {'Publisher_supplied_synopsis': metadatas.get_attribute('pdf_native_metadata')['subject']})
        metadatas.set_attributes_to_values({'pagecount': metadatas.get_attribute('page_size_analysis_results')[3]})
        # save metadatas to json
        # metadatas_df = pd.DataFrame.from_dict(metadatas, orient="columns")
        # metadatas_df.to_json('output/specs/mdsingle.json', orient="records")
        metadatas.set_attributes_to_values({"pdf2text_analysis_complete": True})
        return metadatas

    def create_motivation(self, metadatas):
        summary = metadatas.get_attribute("submit_synopsis")

        metadatas.set_attributes_to_values({'submit_synopsis': summary})
        t2g = Text2Gemini()
        ai_motivation = t2g.process_text(thisdoc_dir, t2g.model_name, t2g.safety_settings, t2g.generation_config,
                                         mmetadatas.get_attribute("pages_strings"), t2g.system_instruction,
                                         "Write a paragraph explaining how and why this book is important reading. Connect to current issues.")
        logging.info(f"motivation response: {ai_motivation.response.text}")
        st.write(f"Motivation: {ai_motivation.response}")
        metadatas.set_attributes_to_values({'ai_motivation': ai_motivation.response.text})
        return metadatas

    def create_thisdoc_dir(self, filename):
        output_dir = "output/"
        filename_no_extension = remove_extension_from_filename(filename)
        thisdoc_dir = make_basename_safe(os.path.basename(filename_no_extension))
        thisdoc_dir = output_dir + thisdoc_dir
        if not os.path.exists(f"{thisdoc_dir}"):
            os.makedirs(f"{thisdoc_dir}")
        logging.info(f"created thisdoc_dir as {thisdoc_dir}")
        # st.info(f"{thisdoc_dir}")
        return thisdoc_dir

    def create_scanned_thisdoc_dir(self, filename):
        scan_results_dir = "output/scan_results/"
        if not os.path.exists(scan_results_dir):
            os.makedirs(scan_results_dir)
        filename_no_extension = remove_extension_from_filename(filename)
        thisdoc_dir = make_basename_safe(os.path.basename(filename_no_extension))
        thisdoc_dir = scan_results_dir + thisdoc_dir
        if not os.path.exists(f"{thisdoc_dir}"):
            os.makedirs(f"{thisdoc_dir}")
        logging.info(f"created thisdoc_dir as {thisdoc_dir}")
        # st.info(f"{thisdoc_dir}")
        return thisdoc_dir

    def create_built_thisdoc_dir(self, filename):
        built_results_dir = "output/build_results"
        if not os.path.exists(built_results_dir):
            os.makedirs(built_results_dir)
        filename_no_extension = remove_extension_from_filename(filename)
        thisdoc_dir = make_basename_safe(os.path.basename(filename_no_extension))
        thisdoc_dir = os.path.join(built_results_dir, thisdoc_dir)
        if not os.path.exists(f"{thisdoc_dir}"):
            os.makedirs(f"{thisdoc_dir}")
        logging.info(f"created thisdoc_dir as {thisdoc_dir}")
        # st.info(f"{thisdoc_dir}")
        return thisdoc_dir

    @staticmethod
    def check_if_number_of_files_exceeds_limit(self, number_of_files, target_search_path, maxfiles2process=100):
        st.write(number_of_files)
        st.write(maxfiles2process)
        if number_of_files > maxfiles2process:
            print(f"More than 100 files found in directory {target_search_path}")
            print(f"do you want to continue? (y/n)")
            # answer = input()
            answer = "Yes"
            answer2 = st.checkbox("Yes", value=True, key=None, help=None)
            if answer == "Yes" or answer == "yes" or answer == "y" or answer == "Y" or answer2 == True:
                return
            else:
                print("exiting")
                logging.warning("user exited b/c too many files")
                exit()
        return

    def widget_to_upload_file2specsfile(self):
        st.info("Optionally add a new book to the production specs file")
        # UI element for uploading a file
        uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")
        output_dir = "output/"
        # Check if a file was uploaded
        if uploaded_file:
            filename = uploaded_file.name
            thisdoc_dir = os.path.join(self.create_thisdoc_dir(filename))

            if not os.path.exists(f"{thisdoc_dir}"):
                os.makedirs(f"{thisdoc_dir}")
            # gather file details
            file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type,
                            "FileSize": uploaded_file.size}
            st.info(file_details)
            # save file to working directory
            save_uploaded_file(uploaded_file, f"{thisdoc_dir}")
        return

    @staticmethod
    def get_pages_limit_from_PDF(metadatas):
        filename = metadatas.get_attribute('filepath')
        logging.info(f"filename is {filename}")
        pages_to_process_limit = metadatas.get_attribute('pages_to_process_limit')
        thisdoc_dir = metadatas.get_attribute('thisdoc_dir')
        logging.info(f"thisdoc_dir is {thisdoc_dir}")
        logging.info(os.getcwd())
        # lsiust.info(os.getcwd())
        try:
            # Check the number of pages in the document
            doco = fitz.open(filename)
            if pages_to_process_limit < doco.page_count:
                # Extract pages if the limit is less than the total pages
                file_for_processing = extract_pages_from_pdf(filename, f"{thisdoc_dir}/sample.pdf", 1,
                                                             pages_to_process_limit)

                # Copy the original file and the processed file to thisdoc_dir
                shutil.copy(filename, thisdoc_dir)
                # shutil.copy(file_for_processing, thisdoc_dir)

                # Store the file path of the processed file and return it
                metadatas.set_attribute('file for processing', file_for_processing)
                return f"{thisdoc_dir}/sample.pdf"
            else:
                # If the page limit is equal or more than the document's pages, copy the original file only
                shutil.copy(filename, thisdoc_dir)
                return metadatas.get_attribute('filepath')

        except Exception as e:
            # Handle any exceptions that occur during file processing
            logging.info("Error copying files to thisdoc_dir:")
            logging.info(e)
            traceback.print_exc()
            st.error("Error copying files to thisdoc_dir")
            st.write(traceback.print_exc())
            st.stop()

    def override_metadata_with_specs(self, metadatas, row):

        attributes = ['title', 'subtitle', 'author', 'Publisher_supplied_synopsis',
                      'Publisher_supplied_Keywords', 'ISBN', 'contributing editor',
                      'filename', 'source', 'flags', 'tokens_in_text', 'motivation']

        for attr in attributes:
            value = row[attr]
            # check if value is not NaN and not empty
            if pd.notnull(value) and value != '':
                metadatas.set_attributes_to_values({attr: value})
        return metadatas

    def gemini_response2metadatas(self, metadatas, gemini_response):
        gemini_text = gemini_response.text
        metadatas.set_attributes_to_values({"gemini_response": gemini_response})
        metadatas.set_attributes_to_values({"gemini_text": gemini_text})
        return metadatas
