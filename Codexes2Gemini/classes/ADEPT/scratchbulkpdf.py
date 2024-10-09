# TODO make sure presets are receiving submit_sunopsis

# TODO set hard limits on # of API calls of abstractive summarization (5) and number of tokens per call(4000)
# FIXME verify that production specs values such as ISBN, etc. are overwriting defautls

# time the following imports

import argparse
import csv
import datetime
import glob
import json
import logging
import os
import shutil
import statistics
import subprocess
import traceback
import uuid
from collections import OrderedDict
from pathlib import Path
from string import ascii_lowercase

import fitz
import pandas as pd
import streamlit as st
import tiktoken
from isbnlib import desc

from app.utilities.OLD_metadatas_df2distributor_reqts import book_metadata_json2distributor_format_targets, \
    create_LSI_ACS_spreadsheet
# from app.utilities.files2llamaindex import check_if_index_dir_exists, summarize_index, load_or_create_simplevectorindex, load_or_create_gptlistindex, query_simple_vector_index
from app.utilities.gpt3complete import presets_parser, chatcomplete
from app.utilities.metadata2lsicoverspecs import calculate_spinewidth
from app.utilities.metadatas2outputformats import metadatas2docx, metadatas2internationaledition, metadatas2bookjson
from app.utilities.pdf2pages2text import pdf_pages_to_list_of_text_strings
from app.utilities.pdfmetadata2all import (
    pdfmetadata2dict,
    pdfpagedimensions2list,
    analyze_page_dimensions,
    pdfgetlistoftoc
)
from app.utilities.text2DALLE2 import create_DALLE2_images, save_all_DALLE2_images
from app.utilities.text2foreword import create_foreword_in_one_step
from app.utilities.text2isbnmeta import (
    text2goom2isbnmetadict,
)
from app.utilities.text2midjourney_clone import run_midjourney_clone
from app.utilities.text2replicate_model import run_replicate_model
from app.utilities.text2sumy_summarize import chunking_sumy_summarize
from app.utilities.text2unsupervised_keyword_extraction import create_keyword_list_yake
# from app.utilities.text 2extractive_summary import create_extractive_summary_as_list
from app.utilities.texts2match import texts2exactmatch, texts2fuzzymatch, texts2caseinsensitivematch
from app.utilities.utilities import (
    create_safe_dir_from_file_path,
    detect_languages
)

# import ydata_profiling

# print("time to load from app.* --- %s seconds ---" % (time.time() - start_time))
# from app.utilities.text 2simple4jsummarizer import create_extractive_summary_as_list
encoding = tiktoken.get_encoding("p50k_base")
encoding35 = tiktoken.get_encoding(
    "cl100k_base")  # from app.utilities.amazon_paapi_wrapper.is_title_in_kdp import read_title_file, get_product_info, kluge_end
os.chdir("/Users/fred/bin/nimble/unity/")


