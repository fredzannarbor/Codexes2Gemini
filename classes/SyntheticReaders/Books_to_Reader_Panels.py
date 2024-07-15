import json
from uuid import uuid4

import ebooklib
import pandas as pd
import spacy
import streamlit as st
from bs4 import BeautifulSoup
from ebooklib import epub

from app.ManageUserAPIKeys import ManageUserAPIKeys
from app.utilities.utilities import (
    read_markdown_file,
    get_version_as_dict, statcounter, save_uploaded_file)
from classes.Codexes.Tools.DocxCodex2Objects import DocxCodex2Objects as dx2obj
from classes.SyntheticReaders.RatingUtilities import rate_objects
from classes.SyntheticReaders.ReaderPanels import ReaderPanels

nlp = spacy.load('en_core_web_sm')

api_key_manager = ManageUserAPIKeys()
st.set_page_config(page_title="Reader Panels", page_icon="👥📚", layout="wide", initial_sidebar_state="expanded")
def extract_text_from_epub(file_path):
    book = epub.read_epub(file_path)
    paragraphs = []

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.content, 'html.parser')
        for p in soup.find_all('p'):
            paragraphs.append(p.get_text())
    return paragraphs


with st.sidebar:
    st.session_state.openai_ky = api_key_manager.enter_api_key("openai")
    st.components.v1.iframe('https://fredzannarbor.substack.com/embed', width=320, height=200, scrolling=False)
    sidebar_message = read_markdown_file("resources/markdown/sidebar_message.md")
    st.sidebar.markdown(sidebar_message)
    st.sidebar.markdown("""**Operational**, no known issues""")
    version2 = json.dumps(get_version_as_dict())
    st.sidebar.json(version2)

st.title("Send Your Book to a Reader Panel")
#
# tab1 = st.tabs(["Evaluate Ideas and More"])
#
# with tab1:
st.write("On this page, you can explore how different Readers experience a book.")
with st.expander("About Synthetic Readers", expanded=True):
    st.markdown(
        """Synthetic Readers are AI and LLM-powered agents whose job is to simulate an individual human's experience reading a book.  They are designed to be used by authors, publishers, and readers to help them understand what makes a book work, and what makes it fail. They arrive at their recommendations by evaluating a book three ways: page by page, cumulatively, and globally.  Further details are available on the documentation pages.""")
    st.markdown(
        """Each Reader has a unique set of preferences and there are thousands of them.  On this page, you can use preconfigured Reader Panels to explore the different ways Readers experience a book.""")


with st.expander("Choose a Reader Panel", expanded=True):
    reader_panels_instance = ReaderPanels()
    # Invoke the user_interface function
    panel_df = reader_panels_instance.user_interface()


with st.expander("Upload A Book", expanded=True):
    with st.form(key='completions dataframe'):
        st.markdown("""Here, you can submit a book to the Reader Panels for evaluation.""")
        st.markdown("""The Reader Panels will evaluate your manuscript one paragraph at a time return a dataframe of results. In this initial version, each paragraph is evaluated on its own merits. In future, a paragraph will be evaluated in the context of the entire preceding content.""")
        uploaded_file = st.file_uploader("Upload epub, docx, or text file", type=["docx", "epub", "txt"])

        st.form_submit_button("Upload Book", on_click=None, help=None)
        if uploaded_file is not None:
            # convert codex to dataframe of paras
            # move uploaded file to working directory

            file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type,
                            "FileSize": uploaded_file.size}
            st.info(file_details)
            save_uploaded_file(uploaded_file, "working")
            # show working/ directory
            #os.system("ls -l working")
        else:
            st.error("You must upload a book to proceed.")



with st.expander("Evaluate the Book", expanded=True):
    with st.form(key='send to readers'):
        n_rows = st.number_input("Number of paragraphs to evaluate", min_value=1, max_value=10000, value=5, step=100)
        submitted = st.form_submit_button("Send Your Book To Readers")
    submit_guard = st.empty()
    #if submit_guard:
    if submitted:
        if uploaded_file.name.endswith('.epub'):
            paras = extract_text_from_epub('working/' + uploaded_file.name)
            paras_df = pd.DataFrame(paras, columns=['para'])
        if uploaded_file.name.endswith('.docx'):
            paras_= dx2obj().prepare4readerpanel('working/' + uploaded_file.name)
            paras_df = pd.DataFrame(paras_, columns=['para'])
            st.write(paras_df)
        results_df = rate_objects(paras_df, panel_df, ["EvaluateParasEnhance"], n_rows, "gpt-3.5-turbo","para")

        #results_df = rate_paras(paras_df, panel_df, "EvaluateParaPointsOnly", 10)
        st.success(f"Completed {results_df.shape[0]} evaluations.")
        #spreadsheet(paras_df, key=(str(uuid4())[:6]))
        filename = "Reader_Panel_results_" + str(uuid4())[:6] + ".csv"
        # if results_df is not empty, then proceed
        if results_df.shape[0] > 0:
            #visualize_object_df(results_df)
            edited_results_df = st.data_editor(results_df, help="Results are editable. Click on a cell to edit it.")

            st.download_button("Download results", results_df.to_csv(), "Reader_Panel_results.csv", "text/csv", key="download1")

with st.expander("Further information", expanded=False):
    st.info(
        "This is a beta feature. If you have questions, suggestions, or feedback, please contact me at the address in the sidebar.")



statcounter(0, 0)
