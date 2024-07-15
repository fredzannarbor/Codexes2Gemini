import json
from uuid import uuid4

import pandas as pd
import streamlit as st

from app.ManageUserAPIKeys import ManageUserAPIKeys
from app.utilities.utilities import (
    read_markdown_file,
    get_version_as_dict, spreadsheet2df, submit_guard)
# from classes.SyntheticReaders import Reader, ReaderPanels as rp, RatingUtilities as cu
from classes.Ideas.IdeaUtilities import IdeaUtilityFunctions as iuf

api_key_manager = ManageUserAPIKeys()



with st.sidebar:
    st.session_state.openai_ky = api_key_manager.enter_api_key("openai")
    st.components.v1.iframe('https://fredzannarbor.substack.com/embed', width=320, height=200, scrolling=False)
    sidebar_message = read_markdown_file("resources/markdown/sidebar_message.md")
    st.sidebar.markdown(sidebar_message)
    st.sidebar.markdown("""**Operational**, no known issues""")
    version2 = json.dumps(get_version_as_dict())
    st.sidebar.json(version2)
st.title("Synthetic Authors")

#tab1, tab2, tab3, tab4 = st.tabs(["Ideas To Authors", "Author Stables", "Author Personas", "Author Generated Ideas"])
tab1, tab2 = st.tabs(["Send Ideas To Authors",  "TK"])

with tab1:
    result_df = pd.DataFrame()
    ideas_df = pd.DataFrame()
    author_stable_name = "resources/author_personas/greats.csv"
    author_stable_df = pd.read_csv(author_stable_name)
    st.caption("Roster of authors available for idea expansion")
    st.dataframe(author_stable_df.head(5))
    selected_authors = st.radio("Select an author stable", ["Greats"])
    button = st.button("Confirm authors")
    if not button:
        st.warning("You must confirm authors to proceed")
    else:
        st.success("Authors confirmed")
    with st.form(key='eeideas'):
        st.info("Pass ideas along to a stable of authors for expansion.")
        uploaded_file = st.file_uploader("Upload a file of ideas to explore and elaborate", type=['xlsx', 'csv', 'txt'])
        st.form_submit_button(label='Upload')
    newideas_df = pd.DataFrame()
    if uploaded_file is None:
        st.error("You must upload a file to proceed.")
    else:
        # move uploaded file to working
        ideas_df = spreadsheet2df(uploaded_file)
        edited_df = st.data_editor(ideas_df)
        file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type,
                        "FileSize": uploaded_file.size}
        st.info(file_details)
    with st.form(key='proceed'):
        num_authors_per_idea = st.number_input("How many authors should each idea be assigned to?", min_value=1, max_value=5, value=1)
        num_ideas_to_generate = len(ideas_df) * num_authors_per_idea
        st.info(f"Generating {num_ideas_to_generate} ideas from {len(ideas_df)} ideas and {num_authors_per_idea} authors assigned to each idea.")
        idea_instance = iuf()
        proceeding = st.form_submit_button(label='Proceed')
        if proceeding:
            submit_guard()
            result_df = idea_instance.ideas2authors_for_expansion(author_stable_df, edited_df)
            st.dataframe(result_df)
            result_df.to_json("output/authors2ideas_para_results" + str(uuid4())[:6] + ".json")
            result_df.to_csv("output/authors2ideas_para_results" + str(uuid4())[:6] + ".csv")
    if result_df.shape[0] > 0:
        st.download_button(label="Download results", data=result_df.to_csv(), file_name="results.csv", mime="text/csv")