def bulkprocessPDFs(pdf_directory, output_dir, list2string, cumulative_file_name, limit, profiling, payservices, engine,
                    run_recursive, single_file_path, run_page_by_page, ai_metadata, create_interior_postscript, mode,
                    batch_limit, production_specs_filepath, skip_spec_check=False, skip_llama_entirely=True):
    if single_file_path != '/dev/null':
        print('single file path is ' + single_file_path)
        target_search_path = single_file_path
    else:
        extension = "*.pdf"
        print('pdf_directory', pdf_directory)
        target_search_path = os.path.join(pdf_directory, extension)
    print('target_search_path', target_search_path)
    print('production_specs_filepath', production_specs_filepath)
    cumulative_df = pd.DataFrame()
    specs_input_df = pd.DataFrame()
    specs_add_row_df = pd.DataFrame()

    if mode == "assess":

        create_interior_postscript = False
        run_recursive = False
        ai_metadata = False
        payservices = False
        run_page_by_page = False
        single_file_path = None
        profiling = False
        limit = 10
        print("assessing candidates only")
        production_specs_df = None


    elif mode == "produce":

        create_interior_postscript = False  # True
        run_recursive = True
        ai_metadata = True
        payservices = True
        single_file_path = None
        profiling = False
        text2images_generate_prompts = True
        text2images_generate_images = True
        limit = 1200

        try:
            print('about to read production_specs_filepath', production_specs_filepath)
            # create dataframe by reading file
            # production_specs_df = pd.read_csv(production_specs_filepath)
            production_specs_df = pd.read_csv(production_specs_filepath, encoding='latin1')
            print(f"production specs found at {production_specs_filepath}")
            print(f"first 5 rows are: {production_specs_df.head()}")
            print(f"overriding per-doc settings with production specs")
            selected_for_production = production_specs_df['select'].sum()
            infomessage = f"{selected_for_production} files in production specs file are ready for production"
            st.info(infomessage)  # production_specs_df = pd.DataFrame()
        except Exception as e:
            print('error reading production specs file', e)
            pass

        print(f"mode is {mode} and production_specs_filepath is {production_specs_filepath}")
    timestamped_filename = datetime.datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")

    checkresults = pd.DataFrame()
    print("looping over pdfs at path: ", target_search_path)
    st.write("looping over pdfs at path: ", target_search_path)
    success, errors = 0, 0
    filecount = 0
    config_file_count = 0
    results = []

    config = {}
    # endregion

    number_of_files = len(
        glob.glob(target_search_path))
    print(number_of_files, "files found in directory", target_search_path)

    st.write(f"number of files in directory {target_search_path} is {number_of_files}")
    if number_of_files == 0:
        print(f"no files found in directory {target_search_path}")
        exit()
    if number_of_files >= 101:
        print(f"More than 100 files found in directory {target_search_path}")
        print(f"do you want to continue? (y/n)")
        # answer = input()
        answer = "Yes"
        answer2 = st.checkbox("Yes", value=True, key=None, help=None)

        if answer == "Yes" or answer == "yes" or answer == "y" or answer == "Y" or answer2 == True:
            pass
        else:
            print("exiting")
            exit()

    for filename in glob.glob(target_search_path):  # loop over files in directory

        print("****** filename is ", filename, "*********")
        pathfile = Path(filename)
        shortname = pathfile.with_suffix("")  # check for config file
        config, config_file_count = check_for_config_file(config, config_file_count, shortname)
        # request analysis of current document
        try:

            text2images_generate_prompts = True
            text2images_generate_images = True
            # st.info('before results')
            results = process_pdf(
                filename,
                output_dir,
                limit,
                list2string,
                filecount,
                timestamped_filename,
                payservices,
                config,
                run_recursive,
                run_page_by_page,
                ai_metadata,
                create_interior_postscript,
                mode,
                production_specs_df=production_specs_df,
                text2images_generate_prompts=text2images_generate_prompts,
                text2images_generate_images=text2images_generate_images,
                skip_spec_check=False, skip_llama_entirely=skip_llama_entirely)
            print('results', results)
            st.error('results' + str(results))
            # df_row = pd.DataFrame.from_dict(results[1])  # metadatas
            df_row = results[1]
            # print(df_row, type(df_row))
            df_row['success'] = True
            df_row.to_json(output_dir + "/dfrow.json", orient="records")
            # exit()# st.write('df_row')

            # st.dataframe(df_row.T, width=1000, height=1000)
        except Exception as e:
            df_row = pd.DataFrame()
            df_row['success'] = False
        print('df_row', df_row)

        try:
            titlestring = "foo"  # df_row['title'].values[0]
            subtitlestring = df_row['subtitle'].values[0]
            authorstring = df_row['author'].values[0]
            synopsisstring = df_row['submit synopsis'].values[0]
            # llamastring = df_row['llama_summary'].values[0]
            keywordstring = df_row['keywords'].values[0]
            pagewidthsstring = df_row['pagewidths'].values[0]
            pageheightsstring = df_row['pageheights'].values[0]
            pagecountstring = df_row['pagecount'].values[0]
            tokensintext = df_row['tokens in text'].values[0]
            # source = base path for file name
            source = filename.split('/')[-3] + '/' + filename.split('/')[-2]
            # basesource = top two levels of path

            resizingstring = df_row['pageresizingneeded'].values[0]
            specs_add_row_df = pd.DataFrame.from_dict(
                {'title': titlestring, 'subtitle': subtitlestring, 'author': authorstring,
                 'Publisher-supplied synopsis': synopsisstring, 'llama_summary': llamastring,
                 'Publisher-supplied Keywords': keywordstring, 'ISBN': 'ISBN TK', 'contributing editor': 'Cincinnatus',
                 'filename': str(filename), 'source': source, 'select': False, 'flags': '',
                 'PDF needs resizing': resizingstring, 'pagewidths': pagewidthsstring,
                 'pageheights': pageheightsstring, 'pagecount': pagecountstring, 'tokens in text': tokensintext},
                orient='index').T

            print("specs_add_row_df: ", specs_add_row_df)
            # specs_add_row_df.fillna('', inplace=True).astype(str)
        except Exception as e:
            print("error creating specs_add_row_df")
            print(str(e))
            traceback.print_exc()

        try:
            df_row.to_csv(output_dir + "/dfrow.csv", index=False)
            success += 1
        except Exception as e:
            print("error writing to cumulative_df: " + filename)
            print(e)
            errors += 1

        filecount += 1
        st.write(f"filecount is {filecount}", f"batch_limit is {batch_limit}")
        st.write(f"filename is {filename}")
        print(f"filecount is {filecount} out of {number_of_files} total and batch_limit is {batch_limit}")
        if filecount == batch_limit:
            print("reached limit of files to process")
            break
        # st.write(cumulative_df, df_row)
        try:
            cumulative_df = pd.concat([cumulative_df, df_row])
        except Exception as e:
            print("error concatenating cumulative_df")
            print(e)
            traceback.print_exc()
        try:
            specs_input_df = pd.concat([specs_input_df, specs_add_row_df], ignore_index=True)
        except Exception as e:
            print("error concatenating specs_input_df")
            print(e)
            traceback.print_exc()
    if filecount >= 2:
        # st.write(cumulative_df.columns)
        cumulative_df = cumulative_df.sort_values(
            by=['pageresizingneeded'], ascending=True
        )
        candidates_prioritized_by_ease = cumulative_df[
            cumulative_df['pageresizingneeded'] == False
            ].sort_values(by=['pagecount'], ascending=False)
        # if candidates prioritized by ease is not None and is not empty:
        if not candidates_prioritized_by_ease.empty:
            print("candidates_prioritized_by_ease: ")
            print(candidates_prioritized_by_ease)
            candidates_prioritized_by_ease.to_csv(
                output_dir + "/" + "candidates_prioritized_by_ease.csv")
    else:
        print("less than two files, no need to prioritize easy candidates")

    cumulative_file_name = timestamped_filename
    if not os.path.exists(output_dir + "/" + "job_results"):
        os.mkdir(output_dir + "/" + "job_results")

    cumulative_df.to_csv(
        output_dir + "/" + "job_results" + "/" + cumulative_file_name, index=False
    )

    cumulative_df.to_csv(output_dir + "/" + "cumulative_metadata.csv", index=False)
    print("success: " + str(success), "errors: " + str(errors))
    print("custom config files found: " + str(config_file_count))
    cumulative_df.to_excel(
        output_dir + "/" + "job_results" + "/" + timestamped_filename + ".xlsx",
        index=False,
    )
    cumulative_df.to_json(
        output_dir + "/job_results/" + timestamped_filename + ".json", orient="records"
    )
    distribution_reqts = book_metadata_json2distributor_format_targets()[2]
    # create 4-digit convenience uuid
    shortuuid = str(uuid.uuid4())[:4]
    try:
        specs_input_df.to_csv('output/job_results/' + shortuuid + '_metadata_stub_for_production_specs.csv',
                              index=True, header=True)
    except Exception as e:
        print("error writing specs_input_df")
        print(e)

    exit()


