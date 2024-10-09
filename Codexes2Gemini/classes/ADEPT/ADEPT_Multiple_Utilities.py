# Copyright (c) 2023. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.comimport os
from pathlib import Path
import os
import pandas as pd
import streamlit as st
import classes.Codexes.Metadata.Metadatas as Metadatas

from llama_index import StorageContext, load_index_from_storage
from llama_index import download_loader, ServiceContext, SummaryIndex, PromptHelper
from llama_index.llms import OpenAI
from llama_index.memory import ChatMemoryBuffer

memory = ChatMemoryBuffer.from_defaults(token_limit=3900)


def index(thisdoc_dir, filename):
    st.info("Indexing PDF")
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
    return summary.response😭

    st.info("Analyzing PDF")
    try:
        text, text_df, text_extractableness = pdfp.pdf2text2df(pdfp.filepath, page_limit,
                                                               pdfp.thisdoc_dir)
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
    metadatas.set_attributes_to_values(
        {'title': metadatas.get_attribute('pdf_native_metadata')['title']})
    metadatas.set_attributes_to_values(
        {'author': metadatas.get_attribute('pdf_native_metadata')['author']})
    metadatas.set_attributes_to_values(
        {'Publisher_supplied_Keywords': metadatas.get_attribute('pdf_native_metadata')['keywords']})
    metadatas.set_attributes_to_values(
        {'Publisher_supplied_synopsis': metadatas.get_attribute('pdf_native_metadata')['subject']})

    analysis_results = metadatas.get_values_for_keys(keylist)
    st.write(analysis_results)
