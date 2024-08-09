import csv
import json
import os
from os import path

# streamlit_analytics.start_tracking()
import pandas as pd
import streamlit as st
from classes.Codexes.PartsOfTheBook.Indexes.pdf2index import search_pdf_pages_with_list_of_search_synonyms, process_index_dict_results, pdf_pages_containing_index_terms



from app.utilities.utilities import (
    read_markdown_file,
    get_version_as_dict,
)

# from streamlit_ace import st_ace

# functions


def file_uploader(user_docs_target_dir="app/userdocs/37/"):

    uploaded_file = None
    file_details = None
    filepath = None

    try:
        uploaded_file = st.file_uploader("Upload your manuscript", type=["pdf"])
    except Exception as e:
        st.error("Could not upload file. Error: %s" % e)

    if uploaded_file is not None:
        file_details = {
            "FileName": uploaded_file.name,
            "FileType": uploaded_file.type,
            "FileSize": uploaded_file.size,
        }
        user_docs_target_dir = "app/userdocs/" + str(user_id)
        if not os.path.exists(user_docs_target_dir):
            os.makedirs(user_docs_target_dir)

        tempdir_target_dir = "/tmp/unity/" + str(user_id)
        if not os.path.exists(tempdir_target_dir):
            os.makedirs(tempdir_target_dir)

        save_result_message = (
            save_uploaded_file(uploaded_file, user_docs_target_dir)
            + " "
            + str(uploaded_file.size)
            + " bytes"
        )
        st.info(save_result_message)
        filepath = user_docs_target_dir + "/" + uploaded_file.name
    st.info(filepath)
    return filepath