def check_for_config_file(config, config_file_count, shortname):
    # check for custom configuration file
    shortname_config = shortname.with_suffix(".config")
    if os.path.exists(shortname_config):
        config_file = str(shortname_config)
        config_file_count += 1
        print("found config file: ", config_file)
        try:
            with open(config_file) as f:
                config = json.load(f)
                print(config)
                # exit()

        except Exception as e:
            print("error loading config file: " + config_file)
            print(e)
    return config, config_file_count


def truncate_values(dict, length):
    return dict((k, v[:length]) for k, v in dict.items())


def text_df_to_ai_services(text_df, presets=None):
    # def text_df_run_each_row_thru_preset_list
    # print(text_df)
    # st.write(text_df)
    st.write("columns", text_df.columns)
    if presets is None:
        presets = ['page_by_page_batch1']
    print(f"presets passed to text_df_to_ai are {presets}")
    results_for_all_presets = []
    for preset in presets:
        preset_values_df = presets_parser(preset)[0]
        print(preset_values_df)
        print('now looping through pages for this preset')
        responses_archive = []
        page_results_for_current_preset = []
        for index, row in text_df.iterrows():

            if index % 20 == 0:
                st.write("processing page: ", index)
                print("processing page: ", index)
            # st.write(row)
            row_text = row['text']  # page corresponds to row in dataframe
            # st.write(row_text)
            row_text_tokens = len(encoding35.encode(row_text))
            # print("^^^ok to ignore this GPT2 warning ^^^")
            if row_text_tokens < 3000:
                # print("page is ok, less than 3000 token")
                try:
                    response = chatcomplete(preset, row_text, engine, '37')  # send this page off to the AI
                    responses_archive.append(response)
                    result_pair = [index + 1, response[0]['choices'][0]['text']]
                    # st.write(result_pair)
                    page_results_for_current_preset.append(result_pair)
                except Exception as e:
                    errormessage = str(e) + "error in chatcomplete"
                    # st.error(e)
                    print(e)
            else:
                # breaking page into chunks

                row_text_chunks = [row_text[i:i + 3000] for i in range(0, len(row_text), 3000)]
                number_chunks = len(row_text_chunks)
                chunked_page_result = []
                thischunknumber = 1
                for chunk in row_text_chunks:
                    print('this chunk is', thischunknumber, 'of', number_chunks)
                    response = chatcomplete(preset, chunk, engine, '37')
                    responses_archive.append(response)
                    if thischunknumber == 1:
                        chunk_result = [index + 1, response[0]['choices'][0]['message']['content']]
                    else:
                        chunk_result = [index + 1, response[0]['choices'][0]['message']['content']]

                    chunked_page_result.append(chunk_result)

                    thischunknumber += 1
                    # st.write(chunk_result)
                page_results_for_current_preset.append(chunked_page_result)
        results_for_all_presets.append(page_results_for_current_preset)

    # flatten results_for_all_presets into a single list
    results_for_all_presets = [item for sublist in results_for_all_presets for item in sublist]
    return results_for_all_presets


