#  Copyright (c) 2023. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com

import json
import os

import altair as alt
import pandas as pd
import streamlit as st

from app.ManageUserAPIKeys import ManageUserAPIKeys
from app.utilities.utilities import read_markdown_file, get_version_as_dict, submit_guard, statcounter
from classes.SyntheticReaders import ReaderPanels as rp, RatingUtilities as cu


def save_uploaded_file(uploaded_file, user_docs_target_dir):
    with open(os.path.join(user_docs_target_dir, uploaded_file.name), "wb") as f:
        f.write(uploaded_file.getbuffer())
    success_msg = f"File {uploaded_file.name} saved successfully to " + f"{user_docs_target_dir}."
    return st.success(success_msg)


api_key_manager = ManageUserAPIKeys()

with st.sidebar:
    st.session_state.openai_key = api_key_manager.enter_api_key("openai for reader panels")
    st.components.v1.iframe('https://fredzannarbor.substack.com/embed', width=320, height=200, scrolling=False)
    sidebar_message = read_markdown_file("resources/markdown/sidebar_message.md")
    st.sidebar.markdown(sidebar_message)
    st.sidebar.markdown("""**Operational**, no known issues""")
    version2 = json.dumps(get_version_as_dict())
    st.sidebar.json(version2)
st.title("Submit A Text To A Reader Panel")
#
# tab1 = st.tabs(["Evaluate Ideas and More"])
#

with st.expander("Choose a Reader Panel", expanded=True):
    st.markdown(
        """Each Reader Panel is a group of Readers who have similar preferences.  You can choose a Reader Panel by clicking on the dropdown below.  The Reader Panel will be displayed in the space below.""")

    rpnames = ["AcquisitionEditorSarah", "PointyHeadedBoss", "Test"]
    rpname = st.selectbox("Choose a Reader Panel", rpnames, index=0)
    if rpname:
        panel_df = rp.ReaderPanels().get_saved_reader_panel(rpname)
        reader_names = panel_df['name']
        reader_names = ', '.join(reader_names)
        # st.info(f"Readers in this panel: {reader_names}")
        panel_df = st.data_editor(panel_df)
        panel_df.to_csv(f'resources/reader_panels/SelectedPanel.csv', index=False)

with st.expander("Evaluate a complete book", expanded=True):
    text_evaluate = st.form(key='text evaluation')
    with text_evaluate:
        uploaded_file = st.file_uploader("Upload a complete book", type=["epub"],
                                         help="Upload a complete book in EPUB format.")
        response_mode = st.radio("Response mode", ["Paragraph-by-paragraph"], index=0,
                                 help="Paragraph-by-paragraph: each para is evaluated by each reader.")
        submitted = st.form_submit_button("Upload and Evaluate")
        if submitted:
            submit_guard()
            if uploaded_file is not None:
                file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type,
                                "FileSize": uploaded_file.size}
                save_uploaded_file(uploaded_file, "working")
            selected_panel_df = pd.read_csv('resources/reader_panels/SelectedPanel.csv')
            # spinnermessage = st.text("Evaluating your text...")
            with st.spinner("Evaluating your text..."):

                result = cu.text2readerpanel2llama("working/" + uploaded_file.name, selected_panel_df,
                                                   "EvaluateTextChunk", response_mode)
            for r in result['Rating']:
                # if r begins with +, then make it a positive n
                # if r begins with -, then make it a negative n
                # if r begins with 0, then make it 0
                if r[0] == '+':
                    r = r[1:]
                if r[0] == '-':
                    r = r[1:]
                if r[0] == '0':
                    r = r[1:]
            ratings_df = pd.DataFrame(result)
            # ratings_df.columns = ['Rating', 'Chunk', 'Sentiment', 'Shortname', 'Shortcerpt']
            ratings_df['Rating'] = ratings_df['Rating'].astype(int)
            # if Ratings is 0, then force it to 0.2
            ratings_df['Rating'] = ratings_df['Rating'].apply(lambda x: 0.2 if x == 0 else x)
            ratings_df['Sentiment'] = ratings_df['Rating'].apply(
                lambda x: 'Zero' if x == 0 else ('Negative' if x < 0 else 'Positive')
            )
            # st.bar_chart(ratings_df)
            st.write(ratings_df)

            # of chunks in df
            num_chunks = len(ratings_df['Chunk'].unique())
            st.caption("Reader panel evaluations")

            chart = alt.Chart(ratings_df).mark_bar().encode(
                alt.Y('Rating:Q', scale=alt.Scale(domain=(-6, 6))),
                alt.X('Chunk:Q',
                      scale=alt.Scale(domain=(1, num_chunks),
                                      nice=False, ),
                      axis=alt.Axis(values=list(range(1, num_chunks + 1)))),
                alt.Color('Sentiment:N',
                          scale=alt.Scale(domain=['Negative', 'Zero', 'Positive'], range=['red', 'blue', 'green'])),
                tooltip=['Rating', 'Chunk', 'Sentiment', 'Reader Shortname']
            )

            st.altair_chart(chart, use_container_width=True)
            fileshortname = uploaded_file.name.split('.')[0] + uuid.uuid4().hex[:6].upper() + '.csv'
            ratings_df.to_csv('output/' + fileshortname, index=False)

with st.expander("Further information", expanded=True):
    st.info(
        "This is an experimental feature in early stages of development. If you have questions, suggestions, or feedback, please contact me at the address in the sidebar.")

statcounter(0, 0)
