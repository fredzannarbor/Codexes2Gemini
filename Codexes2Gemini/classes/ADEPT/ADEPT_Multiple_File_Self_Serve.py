import logging
import os
import re
import traceback
from datetime import datetime

import pandas as pd
import streamlit as st

import classes.ADEPT.ADEPT_utilities as Au
import classes.Codexes.Metadata.Metadatas as MDS
from app.utilities.metadatas2outputformats import metadatas2bookjson
from app.utilities.text2metadata_using_openai import common_presets_for_metadata
from app.utilities.utilities import get_environment_variables, get_version_as_dict
from classes.ADEPT.CorePDFProcessor import CorePDFProcessor
from classes.Codexes.Metadata.Distributors.LSI.create_LSI_ACS_spreadsheet import create_LSI_ACS_spreadsheet

logging = logging.getLogger('root')

submitted = False
use_llama_index = False


def choose_titles(selected_titles):
    chosen_titles_df = selected_titles[selected_titles['title'].isin(chosen_titles)]
    return chosen_titles_df


# st.set_page_config(layout="wide")
with st.expander("Debugging info"):
    OPENAI_API_BASE = os.environ["OPENAI_API_BASE"]
    st.info(OPENAI_API_BASE)
    st.info(os.path.abspath(os.getcwd()))
    st.write(get_version_as_dict())
    st.write(get_environment_variables())

st.title("ADEPT Self-Serve")
st.header("Multiple File Processing")
print('---' * 5 + 'STARTING' + '---' * 5)
production_specs_filepath = "output/specs/test.csv"

autils = Au.ADEPTUtilities()
with st.expander("Scan PDFs and create specs file"):
    scan = st.radio("Scan raw PDFs?", ["Yes", "Skip This Step"])
    if scan == "Yes":

        directory = st.text_input("Enter a directory to explore", value=None)
        if directory is None:
            st.error("You must enter a directory to proceed")
            st.stop()
        else:
            st.info(f"Exploring {directory}")
        rawlist = os.listdir(directory)
        rawlist.sort()
        # filter out non-PDF files
        pdflist = [filename for filename in rawlist if filename.endswith(".pdf")]
        # filter out .DS_Store files
        pdflist = [filename for filename in pdflist if not filename.startswith(".DS_Store")]
        # filter out files that are already in specs file
        # specs_df = pd.read_csv(f"{directory}/raw_specs.csv")
        st.json(pdflist, expanded=False)
        pages_to_process_limit = st.selectbox("Pages to scan", [5, 10, 20, 100, 200, 400, 1200])
        process = st.button(label='Process PDFs')
        if process:
            specs_df = autils.addPDFs2specsfile(directory=directory, pages_to_process_limit=pages_to_process_limit)
            raw_specs_df = st.data_editor(specs_df)
            submit = st.button(label='Save specs file')
            if submit:
                raw_specs_df.to_csv(f"{directory}/raw_specs.csv", index=False)
            else:
                st.warning("No PDFs processed yet")
        else:
            st.subheader("Review and edit specs file")
            production_specs_filepath = st.text_input("Enter path to production specs file")
            # check if production_specs_filepath is a valid path
            if os.path.isfile(production_specs_filepath):
                production_specs_df = pd.read_csv(production_specs_filepath)
                text_cols = ['title', 'subtitle', 'author', 'flags', 'motivation', 'source']
                production_specs_df[text_cols] = production_specs_df[text_cols].astype(str)
                edited_specs = st.data_editor(production_specs_df, use_container_width=True, num_rows="dynamic",
                                              hide_index=True)
            else:
                st.error(f"production_specs_filepath {production_specs_filepath} is not a valid path.")
                st.stop()
        if st.button("Save edited specs"):
            edited_specs.to_csv(production_specs_filepath, index=False)

with st.expander("Edit specs file"):
    edit = st.radio("Edit specs file?", ["Yes", "Skip This Step"])
    if edit == "Yes":
        production_specs_filepath = st.text_input("Enter path to production specs file",
                                                  value=production_specs_filepath)
        # check if production_specs_filepath is a valid path
        if not os.path.isfile(production_specs_filepath):
            st.error(f"production_specs_filepath {production_specs_filepath} is not a valid path.")
            st.stop()
        else:
            production_specs_df = pd.read_csv(production_specs_filepath)
            text_cols = ['title', 'subtitle', 'author', 'flags', 'motivation', 'source']
            production_specs_df[text_cols] = production_specs_df[text_cols].astype(str)
            edited_specs = st.data_editor(production_specs_df, use_container_width=True, num_rows="dynamic",
                                          hide_index=True, key="speczedit")
            save_button = st.button("Save edited specs?")
            if save_button:
                edited_specs.to_csv(production_specs_filepath, index=False)