def check_if_titles_are_in_isbnlib(text):
    catalog_results = text2goom2isbnmetadict(text)
    return catalog_results


def process_pdf(filename, output_dir, limit, list2string, filecount, timestamped_filename, payservices, config,
                run_recursively, run_page_by_page, ai_metadata, create_interior_postscript, mode, production_specs_df,
                text2images_generate_prompts, text2images_generate_images, skip_spec_check=False,
                force_payservices=False):
    # setup on right side
    caseinsensitivematch, destination, exactmatch, extractive_summary, extractive_synopsis, fuzzymatch, keywords_text_list, metadatas, pagesize_analysis_results, text, text_extractableness, thisdoc_dir = setup_process_pdf(
        filename, output_dir)
    # echo parameters received
    # put write statements on one line each

    print('filename is', filename, '\n'
          , 'output_dir is', output_dir
          , 'limit is', limit
          , 'list2string is', list2string
          , 'filecount is', filecount
          , 'timestamped_filename is', timestamped_filename

          , 'payservices is', payservices

          , 'config is', config
          , 'run_recursively is', run_recursively
          , 'run_page_by_page is', run_page_by_page
          , 'ai_metadata is', ai_metadata
          , 'create_interior_postscript is', create_interior_postscript
          , 'mode is', mode
          , 'production_specs_df is', production_specs_df
          , 'text2images_generate_prompts is', text2images_generate_prompts
          , 'text2images_generate_images is', text2images_generate_images
          , 'skip_spec_check is', skip_spec_check

          , 'force_payservices is', force_payservices
          )
    # plow on ahead until we see mode == assess, then stop

    metadatas = pdfmetadata2dict(filename)
    working_doc_row = None
    production_specs_df = None
    # if production_specs_df is not None:
    #     # find the row in the production specs that matches this filename
    #     working_doc_row = production_specs_df.loc[production_specs_df['filename'] == filename]
    #     # test if working_doc_row has any content:
    #     if working_doc_row.any().any():
    #         print('found a match in production specs file')
    #
    #     working_doc_row_copy = working_doc_row.copy().fillna('')
    #     #st.write(working_doc_row_copy)
    #     if len(working_doc_row_copy) > 0:
    #         for key2 in working_doc_row_copy.keys():
    #             if key2 != 'filename':
    #                 metadatas[key2] = working_doc_row_copy[key2].values[0]
    #                 print('setting metadata', key2, 'to', working_doc_row_copy[key2].values[0])
    #     else:
    print('no match in production specs file, might as well ignore it')
    production_specs_df = None

    if production_specs_df is None:
        keys = ['subtitle', 'ISBN', 'contributing editor', 'Publisher-supplied Keywords',
                'Publisher-supplied synopsis', 'select', 'source', 'flags']
        # set metadatas to empty strings
        for key in keys:
            metadatas[key] = ''

    metadatas['languages'] = detect_languages(text)
    metadatas['subject'] = ""
    metadatas['color_interior'] = False
    metadatas['mode'] = mode
    metadatas['toc'] = pdfgetlistoftoc(filename)
    metadatas['publisher'] = 'Nimble Books LLC'  # sensible default
    metadatas['imprint'] = 'Nimble Books LLC'  # sensible default
    # convert PDF to text and store in datafram
    text, text_df, text_extractableness = pdf2text2df(filename, limit, text, thisdoc_dir)
    # llama_synopsis = None
    # try:
    #     index_exists = check_if_index_dir_exists(metadatas, thisdoc_dir)
    #     if index_exists:
    #         index_dir = thisdoc_dir + '/index'
    #     metadatas, list_index = load_or_create_gptlistindex(metadatas, thisdoc_dir)
    #     try:
    #         metadatas, llama_response = summarize_index(metadatas, list_index)
    #     except Exception as e:
    #         print(e, 'error is in summarize index')
    #     print(llama_response)
    #     llama_synopsis = llama_response
    # except Exception as e:
    #     print('error in llama summary', e)
    #
    # vector_index_info = load_or_create_simplevectorindex(metadatas, thisdoc_dir)
    # vquestion = "What is this about?"
    # try:
    #     metadatas['vector_response'] = query_simple_vector_index(metadatas, vector_index_info[1], vquestion)
    # except Exception as e:
    #     print(e, 'error is in vector index')

    extractive_summary, extractive_synopsis, sentences_count, submit_synopsis = create_and_save_extractive_summaries(
        text, thisdoc_dir)

    # keyword extraction and deduping
    deduped_keywords, deduped_keywords_with_scores, keywords_text_list = create_and_save_keyword_lists(text,
                                                                                                       thisdoc_dir)

    metadata_extractableness, pagesize_analysis_results = create_page_size_analysis(filename, metadatas,
                                                                                    pagesize_analysis_results)
    # now adding generated metadata to metadatas
    print(metadatas.keys())
    tokens = get_gpt2_token_count(text)
    try:
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
    except Exception as e:
        print('error in adding generated metadata to metadatas', e)

    print('made it to catalog info')
    check_external_catalogs = False
    # print('metadatas are', metadatas)
    metadatas.update(
        metadata2externalcataloginfo(check_external_catalogs, caseinsensitivematch, exactmatch, filename, fuzzymatch,
                                     keywords_text_list,
                                     metadatas,
                                     thisdoc_dir))

    if not metadata_extractableness and not text_extractableness:
        print("unable to analyze file: " + filename)

        print("payservices: ", payservices)
    # finished gathering free info
    # now gathering payservices info
    # if mode = assess, exit function now
    if mode == 'assess':
        print("mode is assess, exiting function")
        # print("metadatas is", metadatas)
        # metadatas['filename'] = str(filename)
        metadatas_df = pd.DataFrame.from_dict([metadatas], orient="columns")

        return metadatas, metadatas_df
    if payservices:
        print("payservices is true")

        # function to send doc to gpt-index

        # test for previous runs of payservcices

        hack = True
        if hack:
            i
            try:
                summary_list = recursive_result[0]
                final_word_count = len(summary_list[-1].split())
                text_word_count = len(text.split())
                methods = f"Extractive summaries and synopsis fed into recursive, abstractive summarizing prompt to large language model.\nReduced word count from {text_word_count} to {final_word_count} words by extracting the {sentences_count} most significant sentences, then looping through that collection in chunks of 2500 tokens for {len(recursive_result[0])} rounds until the number of words in the remaining text fits between the target floor and ceiling.  Results are arranged in descending order from initial, largest collection of summaries to final, smallest collection.\nMachine-generated and unsupervised; use with caution."
                metadatas['Methods'] = methods
            except Exception as e:
                print('error in adding methods info to metadatas ' + filename + '\n' + str(e))
                metadatas['Methods'] = ''

            try:
                metadatas['Foreword'] = create_foreword_in_one_step(
                    metadatas['title'], metadatas['author'], submit_synopsis, thisdoc_dir
                )
            except Exception as e:
                print("error creating foreword" + str(e))
                metadatas['Foreword'] = ""
            ceslug = create_contributing_editor_slug(metadatas)
            metadatas[
                'description_of_annotations'] = f"This book is annotated by Nimble AI and includes a Foreword by {ceslug}; a variety of pithy, opinionated abstracts including scientific style, tldr, tldr one word, Explain It to Me Like I'm Five Years Old, and Action Items; tools for viewpoint diversity such as Dissents, Red Team Critiques, and MAGA Perspectives; a recursive summary with synopsis; page-by-page summaries; and interior art by artist herb.loc['AI']."

            if create_interior_postscript:
                try:
                    # subprocess.run(
                    # ['gs', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4', '-dPDFSETTINGS=/prepress', '-dNOPAUSE',
                    #  '-dQUIET', '-dBATCH', '-sOutputFile=interior_postscript.pdf', 'interior.pdf'])
                    # run ghostscript from command line
                    subprocess.run(
                        ["gs", "-dNOPAUSE", "-dBATCH", "-dQUIET", "-sDEVICE=ps2write", "-sOutputFile=output.ps",
                         filename])

                except Exception as e:
                    print("error creating postscript" + str(e))
                    metadatas['interior_postscript'] = ""

        extractive_summary = metadatas.pop("extractive_summary")
        metadatas['extractive_summary'] = extractive_summary
        if run_page_by_page == True:
            if text_df is not None:

                try:
                    page_by_page_results = text_df_to_ai_services(text_df=text_df, service="openai", presets=[
                        'recursive_summarizer_concise'])  # returns list of lists
                    metadatas['page_by_page_results'] = page_by_page_results
                except Exception as e:
                    metadatas['page_by_page_results'] = []
                    print('Error running page by page' + str(e))
        else:
            metadatas['page_by_page_results'] = ''

        international_edition = False
        if international_edition:
            try:
                international_section = metadatas2internationaledition(metadatas, thisdoc_dir, ['ch'],
                                                                       ['MotivateChineseEdition'], "Global Edition")
                metadatas['international edition name'] = ''
            except Exception as e:
                print("error creating international edition: " + filename + "\n" + str(e))

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

        papercolor = 'White'  # I hate cream
        paperweight = '50'  # by default
        # sheetname = calculate_sheetname(papercolor, color_interior, paperweight, binding, cover_finish )
        sheetname = 'Standard Color 50 Perfect'
        metadatas['service context'] = str(metadatas['service context'])
        try:
            with open(thisdoc_dir + '/test_metadatas.json', 'w') as outfile:
                json.dump(metadatas, outfile)
        except Exception as e:
            print('error writing test_metadatas.json: ' + str(e))
            print(metadatas.keys())

        try:
            checkISBN = str(metadatas['ISBN'])

            if checkISBN.startswith('978'):
                metadatas2docx(metadatas, thisdoc_dir, "LSI")
            else:
                checkISBN = 'TK'
                metadatas2docx(metadatas, thisdoc_dir, "LSI")
            print('successfully created frontmatter')
        except Exception as e:
            print("error creating frontmatter: " + filename + "\n" + str(e))
            print(traceback.format_exc())
            checkISBN = 'TK'
            # print('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))
        try:
            pass
            # backmatter = texts2docx(backparts, "backmatter.docx", thisdoc_dir, ".")
        except Exception as e:
            print("error creating backmatter: " + filename + "\n" + str(e))
        try:
            doc1 = fitz.Document(destination)
            doc1.insert_pdf(fitz.Document(thisdoc_dir + '/frontmatter.pdf'), show_progress=1, start_at=0)
            if checkISBN is not None:
                ftp2lsi_filename = 'ftp2lsi/' + checkISBN + '_interior.pdf'
                doc1.save(ftp2lsi_filename)
            finalpagecount = doc1.page_count
            doc1.close()
            # force final page count to be even
            if finalpagecount % 2 == 1:
                finalpagecount = finalpagecount + 1
            # safety pages
            finalpagecount = finalpagecount + 4
            metadatas['final page count'] = finalpagecount
            metadatas['spinewidth'] = calculate_spinewidth(sheetname, finalpagecount)
            print("successfully saved complete.pdf")
        except Exception as e:
            print("error creating complete pdf including front matter " + str(e))

    # st.write(metadatas)
    bookjson_results = metadatas2bookjson(metadatas, thisdoc_dir)
    # housekeeping: write out previously created result files
    with open(thisdoc_dir + "/" + "pagedimensions.csv", "w") as m:
        # convert list of lists to csv
        writer = csv.writer(m)
        writer.writerows(pdfpagedimensions2list(filename))

    with open(thisdoc_dir + "/" + "extractive_summary.txt", "w") as m:
        m.write(str(extractive_summary))

    with open(thisdoc_dir + "/" + "keywords.json", "w") as m:
        json.dump(metadatas['alpha_sorted_deduped_keywords'], m)

    # now create the master metadatas dataframe
    try:  # creating metadatas_df
        metadatas_df = pd.DataFrame.from_dict([metadatas], orient="columns")
    except Exception as e:
        print("error creating metadatas_df: " + filename + "\n" + str(e))

    # write it as result
    try:
        metadatas_df.to_csv(thisdoc_dir + "/" + "metadatas_df.csv")
        metadatas_df.to_json(thisdoc_dir + "/" + "metadatas_df.json")
    except Exception as e:
        print("error saving metadatas_df: " + filename + "\n" + str(e))

    if payservices:
        book_metadata_objects = book_metadata_json2distributor_format_targets("LST", thisdoc_dir)
        LSI_ACS_required_fields = book_metadata_objects[2]
        LSI_ACS_df = create_LSI_ACS_spreadsheet(metadatas_df, LSI_ACS_required_fields)
        # remove index from LSI_ACS_df
        LSI_ACS_df = LSI_ACS_df.reset_index(drop=True)
        LSI_ACS_df.to_csv(thisdoc_dir + "/" + "LSI_ACS_df.csv", index=False)
        LSI_ACS_df.T.to_csv(thisdoc_dir + "/" + "convenience_LSI_ACS_df.csv", index=False)
        LSI_ACS_df.to_json(thisdoc_dir + "/" + "LSI_ACS.json", orient="records")

        if os.path.exists(output_dir + "/job_results/" + "thisjob_LSI_ACS.csv"):
            # add LSI_ACS_df as row
            LSI_ACS_df.to_csv(output_dir + "/job_results/" + "thisjob_LSI_ACS.csv", mode='a', header=False)
            print("successfully added a row to thisjob_LSI_ACS.csv")
        else:
            LSI_ACS_df.to_csv(output_dir + "/job_results/" + "thisjob_LSI_ACS.csv", index=False)
            print("successfully created thisjob_LSI_ACS.csv")

    return metadatas, metadatas_df  # , LSI_ACS_df