@st.cache_data()
def save_uploaded_file(uploaded_file, user_docs_target_dir):
    save_file_path = os.path.join(user_docs_target_dir, uploaded_file.name)
    with open(save_file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    if os.path.exists(save_file_path):
        success_msg = (
            f"File {uploaded_file.name} saved successfully to "
            + f"{user_docs_target_dir}."
        )
    else:
        success_msg = (
            f"File {uploaded_file.name} could not be saved to {user_docs_target_dir}."
        )
    return success_msg


@st.cache_data
def convert_df(df):
    return df.to_csv().encode("utf-8")


# settings

user_id = "37"

filepath = "test/pdf/lorem_with_roman_through_piii.pdf"
tempdir_target_dir = "output/"
uploaded_file = None

output_dir = "output/"
# search_terms_filename = 'working/contracted/15_with_author/AGFW/index_terms.txt'
search_terms_filename = "working/contracted/15_with_author/AGFW/list2.txt"
front_matter_last_page = 24  # should be odd because physical page number is verso, minus 1 because Python logical page numbering starts at 0
unnumbered_front_matter_pages = [0, 1, 3]
do_not_index_these_pages_list = [0, 1, 2, 3]
# read in csv file
with open(search_terms_filename, "r") as f:
    reader = csv.reader(f)
    search_terms_list = list(reader)


# set up banner and sidebar

banner = ['resources/images/Trifecta.jpg']
#banner = build_trifecta_banner()()
st.image(banner[0], use_column_width=True)

sidebar_message = read_markdown_file("resources/markdown/sidebar_message.md")
st.sidebar.markdown(sidebar_message)
version2 = get_version_as_dict()
st.sidebar.write(version2)

with st.expander("History of the Book Index", expanded=True):

    st.markdown(
        """

    Indexes in codex books have a long and elaborate history that is well narrated in _A History of the Index_ (Duncan 2021). In a nutshell, indexes began as a diverse and populous genus that included dozens of large charismatic species, then gradually shrank down to a few efficient, modern forms--until encountering the twin planet-killing near-extinction events we know as the search engine and the e-reader.

    """
    )

with st.expander("State of the Art for Back-of-the-Book Indexing", expanded=True):

    st.markdown(
        """ ## Overview
    To summarize briefly, many automated tools are available to help create the index to a book, but the most effective and accurate results still require human participation.
    The scholarly literature sometimes distinguishes book indexing from other types of indexing by using the term "back-of-the-book indexing."
    
    ## Whether to Include An Index
    
    The first decision a publisher must make is whether a book requires an index. By default, fiction usually does not include an index, but there are occasional exceptions, often for purposes of whimsy or metacommentary. Nonfiction usually does include an index.  
    
    With the advent of electronic books, the case for automatically including an index has become less clear.  Electronic book readers usually include a keyword search tool that probably meets most of the user's requirements.
    
    Perhaps the most compelling reason for leaving out an index is that it is costly and time-consuming to create.  Professional indexers charge between $3 and $5 per page depending on the type of material and the level of expertise. (Index Busters, 2022; Society of Indexers, 2022) Authors may resist the effort which might
    
    ## Identifying Index Entry Terms
    
    ## Expanding Index Entry Terms to Include Synonyms and Related Terms
    
    ##
    
    
    ## Searching The Manuscript for Occurrences of Index Terms and Concepts
    
    Having identified the index entry terms, the next step is to search the manuscript for occurrences of the index terms. There are a few subtleties to be aware of.  
    
    The index terms are not always the same as the search terms.  For example, the index term "R–14" is not the same as the search term R-14 (the former uses an en dash, Unicode 0x2013, to separate the two digits, whereas the latter uses a hyphen, Unicode 0x002D). In this case, you want to include the index entry to include all instances of both spellings.
        """
    )


with st.expander("About the All-in-One Indexer", expanded=False):
    st.markdown(
        """
        I wrote **pdf2index**, a Python module that analyzes the final interior PDF of a book to create an index for the print version.  The module can be run from the command line, called from other programs, executed step-by-step in the expander sections that follow, or run all at once if a clean list of index entries is already available."""
    )
with st.expander("Upload your file here", expanded=True):
    # filepath = None
    try:
        uploaded_file = st.file_uploader("Upload your manuscript", type=["pdf"])
    except Exception as e:
        st.error("Could not upload file. Error: %s" % e)

    if uploaded_file is not None:
        file_details = {
            "FileName": uploaded_file.name,
            "FileType": uploaded_file.type,
            "FileSize": uploaded_file.size,
        }
        user_docs_target_dir = "app/userdocs/" + str(user_id)
        if not os.path.exists(user_docs_target_dir):
            os.makedirs(user_docs_target_dir)

        tempdir_target_dir = "/tmp/unity/" + str(user_id)
        if not os.path.exists(tempdir_target_dir):
            os.makedirs(tempdir_target_dir)

        save_result_message = (
            save_uploaded_file(uploaded_file, user_docs_target_dir)
            + " "
            + str(uploaded_file.size)
            + " bytes"
        )
        st.info(save_result_message)
        filepath = user_docs_target_dir + "/" + uploaded_file.name
        index_results_temp = pdf_pages_containing_index_terms(filepath, search_terms_list, 1200)
        # st.write('search terms will be:', search_terms_list)
        index_results_temp = search_pdf_pages_with_list_of_search_synonyms(
            filepath, search_terms_list, searchpageslimit=1200
        )
        index_results = index_results_temp[0]
        converted_page_text_list = index_results_temp[1]

        # index_results_json = json.dumps(index_results)
        # st.download_button("download json", data=index_results_json, file_name="index_results.json")

        # converted_page_text_json = json.dumps(converted_page_text_list)
        # st.download_button("download page text json", data=converted_page_text_json, file_name="converted_page_text_list.json")

        try:
            index_results = process_index_dict_results(
                index_results,
                output_dir,
                front_matter_last_page,
                unnumbered_front_matter_pages_list=[0],
                do_not_index_these_pages_list=[0],
            )

        except Exception as e:
            st.error("Exception: " + str(e))
        a, b, c = st.columns([3, 3, 3])
        string = ""
        with open(path.join(output_dir, "index_dict.txt"), "w") as f:
            for key, value in sorted(index_results.items()):
                pages = ", ".join(str(x) for x in value)
                # print(pages)
                f.write(key + "\t" + str(pages) + "\n")
                string = key + "\t" + str(pages) + "\n" + string
            a.download_button(
                "Download index results as tab-delimited text file", string, "text/csv"
            )

            # convert index)results to json
            index_results_json = json.dumps(index_results)
            b.download_button(
                "Download index results as JSON",
                data=index_results_json,
                file_name="index results.json",
            )
            index_results_df = pd.DataFrame.from_dict(index_results, orient="index")

            csv = convert_df(index_results_df)
            c.download_button(
                "Download index result as CSV",
                csv,
                "file.csv",
                "text/csv",
                key="download-csv",
            )



