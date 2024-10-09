import os
from pathlib import Path

import fitz
import pandas as pd
import streamlit as st
from llama_index import StorageContext, load_index_from_storage
from llama_index import download_loader, ServiceContext, SummaryIndex, PromptHelper
from llama_index.llms import OpenAI
from llama_index.memory import ChatMemoryBuffer

import classes.Codexes.Metadata.Metadatas as Metadatas

memory = ChatMemoryBuffer.from_defaults(token_limit=3900)

from classes.ADEPT.CorePDFProcessor import CorePDFProcessor
from app.utilities.text2metadata_using_openai import common_presets_for_metadata
from app.utilities.utilities import save_uploaded_file, make_basename_safe, get_environment_variables, \
    get_version_as_dict
from streamlit_extras.let_it_rain import rain

import logging

# show tracebacks for any error messagess
logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger('nimble')

st.set_page_config(layout="wide")
with st.expander("Debugging info"):
    OPENAI_API_BASE = os.environ["OPENAI_API_BASE"]
    st.info(OPENAI_API_BASE)
    st.info(os.path.abspath(os.getcwd()))
    st.write(get_environment_variables())
    st.write(get_version_as_dict())

from app.utilities.pdfpagerange2sample import extract_pages_from_pdf

from app.utilities.metadatas2outputformats import metadatas2bookjson

st.title("ADEPT Self-Serve")
st.header("Single File Processing")

thisdoc_dir = "output/foo"

with st.expander("Documents ready for processing (specs_df)"):
    # select a production specs file
    specs_available = ["resources/sources_of_truth/current_specs.csv",
                       "/Users/fred/bin/nimble/bookpublisherGPT/working/traffic_cop/current_specs.csv"
                       ]
    production_specs_filepath = st.selectbox("Select a production specs file", specs_available)
    production_specs_df = pd.read_csv(production_specs_filepath)
    edited_specs = st.data_editor(production_specs_df, use_container_width=True, num_rows="dynamic", hide_index=True)
    # get items from edited_specs where produce = True
    selected_titles = edited_specs[edited_specs['select'] == True]
    if st.button("Save edited specs"):
        edited_specs.to_csv(production_specs_filepath, index=False)

# UI element for uploading a file
uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