def create_llama_summary(metadatas, thisdoc_dir):
    if check_if_index_dir_exists(metadatas, thisdoc_dir):
        # if dir doesn't exist, will create it
        index_info = load_or_create_gptlistindex(thisdoc_dir)
        index = index_info[0]
        summary = summarize_index(index)
        metadatas['summary_response'] = summary


def create_midjourney_images(metadatas):
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


def create_contributing_editor_slug(metadatas):
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
        print(pagesizemedianwidth, pagesizemedianheight)
        print("pagesize_analysis_results", pagesize_analysis_results)
        metadatas['pageresizingneeded'] = pagesize_analysis_results[2]
        metadatas['pageheights'] = pagesizemedianheight
        metadatas['pagewidths'] = pagesizemedianwidth
        metadata_extractableness = True

    except Exception as e:
        print("can't extract metadata from PDF file: " + filename, e)
        metadata_extractableness = False
    return metadata_extractableness, pagesize_analysis_results


def create_and_save_keyword_lists(text, thisdoc_dir):
    print("starting keyword analysis")
    keywords = create_keyword_list_yake(
        text, calculate_number_of_target_keywords=True
    )

    keywords_text_list = keywords[1]
    deduped_keywords = keywords[2]
    deduped_keywords_with_scores = keywords[3]
    pd.DataFrame(keywords_text_list).to_csv(
        thisdoc_dir + "/" + "keywords.csv", index=False
    )
    # print(deduped_keywords_with_scores)
    deduped_keywords_df = pd.DataFrame(deduped_keywords_with_scores, index=[0])
    deduped_keywords_df.to_json(thisdoc_dir + "/" + "deduped_keywords.json")
    return deduped_keywords, deduped_keywords_with_scores, keywords_text_list


