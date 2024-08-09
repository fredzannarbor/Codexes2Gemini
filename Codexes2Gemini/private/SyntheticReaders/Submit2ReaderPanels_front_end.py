import json
from uuid import uuid4

import pandas as pd
import streamlit as st

from app.ManageUserAPIKeys import ManageUserAPIKeys
from classes.Utilities.utilities import (
    read_markdown_file,
    get_version_as_dict, statcounter)
from Codexes2Gemini.private.SyntheticReaders.RatingUtilities import rate_ideas, rate_remits, llmjson2json
# from classes.SyntheticReaders import Reader, ReaderPanels as rp, RatingUtilities as cu
from Codexes2Gemini.private.SyntheticReaders.ReaderPanels import ReaderPanels as rp

api_key_manager = ManageUserAPIKeys()


with st.sidebar:
    st.session_state.openai_ky = api_key_manager.enter_api_key("openai")
    st.components.v1.iframe('https://fredzannarbor.substack.com/embed', width=320, height=200, scrolling=False)
    sidebar_message = read_markdown_file("resources/markdown/sidebar_message.md")
    st.sidebar.markdown(sidebar_message)
    st.sidebar.markdown("""**Operational**, no known issues""")
    version2 = json.dumps(get_version_as_dict())
    st.sidebar.json(version2)
st.title("Reader Panels")
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

    rp = rp()
    user_interface = rp.user_interface()

with st.expander("Submit Ideas", expanded=True):
    with st.form(key='completions dataframe'):
        st.markdown("""Here, you can submit a list of series ideas to the Reader Panels for evaluation.""")
        st.markdown(
            """First, you will need to create a list of ideas. You can do this by using the [Book Series Generator](Book_Series_Generator) page and downloading the dataframe as a csv file, or by creating a csv file of your own in the sam format. Then, you can upload the ideas file here.""")
        st.markdown(
            """Once you have uploaded the csv file, you can submit it to the Reader Panels for evaluation.  The Reader Panels will evaluate the completions and return a dataframe of results.  You can download the results as a csv file.""")
        uploaded_file = st.file_uploader("Upload a csv file of ideas", type=["csv", "xlsx", "xls"])
        remit_or_idea = st.radio("Idea or Remit", ["Idea", "Remit"], index=0, help=" Ideas: new projects; Remits: new imprints or programs")
        st.form_submit_button("Upload Ideas", on_click=None, help=None)
        if uploaded_file is not None:
                completions_df = pd.read_csv(uploaded_file)
                st.info(
                    f"Uploaded {uploaded_file.name} with {completions_df.shape[0]}  {remit_or_idea}s.")
                st.write(completions_df.head(5))
        else:
            st.error("You must upload a file to proceed.")
            st.stop()


with st.expander("Evaluate Ideas", expanded=True):

    submitted = st.button("Evaluate")
    submit_guard = st.empty()
    if submitted and remit_or_idea == "Remit":
        results_df = rate_remits(completions_df, panel_df)
    elif submitted and remit_or_idea == "Idea":
        results_df = rate_ideas(completions_df, panel_df)
        results_df.to_csv("working/Reader_Panel_results.csv")
    else:
        st.warning(
            "This service requires an OpenAI API key and quite a few API calls: (number of readers) * (number of ideas) * (2 calls per idea). The process takes a few minutes. You must hit 'Evaluate' to proceed. ")

    if submitted:
        st.success(f"Completed {results_df.shape[0]} evaluations.")

        # get average rating excluding 0s
        if remit_or_idea == "Idea":
            avg_rating = results_df[results_df["Rating"] != 0]["Rating"].mean()
            # express average rating with one decimal place
            avg_rating = round(avg_rating, 1)
            st.success(f"Average rating excluding failed attempts: {avg_rating}")
        if remit_or_idea == "Remit":
            # extract json from results_df['Result ']
            # if json.loads error, then set to {}
            # how do I do try/except within a lambda function

            results_df['Result'] = results_df['Result'].apply(lambda x: llmjson2json(x))

            results_df['Classification'] = results_df['Result'].apply(lambda x: x['Classification'])
            # count the classifications
            results_df['Explanation'] = results_df['Result'].apply(lambda x: x['Explanation'])
            results_df = pd.DataFrame(results_df)
            classification_counts = results_df['Classification'].value_counts()
            classifications_mini_df = pd.DataFrame(classification_counts)
            st.write(classifications_mini_df)
            st.dataframe(results_df, hide_index=True)
        filename = "Reader_Panel_results_" + str(uuid4())[:6] + ".csv"
        # if results_df is not empty, then proceed
        if results_df.shape[0] > 0:
            st.download_button("Download results", results_df.to_csv(), "Reader_Panel_results.csv", "text/csv",
                               key=(str(uuid4())[:6]))
            results_df.to_json("working/Reader_Panel_results.json", orient="records")

with st.expander("Further information", expanded=False):
    st.info(
        "This is a beta feature. If you have questions, suggestions, or feedback, please contact me at the address in the sidebar.")



statcounter(0, 0)