# Check if a file was uploaded
if uploaded_file:

    if uploaded_file is not None:
        # create safe thisdoc_dir filename from base filename
        filename = uploaded_file.name.split('.')[0]
        output_dir = "output/"
        thisdoc_dir = make_basename_safe(os.path.basename(filename))
        thisdoc_dir = output_dir + thisdoc_dir
        if not os.path.exists(f"{thisdoc_dir}"):
            os.makedirs(f"{thisdoc_dir}")

        file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type,
                        "FileSize": uploaded_file.size}
        st.info(file_details)
        save_uploaded_file(uploaded_file, f"{thisdoc_dir}")

    else:
        st.error("You must upload a book to proceed.")
        st.stop()

    # Instantiate and load the classes that will be used to process the PDF
    pdfp = CorePDFProcessor(f"{thisdoc_dir}/{uploaded_file.name}")
    # au.make_directories(pdfp.output_dir, pdfp.thisdoc_dir)
    st.info(pdfp.production_specs_filepath)
    production_specs_df = pdfp.read_production_specs_df(pdfp.production_specs_filepath)
    # initialize metadatas object
    metadatas = Metadatas.Metadatas()

    # make metadatas a dict

    metadatas.set_attributes_to_values({'thisdoc_dir': thisdoc_dir})

    # on go-ahead from user, process the PDF

    with st.form(key='pdf_form'):
        box1, box2, box3, box4 = st.columns(4)
        page_limit = box1.number_input("Pages to scan", min_value=1, max_value=1200, value=10)
        preset_this_run = box2.selectbox("Preset", ["Test (ELI5)", "Full", "Tweets"])
        model = box3.selectbox("Model", ["gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-4"])
        temperature = box4.number_input("Temperature for Summary", min_value=0.0, max_value=2.0, value=0.0)
        flags = box1.multiselect("Flags", ["page-by-page-AI", "verbose-chat-complete"])
        number_of_front_matter_pages = box2.number_input("Number of Front Matter Pages", min_value=1, max_value=100,
                                                         value=1,
                                                         help="number of PDF pages before the printed page that is numbered '1'")
        spin = st.text_area("Spin", value="Summarize this book insightfully.")
        mode = st.selectbox("Mode", ["assess", "produce"])
        if preset_this_run == "Test (ELI5)":
            preset_this_run = {"ELI5": "ELI5"}
        elif preset_this_run == "Full":
            preset_this_run = common_presets_for_metadata()
        elif preset_this_run == "Tweets":
            preset_this_run = {"TweetCountdown": "TweetCountdown"}
        submitted = st.form_submit_button(label='Process PDF')
        if submitted:
            metadatas.set_attributes_to_values({'filepath': pdfp.filepath})

            # if page_limit less than length of PDF in pages, excerpt that number of pages
            if page_limit < len(fitz.open(f"{thisdoc_dir}/{uploaded_file.name}")):
                output_file = extract_pages_from_pdf(f"{thisdoc_dir}/{uploaded_file.name}", f"{thisdoc_dir}/sample.pdf",
                                                     1, page_limit)
                file_to_read = output_file
                filepath_to_load = f"{thisdoc_dir}/sample.pdf"
                st.info(f"excerpted {page_limit} pages from {filepath_to_load} for easy test processing")
                logger.info(f"excerpted {page_limit} pages from {filepath_to_load} for easy test processing")
            else:
                file_to_read = f"{uploaded_file.name}"
                filepath_to_load = f"{thisdoc_dir}/{uploaded_file.name}"
            if "page-by-page-AI" in flags:
                pagebypage = True
            if "verbose-chat-complete" in flags:
                Verbose = True

            with st.status("loading PDF and summarizing"):
                PDFReader = download_loader("PDFReader")
                loader = PDFReader()
                documents = loader.load_data(file=Path(filepath_to_load))
                persist_location = f"{thisdoc_dir}/index/docstore.json"
                persist_dir = f"{thisdoc_dir}/index"

                # variables for query_engine
                qmax_tokens = 500
                qmodel = "gpt-3.5-turbo-instruct"
                qmemory = 3900

                # variables for prompt helper
                # define prompt helper
                # set maximum input size
                max_input_size = 3000
                # set number of output tokens
                num_output = 256
                # set maximum chunk overlap
                max_chunk_overlap = 0.2

                prompt_helper = PromptHelper(max_input_size, num_output, max_chunk_overlap)

                if os.path.exists(persist_location):
                    # rebuild storage context
                    storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
                    # load index
                    summary_index = load_index_from_storage(storage_context)
                    chat_engine = summary_index.as_query_engine(memory=qmemory,
                                                                response_mode="tree_summarize"
                                                                , service_context=ServiceContext.from_defaults(
                            prompt_helper=prompt_helper,
                            llm=OpenAI(temperature=temperature, model=qmodel, max_tokens=qmax_tokens)))
                    st.success(f"loaded index from storage {persist_dir}")
                    logger.info(f"loaded index from storage {persist_dir}")
                # use llama-index to get statistics about the index

                else:
                    try:
                        summary_index = SummaryIndex.from_documents(documents, show_progress=True)
                        summary_index.storage_context.persist(Path(f"{thisdoc_dir}/index"))
                        chat_engine = summary_index.as_query_engine(
                            response_mode="tree_summarize", service_context=ServiceContext.from_defaults(
                                llm=OpenAI(temperature=temperature, model=qmodel, max_tokens=qmax_tokens,
                                           qmemory=qmemory, prompt_helper=prompt_helper)))

                        summary_index.storage_context.persist(Path(f"{thisdoc_dir}/index"))
                        st.success(f'saved index to storage in {thisdoc_dir}/index')
                    except Exception as e:
                        st.error(f"An error occurred in llama_index while processing the PDF: {str(e)}")
                        st.stop()
                text = documents[0].text
                # st.info("getting ready to go to LLM")
                llm = OpenAI(temperature=temperature, model="gpt-3.5-turbo-16k", max_tokens=700)
                service_context = ServiceContext.from_defaults(llm=llm, chunk_size=500)
                # st.write(service_context.to_dict())
                summary = chat_engine.query(spin)
                st.write(summary.response)

            with st.status("algorithmic analysis of PDF in process..."):
                try:
                    text, text_df, text_extractableness = pdfp.pdf2text2df(pdfp.filepath, page_limit, pdfp.thisdoc_dir)
                    text_dict = text_df.to_dict()
                except Exception as e:
                    st.error(f"An error occurred while processing the PDF: {str(e)}")
                    st.stop()
                # st.write(text_extractableness)
                metadatas.set_attributes_to_values({'text': text})
                metadatas.set_attributes_to_values({'text_df': text_df})
                metadatas.set_attributes_to_values({'text_dict': text_dict})
                metadatas.set_attributes_to_values({'text_extractableness': text_extractableness})
                pdf_inferred_metadata = pdfp.infer_additional_metadata_about_pdf(metadatas)
                metadatas.set_attributes_to_values({'pdf_inferred_metadata': pdf_inferred_metadata})
                toc = pdfp.pdfgetlistoftoc(pdfp.filepath)
                metadatas.set_attributes_to_values({'toc': toc})
                metadatas = pdfp.metadatas2keywordlists(metadatas, thisdoc_dir)
                pagedimensionslist = pdfp.pdfpagedimensions2list(pdfp.filepath)
                metadatas.set_attribute('pagedimensionslist', pagedimensionslist)
                page_size_analysis_results = pdfp.analyze_page_dimensions(pagedimensionslist)
                metadatas.set_attribute('page_size_analysis_results', page_size_analysis_results)
                tokens = pdfp.count_tokens(text)
                metadatas.set_attribute('tokens', tokens)
                metadatas = pdfp.pdfnativemetadata(metadatas)
                keylist = ["filepath", "pdf_native_metadata", "toc"]
                metadatas.set_attributes_to_values({'title': metadatas.get_attribute('pdf_native_metadata')['title']})
                metadatas.set_attributes_to_values({'author': metadatas.get_attribute('pdf_native_metadata')['author']})
                metadatas.set_attributes_to_values(
                    {'Publisher_supplied_Keywords': metadatas.get_attribute('pdf_native_metadata')['keywords']})
                metadatas.set_attributes_to_values(
                    {'Publisher_supplied_synopsis': metadatas.get_attribute('pdf_native_metadata')['subject']})

                algorithmic_info = metadatas.get_values_for_keys(keylist)
                st.write(algorithmic_info)

            with st.status("incorporating specifications from production specs"):
                try:
                    metadatas = pdfp.process_production_specs_df(metadatas, production_specs_df)
                    st.info(metadatas.get_attribute('specs_matches'))
                    # st.info(metadatas.get_attribute('changed_values'))
                except Exception as e:
                    st.error(f"An error occurred while incorporating production specs: {str(e)}")
            if mode == 'assess':
                st.info("mode is assess, exiting function")
                metadatas_df = pd.DataFrame.from_dict(metadatas.get_all_attributes(), orient='index')
                metadatas_df.sort_index(inplace=True)
                edited_df = st.data_editor(metadatas_df)
                edited_df.to_json(f'{thisdoc_dir}/metadatas.json')
                st.stop()
            elif mode == 'produce':
                st.info("mode is produce, continuing")
                metadatas.set_attributes_to_values({'mode': 'produce'})
                metadatas.submit_synopsis = summary.response

            with st.status("creating AI metadata for book as a whole"):
                try:
                    metadatas = pdfp.metadatas2aiservices(metadatas, presets=preset_this_run, model=model,
                                                          temperature=temperature, verbose=False)
                    st.success(f"Created AI metadata using {len(preset_this_run)} presets.")
                    metadatas_dict = metadatas.get_all_attributes()
                    # st.json(display_dict, expanded=False)
                    metadatas_df = pd.DataFrame.from_dict(metadatas_dict, orient='index')
                    metadatas_df.sort_index(inplace=True)
                    # metadatas_df.to_json(f'{thisdoc_dir}/metadata.json')
                    edited_df = st.data_editor(metadatas_df, use_container_width=True)
                    metadatas_df = edited_df
                    # convert metadatas_df to metadatas object
                    metadatas.set_attributes_to_values(metadatas_df.to_dict())
                    metadatas.set_attributes_to_values({'text_df': text_df})
                    edited_df.to_json(f'{thisdoc_dir}/edited_df.json')
                except Exception as e:
                    st.error(f"An error occurred in 2ai while processing the PDF: {str(e)}")

            with st.status("creating metadata for each page"):
                pagebypage = True
                if pagebypage:
                    pagebypagepresets = ['PageByPageSummary', 'PageByPageNotableQuotes']
                    try:
                        results_df = pdfp.pagebypage2aiservices(metadatas, presets=pagebypagepresets)
                        st.success(f"Created page by page analysis using {len(pagebypagepresets)} presets.")
                    except Exception as e:
                        st.error(f"An error occurred in pagebypage2aiservices while processing the PDF: {str(e)}")
                else:
                    st.info("Did not create any page by page metadata")

            with st.status("creating front matter"):
                try:
                    st.info(f"{thisdoc_dir}/{uploaded_file.name}")
                    metadatas = pdfp.create_front_matter(f"{thisdoc_dir}/{uploaded_file.name}", metadatas,
                                                         thisdoc_dir)
                except Exception as e:
                    st.error(f"An error occurred in create_front_matter while processing the PDF: {str(e)}")

            with st.status("creating cover metadata"):
                try:
                    # st.info('trying to create cover metadata')
                    bookjson = metadatas2bookjson(metadatas, thisdoc_dir)
                    # st.info('tried')
                    st.info('Successfully created bookjson for cover')
                    st.write(bookjson)
                except Exception as e:
                    st.error(f"An error occurred in 2bookjson while processing the PDF: {str(e)}")
                    bookjson = {f"error": {e}}
                bookjson_df = pd.DataFrame.from_dict(bookjson, orient='index')
                # fill in missing values
                bookjson_df = bookjson_df.fillna('')
                bookjson_df.sort_index(inplace=True)
                bookjson_df.to_json(f'{thisdoc_dir}/bookjson.json')
                # check if metadatas.uuid has well-formed uuid
                uuid = metadatas.get_attribute('uuid')
                if len(uuid) == 8:
                    st.info(f"uuid is {uuid}")
                else:
                    st.error(f"uuid is {uuid}")

                full_path = os.path.abspath(f'resources/bookjson/{metadatas.uuid}.json')
                print(full_path)
                st.info(f"bookjson saved to {full_path}")
                bookjson_df.to_json(full_path)
                # bookjson_df.to_json(f'resources/bookjson/{metadatas.title}.json')

                st.success("Processing complete!")
                rain(
                    emoji="📚",
                    font_size=54,
                    falling_speed=5,
                    animation_length="5",
                )