with st.expander("Build books per specs file"):
    production_specs_filepath = st.text_input("Enter path to production specs file", value=production_specs_filepath,
                                              key="edit_this_specs_df")
    if not os.path.isfile(production_specs_filepath):
        st.error(f"production_specs_filepath {production_specs_filepath} is not a valid path.")
        st.stop()
    else:
        production_specs_df = pd.read_csv(production_specs_filepath)
        text_cols = ['title', 'subtitle', 'author', 'flags', 'motivation', 'source']
        production_specs_df[text_cols] = production_specs_df[text_cols].astype(str)
        edited_specs = st.data_editor(production_specs_df, use_container_width=True, num_rows="dynamic",
                                      hide_index=True, key="build")
    selected_titles = edited_specs[edited_specs['select'] == True]

    if selected_titles['select'].count() > 0:
        st.info(f"Found {selected_titles['select'].count()} titles to process")
        with st.form(key='production_form'):
            box1, box2, box3, box4 = st.columns(4)
            available_titles = selected_titles['title'].values
            chosen_titles = st.multiselect("Select titles to process", available_titles)
            chosen_titles_df = selected_titles[selected_titles['title'].isin(chosen_titles)]
            pages_to_process_limit = box1.selectbox("Pages to scan", [5, 10, 20, 100, 200, 400, 1200], index=1)
            presets_this_run = box2.selectbox("Preset", ["Test (ELI5)", "Full", "Tweets"], index=1)
            model = box3.selectbox("Model", ["gpt-3.5-turbo", "gpt-4", "groq", "gemini-1.0-pro"])
            temperature = box4.number_input("Temperature for Summary", min_value=0.0, max_value=2.0, value=0.0)
            number_of_front_matter_pages = 0
            # convert to comma separated string list
            sheetnames = ["White B&W Perfect", "White B&W Case", "Cream B&W Perfect", "Cream B&W Case",
                          "Premium Color Paperback", "Premium Color Case", "Standard Color 50 Perfect",
                          "Standard Color 50 Case", "Standard 70 perfect", "Standard 70 Case", "Groundwood Case",
                          "Groundwood Perfect"]

            flags = box1.multiselect("Flags", ["page-by-page-AI"])
            sheetname = box2.selectbox("Binding/Paper", sheetnames)
            read_specs_into_metadata = box3.checkbox("Read specs into metadata?", value=True)
            use_llama_index = box4.checkbox("Use Llama Index to generate synopsis, etc.", value=False)
            spin = st.text_area("Spin", value="Summarize this document.")
            submitted = st.form_submit_button(label='Generate ADEPT Titles')
            st.info('submitted')
            if not submitted:
                st.info(submitted)
            else:

                cumulative_lsi_df = pd.read_csv("output/cumulative_lsi_df.csv")
                if 'page-by-page-AI' in flags:
                    pagebypage = True
                else:
                    pagebypage = False
                pagebypage = True
                if presets_this_run == "Test (ELI5)":
                    presets_this_run = {"ELI5": "ELI5"}
                elif presets_this_run == "Full":
                    presets_this_run = common_presets_for_metadata()
                elif presets_this_run == "Tweets":
                    presets_this_run = {"TweetCountdown": "TweetCountdown"}
                # get the title value for each row in specs_df where select = Tru
                for index, row in chosen_titles_df.iterrows():
                    st.info(f"looping through item {index + 1} of {len(chosen_titles)} selected titles")
                    # temporary fix to inconsistent names in spec_df v. metadatas
                    # rename column
                    row.rename({'Publisher-supplied synopsis': 'Publisher_supplied_synopsis',
                                'Publisher-supplied Keywords': 'Publisher_supplied_Keywords',
                                'tokens in text': 'tokens_in_text'}, inplace=True)
                    # create safe thisdoc_dir filename from base filename
                    filename = row['filename']
                    safedirname = row['title']
                    # check if these keys exist in dataframe
                    needed_keys = ['title', 'filename', 'author', 'ISBN']
                    for n in needed_keys:
                        if n not in chosen_titles_df.columns:
                            st.error("dataframe is missing a required column heading` (key)")
                            st.stop()
                    # if any value in the columns needed_keys within row is na, fill it with placeholder
                    chosen_titles_df[needed_keys] = chosen_titles_df[needed_keys].fillna("placeholder")
                    if len(safedirname) <= 4:
                        if len(row["ISBN"] >= 13):
                            safedirname = row["ISBN"]
                        else:
                            if len(row['author']) >= 3:
                                safedirname = row['author']
                            else:
                                now = datetime.now()

                                # Convert the current datetime to string
                                time_string = now.strftime("%Y-%m-%d-%H:%M:%S")
                                safedirname = time_string

                    safedirname = re.sub(r'\W', '_', safedirname)
                    thisdoc_dir = autils.create_built_thisdoc_dir(safedirname)
                    # truncate thisdoc_dir at 30
                    # thisdoc_dir = thisdoc_dir[:29]
                    st.info(f"thisdoc_dir is {thisdoc_dir}")

                    core = CorePDFProcessor(f"{row['filename']}")
                    metadatas = MDS.Metadatas()
                    metadatas.set_attributes_to_values({'presets_this_run': presets_this_run})
                    metadatas.set_attributes_to_values({'thisdoc_dir': thisdoc_dir})
                    metadatas.set_attributes_to_values({'filepath': row['filename']})
                    metadatas.set_attributes_to_values({'pages_to_process_limit': pages_to_process_limit})
                    metadatas.set_attributes_to_values({'number_of_front_matter_pages': number_of_front_matter_pages})
                    metadatas.set_attributes_to_values({'spin': spin})
                    metadatas.set_attributes_to_values({'flags': flags})
                    # print(metadatas.get_all_attributes())
                    # if page_limit less than length of PDF in pages, excerpt that number of pages
                    # st.info(row['filename'])
                    # st.info(metadatas.get('filepath'))
                    file_to_read = autils.get_pages_limit_from_PDF(metadatas)