def create_and_save_extractive_summaries(text, thisdoc_dir):
    sentences_count = 20  # default
    try:
        print('starting summary')
        extractive_summary = chunking_sumy_summarize(text, sentences_count)
        extractive_summary_chunks = extractive_summary[1]
        extractive_summary = extractive_summary[0]
        print("starting synopsis", "...")
        extractive_synopsis = chunking_sumy_summarize(text, sentences_count=5)[0]
        extractive_synopsis_chunks = chunking_sumy_summarize(text, sentences_count=5)[1]

    except Exception as e:
        print("error in extractive summary", str(e))
    with open(thisdoc_dir + '/' + 'extractive_summary.txt', 'w') as f:
        f.write(extractive_summary)
    with open(thisdoc_dir + '/' + 'extractive_synopsis.txt', 'w') as f:
        f.write(extractive_synopsis)
    submit_synopsis = extractive_synopsis
    return extractive_summary, extractive_synopsis, sentences_count, submit_synopsis


def pdf2text2df(filename, limit, text, thisdoc_dir):
    try:
        text = pdf_pages_to_list_of_text_strings(filename, limit, output_dir="output")  # text is list of strings
        text_df = pd.DataFrame(text)
        text_df.to_json(thisdoc_dir + "/" + "text.json", orient="records")
        text = " ".join(text)  # text is now a stringls
        # text total word count
        text_word_count = len(text.split())
        with open(thisdoc_dir + "/" + "text.txt", "w") as f:
            f.write(text)
        text_extractableness = True
    except Exception as e:
        print("error converting pdf to text", e)
        text_df = pd.DataFrame()
    return text, text_df, text_extractableness