with st.status("Analyzing PDF"):
    metadatas = autils.pdf2text_analysis(metadatas, file_to_read)
    st.write(metadatas.get_all_attributes())

with st.status("Populating analytics with info from specs file"):
    metadatas = autils.override_metadata_with_specs(metadatas, row)
    # check override values for title, subtitle, author, publisher-submitted synopsis
    checked_values = metadatas.get_values_for_keys(
        ['title', 'subtitle', 'author',
         'ISBN', 'Publisher_supplied_synopsis', 'submit_synopsis', 'motivation'])
    st.write(checked_values)

with st.status("Creating AI metadata for book as  whole"):
    try:
        # etadatas.get_all_attributes())
        metadatas = core.metadatas2aiservices(metadatas, presets=presets_this_run, model=model,
                                              temperature=temperature, verbose=False)
        st.success(f"Created AI metadata using {len(presets_this_run)} presets.")
        metadatas_dict = metadatas.get_all_attributes()
        # st.json(display_dict, expanded=False)
        metadatas_df = pd.DataFrame.from_dict(metadatas_dict, orient='index')
        metadatas_df.fillna("", inplace=True)
        metadatas_df.sort_index(inplace=True)
        # metadatas_df.to_json(f'{thisdoc_dir}/metadata.json')
        edited_df = st.data_editor(metadatas_df, use_container_width=True)
        metadatas_df = edited_df
        # convert metadatas_df to metadatas object

        edited_df.to_json(f'{thisdoc_dir}/edited_df.json')
    except Exception as e:
        st.error(f"An error occurred in 2ai while processing the PDF: {str(e)}")
        traceback.print_exc()
with st.status("Creating metadata for each page"):
    print(f"pagebypage is {pagebypage}")
    # print(metadatas)
    if pagebypage:
        pagebypagepresets = ['PageByPageSummary', 'PageByPageNotableQuotes']
        metadatas.set_attributes_to_values({'page_by_page_presets': pagebypagepresets})
        try:
            results_df = core.pagebypage2aiservices(metadatas, presets=pagebypagepresets)

            st.success(f"Created page by page analysis using {len(pagebypagepresets)} presets.")
        except Exception as e:
            st.error(
                f"An error occurred in pagebypage2aiservices while processing the PDF: {str(e)}")
    else:
        metadatas.set_attributes_to_values({'page_by_page_presets': ""})

        st.info("Did not create any page by page metadata")

with st.status("creating front matter"):
    try:
        print('creating front matter')
        metadatas = core.create_front_matter(f"{row['filename']}", metadatas,
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
        error_message = traceback.print_exc()
        st.error(f"An error occurred in 2bookjson while processing the PDF: {error_message}")
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

with st.status("creating metadata for distributors"):
    try:
        lsi_df = create_LSI_ACS_spreadsheet(metadatas)
    except Exception as e:
        errormessage = f"error creating metadata for distributors in {e}"
        st.error(errormessage)
        print(errormessage)
    metadatas = metadatas.get_all_attributes()
    ISBN = metadatas['ISBN']
    title = metadatas['title']
    if ISBN:
        # replace special characters with undersocres in ISBN
        ISBN_safe = re.sub(r'\W+', '_', ISBN)
        LSI_ACS_filename = f"{ISBN_safe}_frontmatter.csv"
    else:
        title_safe = re.sub(r'\W+', '_', ISBN)
        LSI_ACS_filename = f"{title_safe}_frontmatter.csdv"

    lsi_df.to_csv(f"{thisdoc_dir}/{LSI_ACS_filename}")
    st.info(f"wrote {LSI_ACS_filename} to {thisdoc_dir}")
    st.write(lsi_df.head())
    cumulative_lsi_df = pd.concat([lsi_df, cumulative_lsi_df])
    cumulative_lsi_df.to_json("output/cumulative_lsi_df.json", orient="table", index=False)

    # st.success("Processing complete!")
    # rain(
    #     emoji="📚",
    #     font_size=54,
    #     falling_speed=5,
    #     animation_length=5)