def setup_process_pdf(filename, output_dir):
    thisdoc_dir = create_safe_dir_from_file_path(filename, output_dir)[0]
    destination = thisdoc_dir + '/' + os.path.basename(filename)
    shutil.copy2(filename, destination)
    text_word_count = 0
    kdp_metadata_df = pd.DataFrame()
    # create ordered dict metadatas
    metadatas = OrderedDict()
    # initialize variables
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
    # create safe filename for each document and corresponding directory
    metadata_csv_file_path = thisdoc_dir + "/" + "metadata.csv"
    return caseinsensitivematch, destination, exactmatch, extractive_summary, extractive_synopsis, fuzzymatch, keywords_text_list, metadatas, pagesize_analysis_results, text, text_extractableness, thisdoc_dir


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


def get_gpt2_token_count(text):
    logging.getLogger("models.gpt2.GPT2TokenizerFast").setLevel(logging.CRITICAL)
    tokens = encoding35.encode(text)
    print('>bulk: created text; # of tokens: ', len(tokens))
    return tokens


def argparse_handler(args=None):
    argparser = argparse.ArgumentParser()

    argparser.add_argument("--limit", help="limit", default=1200)
    argparser.add_argument(
        "--list2string",
        help="output converted text as single string, not a list",
        default=False,
    )

    argparser.add_argument(
        "--pdf_directory",
        help="The directory of the files to be processed",
        default="working/public_domain",
    )
    argparser.add_argument(
        "--output_dir", help="path to output directory", default="output"
    )
    argparser.add_argument("--working_dir", help="working_dir", default="working")
    argparser.add_argument(
        "--cumulative_file_name",
        help="cumulative_file_name",
        default="output/cumulative_metadata.csv",
    )
    argparser.add_argument(
        "--profiling",
        help="create pandas profile report, time consuming",
        default=False,
    )
    argparser.add_argument("--checkamazon", default=False, action="store_true")
    argparser.add_argument("--payservices", default=False, action="store_true")
    argparser.add_argument(
        "--engine", default="gpt-3.5-turbo", help="override preset engine"
    )
    argparser.add_argument("--run-recursive-summarizer", default=False, action="store_true",
                           help="run expensive recursive summarizer")
    argparser.add_argument("--single-file-path", default=None, help="run against just one file")
    argparser.add_argument("--run-page-by-page", default=False, action="store_true",
                           help="run page by page analysis of pdf")
    argparser.add_argument("--ai-metadata", default=False, action="store_true",
                           help="use AI to generate narrative metadata")
    argparser.add_argument("--create-postscript-file", default=False, action="store_true",
                           help="create postscript file for convenience; slow, but faster than Acrobat")
    argparser.add_argument("--mode", default="assess", help="assess, produce")
    argparser.add_argument("--batch-limit", default="5", help="limit number of files to process")
    argparser.add_argument("--production-specs-filepath", default="test/csv/testing_specs.csv", help=
    "path to specific production specs file")
    argparser.add_argument("--add-to-final", default=False, help="add this table to final_LSI_ACS.csv",
                           action="store_true")
    argparser.add_argument("--skip-spec-check", default=False, help="skip checking for production spec",
                           action="store_true")
    argparser.add_argument("--skip-llama-entirely", default=False, help="skip llama entirely")
    args = argparser.parse_args()
    pdf_directory = args.pdf_directory
    limit = args.limit
    skip_spec_check = args.skip_spec_check
    output_dir = args.output_dir
    list2string = args.list2string
    cumulative_file_name = args.cumulative_file_name
    working_dir = args.working_dir
    profiling = args.profiling
    payservices = args.payservices
    run_recursive = args.run_recursive_summarizer
    single_file_path = args.single_file_path
    run_page_by_page = args.run_page_by_page
    ai_metadata = args.ai_metadata
    create_interior_postscript = args.create_postscript_file
    mode = args.mode
    batch_limit = args.batch_limit
    production_specs_filepath = args.production_specs_filepath
    add_to_final = args.add_to_final
    engine = args.engine
    # skip_llama_entirely = args.skip_llama_entirely
    return (
        pdf_directory,
        output_dir,
        list2string,
        cumulative_file_name,
        limit,
        working_dir,
        profiling,
        payservices,
        engine,
        run_recursive,
        single_file_path,
        run_page_by_page,
        ai_metadata,
        create_interior_postscript,
        mode,
        batch_limit,
        production_specs_filepath, add_to_final, skip_llama_entirely
    )


if __name__ == "__main__":

    (
        pdf_directory,
        output_dir,
        list2string,
        cumulative_file_name,
        limit,
        working_dir,
        profiling,
        payservices,
        engine, run_recursive, single_file_path, run_page_by_page, ai_metadata, create_interior_postscript, mode,
        batch_limit, production_specs_filepath, add_to_final, skip_llama_entirely
    ) = argparse_handler()

    # housekeeping

    # check if output directory exists, if not create it
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
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
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)

    # create job direct

    # output_dir + '/' + str(uuid.uuid4()) + cumulative_file_name
    print("pdf directory is " + pdf_directory)
    bulkprocessPDFs(pdf_directory, output_dir, list2string, cumulative_file_name, limit, profiling, payservices, engine,
                    run_recursive, single_file_path, run_page_by_page, ai_metadata, create_interior_postscript, mode,
                    batch_limit, production_specs_filepath, skip_spec_check=False, skip_llama_entirely=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    print("successfully completed at " + str(timestamp))
    # os._exit(0)
