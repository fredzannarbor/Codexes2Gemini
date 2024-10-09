import base64
import io
import json
import os

import sys
import tempfile

import time
import traceback

from datetime import datetime
from importlib import resources
from io import BytesIO
from typing import Dict

import chardet
import docx2txt
import fitz  # PyMuPDF
import pandas as pd
import pypandoc
import streamlit as st
from Codexes2Gemini.classes.Codexes.Metadata.Metadatas import Metadatas
from docx import Document

from Codexes2Gemini.classes.Codexes.Metadata.metadatas2outputformats import metadatas2bookjson

# TODO add bookjson
# TODO add proofing prompt

# print("Codexes2Gemini location:", Codexes2Gemini.__file__)

current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory
parent_dir = os.path.dirname(current_dir)

# Get the directory above the parent
grandparent_dir = os.path.dirname(parent_dir)

# Append both directories to the Python path
sys.path.append(parent_dir)
sys.path.append(grandparent_dir)

import google.generativeai as genai
import logging
from Codexes2Gemini.classes.Codexes.Fetchers.pg19Fetcher_v2 import PG19FetchAndTrack

from Codexes2Gemini.classes.Codexes.Builders.BuildLauncher import BuildLauncher
from Codexes2Gemini.classes.Utilities.classes_utilities import configure_logger, load_spreadsheet
from Codexes2Gemini.classes.user_space import UserSpace, save_user_space, load_user_space, InstructionPack
from Codexes2Gemini import __version__, __announcements__
from Codexes2Gemini.ui.multi_context_page import MultiContextUI as MCU
from Codexes2Gemini.classes.Codexes.Builders.PromptsPlan import PromptsPlan
from Codexes2Gemini.ui.ui_utilities import results2assembled_pandoc_markdown_with_latex, flatten_and_stringify, \
    markdown2pdf_buffer

logger = configure_logger("DEBUG")
logging.info("--- Began logging ---")
user_space = load_user_space()
# logger.debug(f"user_space: {user_space}")

GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']


def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        import base64
        return base64.b64encode(image_file.read()).decode()


def load_json(file_path: str) -> dict:
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        st.error(f"Error: File not found: {file_path}")
        return {}
    except json.JSONDecodeError:
        st.error(f"Error: Invalid JSON in file: {file_path}")
        return {}


def load_json_file(file_name):
    try:
        with resources.files('resources.prompts').joinpath(file_name).open('r') as file:
            return json.load(file)
    except Exception as e:
        st.error(f"Error loading JSON file: {e}")
        return {}


def load_image_file(file_name):
    try:
        with resources.files('resources.images').joinpath(file_name).open('rb') as file:
            return file.read()
    except Exception as e:
        st.error(f"Error loading image file: {e}")
        return


def get_binary_file_downloader_html(bin_file, file_label='File'):
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}">Download {file_label}</a>'
    return href


def upload_build_plan():
    st.header("Upload Plan File")

    config_file = st.file_uploader("Upload JSON configuration file", type="json")
    if config_file is not None:
        plan = json.load(config_file)
        st.subheader("Review Contents of Uploaded Plan File")
        truncated_plan = plan.copy()
        if 'context' in truncated_plan:
            truncated_plan['context'] = truncated_plan['context'][:1000] + "..." if len(
                truncated_plan['context']) > 1000 else truncated_plan['context']
        st.json(truncated_plan, expanded=False)

        if st.button("Run Uploaded Plan"):
            pass


def count_tokens(text, model='models/gemini-1.5-pro'):
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel(model)
    response = model.count_tokens(text)
    return response.total_tokens


def get_epoch_time_string():
    # Get the current time in seconds since the Unix epoch
    current_time_seconds = time.time()

    # Convert to tenths of a second
    current_time_tenths = int(current_time_seconds * 10)

    # Convert to string
    current_time_string = str(current_time_tenths)

    return current_time_string


def count_context_tokens(context_files):
    total_tokens = 0
    for file in context_files:
        content = file.getvalue().decode("utf-8")
        tokens = count_tokens(content)
        total_tokens += tokens
    return total_tokens


def tokens_to_mb(tokens, bytes_per_token=4):
    bytes_total = tokens * bytes_per_token
    mb_total = bytes_total / (1024 * 1024)
    return mb_total


def tokens_to_millions(tokens):
    return tokens / 1_000_000


def read_file_content(file):
    file_name = file.name.lower()
    content = ""
    st.write(file_name)
    try:
        if file_name.endswith('.txt'):
            raw_data = file.getvalue()
            encoding_result = chardet.detect(raw_data)
            encoding = encoding_result['encoding'] or 'utf-8'
            content = raw_data.decode(encoding)

        elif file_name.endswith('.doc'):
            with tempfile.NamedTemporaryFile(suffix=".doc") as temp_doc:
                temp_doc.write(file.getvalue())
                temp_doc.flush()
                try:
                    docx2txt.process(temp_doc.name, "temp_docx.docx")
                    with open("temp_docx.docx", "r") as docx_file:
                        content = docx_file.read()
                    os.remove("temp_docx.docx")
                except Exception as e:
                    st.error(f"Error converting .doc to .docx: {str(e)}")

        elif file_name.endswith('.docx'):
            try:
                doc = Document(io.BytesIO(file.getvalue()))
                content = "\n".join([para.text for para in doc.paragraphs])
            except Exception as e:
                st.error(f"Error processing .docx file: {str(e)}")

        elif file_name.endswith('.pdf'):
            try:
                pdf = fitz.open(stream=file.getvalue(), filetype="pdf")
                content = ""
                for page_num in range(len(pdf)):
                    page = pdf[page_num]
                    page_text = page.get_text()
                    if page_text.strip():
                        content += page_text
                        content += f"\n\nPage {page_num + 1}\n\n"
                pdf.close()
            except Exception as e:
                st.error(f"Error processing .pdf file: {str(e)}")
        elif file_name.endswith('.json'):
            try:
                data = json.load(file)
                # Extract text from the JSON object
                content = extract_text_from_json(data)
            except Exception as e:
                st.error(f"Error processing .json file: {str(e)}")

        else:
            st.error("Unsupported file type")

        return content

    except Exception as e:
        st.error(f"Error processing file {file.name}: {str(e)}")
        return ""

    except Exception as e:
        st.error(f"Error processing file {file.name}: {str(e)}")
        return ""


def extract_text_from_json(data):
    """
    Extracts text from a JSON object.

    Args:
        data: The JSON object.

    Returns:
        str: The extracted text.
    """
    text = ""
    if isinstance(data, dict):
        for key, value in data.items():
            text += f"{key}: {extract_text_from_json(value)}\n"
    elif isinstance(data, list):
        for item in data:
            text += f"{extract_text_from_json(item)}\n"
    else:
        text = str(data)
    return text


def prompts_plan_builder_ui(user_space: UserSpace):
    st.header("Data Set Explorer")

    # initialize session state

    if 'current_plan' not in st.session_state:
        st.session_state.current_plan = {
            "context_choice": "Random",
            "confirmed_data_set": False,
            "number_of_context_files_to_process": None,
            "file_index": None,
            "selected_system_instruction_keys": [],
            "selected_system_instruction_values": [],
            "complete_system_instruction": "",
            "selected_user_prompt_keys": [],
            "selected_user_prompt_values": [],
            "custom_user_prompt": "",
            "user_prompt_override": False,
            "complete_user_prompt": "",
            "user_prompts_dict": None,
            "selected_user_prompts_dict": {},
            "complete_system_instruction": "",
            "system_instructions_dict": None,
            "name": "",
            "selected_rows": None,
            "filter": "",
            "imprint": "Collapsar"
            #  "system_filter_submitted": system_filter_submitted
        }

    user_prompts_dict = load_json_file("collapsar_user_prompts.json")
    system_instructions_dict = load_json_file("system_instructions.json")
    st.session_state.current_plan.update({"approved_titles": False})
    # selected_rows = pd.read_csv("resources/data_tables/collapsar/sample_row.csv")
    # st.session_state.current_plan.update({"selected_rows": selected_rows.to_dict('records')})

    METADATA_FILE = "data/pg19/metadata.csv"
    DATA_DIRS = [
        "data/pg19/test/test",
        "data/pg19/train/train",
        "data/pg19/validation/validation",
        "data/pg19/ADEPT"
    ]

    # check if PG19 is available

    if not os.path.exists(METADATA_FILE) or not all([os.path.exists(DATA_DIR) for DATA_DIR in DATA_DIRS]):
        error_msg_pg19 = """
        To use this page, you must download the PG19 dataset of text files curated by Google Deepmind from Project Gutenberg. It is *large*: **11.74 GB**.  Place it in the data/ directory.
        ```
        cd Codexes2Gemini/data
        git clone https://github.com/google-deepmind/pg19.git
        ```
        """

        logging.error(error_msg_pg19)
        st.error(error_msg_pg19)
        st.stop()

    FT = PG19FetchAndTrack(METADATA_FILE, DATA_DIRS)
    # Step 1: Context Selection

    st.subheader("Step 1: Context Selection")

    with st.form("Select Data Set"):
        selection_strategy = st.radio("Choose context selection strategy:", ["Random", "User Upload"], index=0)
        uploaded_file = st.file_uploader("Upload CSV file (PG19 format)", type=["csv"],
                                         help="Will be ignored unless you choose Upload option.")
        number_of_context_files_to_process = st.number_input("Number of Context Files to Process (PG19 only)",
                                                             min_value=1, value=3,
                                                             disabled=(selection_strategy == "User Upload"))
        skip_processed = st.checkbox("Skip Already Processed Files from PG19", value=True,
                                     disabled=(selection_strategy == "User Upload"))
        st.session_state.current_plan.update({"skip_processed": skip_processed})

        st.session_state.current_plan.update({"context_choice": selection_strategy})
        initial_documents = st.form_submit_button("Initial Document Selection")
        st.session_state.current_plan.update({"number_of_context_files_to_process": number_of_context_files_to_process})

        # --- Initial Data Selection --
        if initial_documents:
            selected_rows = []  # Initialize empty list for selected rows

            if selection_strategy == "User Upload":
                if uploaded_file:
                    try:
                        selected_rows_df = pd.read_csv(uploaded_file, header=None,  # No header row
                                                       names=['textfilename', 'Title', 'Publication Year', 'URI'],
                                                       # Column names
                                                       dtype={'textfilename': str, 'Title': str, 'URI': str},
                                                       # Specify string types
                                                       parse_dates=['Publication Year'],
                                                       # Parse 'Publication Year' as datetime
                                                       date_parser=lambda x: pd.to_datetime(x, format='%Y')
                                                       # Specify year format
                                                       )
                        selected_rows_df = selected_rows_df.drop_duplicates()
                        # take N random rows from df
                        selected_rows_df = selected_rows_df.sample(n=number_of_context_files_to_process)
                        selected_rows = selected_rows_df.to_dict('records')


                    except Exception as e:
                        st.error(f"Error reading CSV: {e}")




            elif selection_strategy == "Random":
                try:
                    file_index = FT.create_file_index()
                    st.session_state.current_plan.update({"file_index": file_index})
                    st.success("Created file index")
                    selected_rows = FT.fetch_pg19_metadata(number_of_context_files_to_process, selection_strategy)

                    selected_rows_df = pd.DataFrame(selected_rows,
                                                    columns=['textfilename', 'Title', 'Publication Year', 'URI'])


                    selected_rows = selected_rows_df.to_dict('records')

                except Exception as e:
                    st.error(f"Error fetching PG19 data: {e}")

            # --- Display and Edit Selected Rows ---
            if selected_rows:
                # st.info("Selected Rows:")
                edited_df = st.data_editor(selected_rows_df, num_rows="dynamic")
                st.session_state.current_plan.update({"confirmed_data_set": True})

                st.session_state.current_plan.update({"selected_rows": edited_df.to_dict('records')})

                st.session_state.selected_rows_df = edited_df

                st.rerun()

        if 'selected_rows_df' in st.session_state:
            st.subheader("Selected Rows:")
            edited_df = st.data_editor(st.session_state.selected_rows_df, num_rows="dynamic")

    st.subheader("Step 2: Instructions and Prompts")

    with st.expander("Optional: Load Instruction Pack"):
        with st.form("load-instruction-pack"):
            instruction_packs = user_space.get_instruction_packs()

            # Display a selectbox to choose an instruction pack
            selected_pack_name = st.selectbox("Select Instruction Pack", ["-- None --"] + list(instruction_packs.keys()))
            loaded = st.form_submit_button("Load This Pack")
            if loaded:
                if selected_pack_name != "-- None --":
                    selected_pack = instruction_packs[selected_pack_name]

                    st.session_state.current_plan.update({
                        "selected_system_instruction_keys": selected_pack.system_instructions,
                        "selected_user_prompt_keys": list(selected_pack.user_prompts.keys()),
                        "custom_user_prompt": selected_pack.custom_prompt,
                        "user_prompt_override": selected_pack.override
                    })
                    st.rerun()
                else:
                    st.warning("No instruction pack selected, no effect.")

    with st.form("filter-system-instructions"):
        system_filter = st.text_input("Filter system instructions")
        filtered_system = filter_dict(system_instructions_dict, system_filter)
        selected_system_instruction_values = []
        selected_system_instruction_keys = st.multiselect(
            "Select system instructions",
            options=list(filtered_system.keys()),
            default=st.session_state.current_plan.get("selected_system_instruction_keys", []),  # Populate default
            format_func=lambda x: f"{x}: {filtered_system[x]['prompt'][:50]}..."
        )
        for key in selected_system_instruction_keys:
            selected_system_instruction_values.append(system_instructions_dict[key]['prompt'])

        complete_system_instruction = "\n".join(selected_system_instruction_values)

        # Submit button for the system instructions form:
        system_filter_submitted = st.form_submit_button("Select System Instructions")
        if system_filter_submitted:
            st.session_state.current_plan.update({"system_filter_submitted": system_filter_submitted,
                                                  "selected_system_instruction_keys": selected_system_instruction_keys,
                                                  "selected_system_instruction_values": selected_system_instruction_values})



    with st.form("filter-user-prompts2"):
        filter = st.text_input("Filter user prompts", "ADEPT")
        submitted = st.form_submit_button("Filter Now")
        if submitted:
            st.session_state.current_plan.update(
                {"filter": filter}
            )
    with st.form("present-filtered-prompts"):
        filtered_user = filter_dict(user_prompts_dict, st.session_state.current_plan["filter"])
        # st.write(filtered_user.keys())
        selected_user_prompt_keys = st.multiselect(
            "Select user prompt keys",
            options=list(filtered_user.keys()),
            default=st.session_state.current_plan.get("selected_user_prompt_keys", []),  # Populate default
            format_func=lambda x: f"{x}: {filtered_user[x]['prompt'][:50]}..."
        )
        selected_user_prompt_values = [filtered_user[key]['prompt'] for key in selected_user_prompt_keys]
        selected_user_prompts_dict = {key: filtered_user[key]['prompt'] for key in selected_user_prompt_keys}

        filtered_user_prompts = st.form_submit_button("Select these predefined user prompts")
        if filtered_user_prompts:
            st.session_state.current_plan.update({
                "selected_user_prompt_keys": selected_user_prompt_keys,
                "selected_user_prompt_values": selected_user_prompt_values,
                "selected_user_prompts_dict": selected_user_prompts_dict,
            })

    with st.form("add custom_user_prompts"):
        custom_user_prompt = st.text_area("Custom User Prompt (optional)")
        user_prompt_override = st.radio("Override?",
                                        ["Override other user prompts", "Add at end of other user prompts"],
                                        index=1)

        user_prompts_done = st.form_submit_button("Use This Custom Prompt")
        if user_prompts_done:
            st.session_state.current_plan.update({
                "selected_user_prompt_keys": selected_user_prompt_keys,
                "selected_user_prompt_values": selected_user_prompt_values,
                "custom_user_prompt": custom_user_prompt,
                "user_prompt_override": user_prompt_override == "Override other user prompts",
                "user_prompts_dict": selected_user_prompts_dict,
            })

    with st.expander("Optional: Save Instruction Pack", expanded=False):
        with st.form("save-instruction-pack"):
            pack_name = st.text_input("Pack Name")

            if st.form_submit_button("Save Pack"):
                pack = InstructionPack(pack_name,
                                       st.session_state.current_plan["selected_system_instruction_keys"],
                                       st.session_state.current_plan['selected_user_prompts_dict'],
                                       st.session_state.current_plan['custom_user_prompt'],
                                       st.session_state.current_plan['user_prompt_override'])
                user_space.save_instruction_pack(pack)
                st.success(f"Instruction pack '{pack_name}' saved.")

    with st.form("save-instructions-continue"):
        instructions_submitted = st.form_submit_button(
            "Continue",
            disabled=not st.session_state.current_plan["confirmed_data_set"]
        )

        if instructions_submitted:
            st.session_state.current_plan.update({
                "selected_system_instruction_keys": selected_system_instruction_keys,
                "selected_system_instruction_values": selected_system_instruction_values,
                "complete_system_instruction": complete_system_instruction,
                'selected_user_prompt_keys': selected_user_prompt_keys,
                'selected_user_prompt_values': selected_user_prompt_values,
                'custom_user_prompt': custom_user_prompt,
                'user_prompt_override': user_prompt_override,
                'selected_user_prompts_dict': selected_user_prompts_dict,
                'complete_system_instruction': complete_system_instruction,
                'system_instructions_dict': system_instructions_dict,
            })
            st.success("Instructions and prompts saved.")
        # truncate_plan_values_for_display(plan)

    # Step 3: Output Settings
    st.subheader("Step 3: Output Settings")
    with st.form("step3-output-settings"):
        with st.expander("Set Output Requirements"):
            mode_options = ["Full Codex (Codex)"]  # Add "Codex" option
            mode_mapping = {"Single Part of a Book (Part)": 'part',
                            "Full Codex (Codex)": 'codex'}  # Add mapping for "Codex"
            selected_mode_label = st.selectbox("Create This Type of Codex Object:", mode_options)
            mode = mode_mapping[selected_mode_label]
            maximum_output_tokens = 10000000
            minimum_required_output = False
            minimum_required_output_tokens = 10
            require_json_output = st.checkbox("Require JSON Output", value=False)
            imprint = st.selectbox("Imprint", ["Nimble Books LLC", "ADEPT", "Collapsar"], index=2)

        with st.expander("Set Output Destinations"):
            thisdoc_dir = st.text_input("Output directory", value=os.path.join(os.getcwd(), 'processed_data'))
            output_file = st.text_input("Output filename base", "output")
            log_level = st.selectbox("Log level", ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
            plan_name = st.text_input("Plan Name", value=st.session_state.current_plan.get('name', 'Current Plan'))

        submit_disabled = False

        plan_submitted = st.form_submit_button("Accept Output Settings", disabled=submit_disabled)
        #st.write(st.session_state.current_plan)

        if plan_submitted:
            st.session_state.current_plan.update({
                "name": plan_name,
                "mode": mode,
                "thisdoc_dir": thisdoc_dir,
                "output_file": output_file,
                "maximum_output_tokens": maximum_output_tokens,
                "minimum_required_output": minimum_required_output,
                "minimum_required_output_tokens": minimum_required_output_tokens,
                "log_level": log_level,
                "require_json_output": require_json_output,
                "imprint": imprint
            })

            st.success(f"Plan '{plan_name}' updated")

    st.subheader("Step 4: Begin Building from Data Set")

    #show all keys in st.session_state.current_plan
    logging.info(f"session state keys are {st.session_state.current_plan.keys()}")
    logging.info(f"skipping previously processed files: {st.session_state.current_plan['skip_processed']}")
    logging.info(f"selected_rows: {st.session_state.current_plan['selected_rows']}")

    if st.button(f"Build From Data Set {selection_strategy}"):  #
        # st.write(st.session_state.current_plan["selected_rows"])
        PP = PromptsPlan(
            name=st.session_state.current_plan['name'],
            require_json_output=st.session_state.current_plan.get('require_json_output', False),
            context=st.session_state.current_plan.get('context', ''),  # Add context if available
            selected_user_prompts_dict=st.session_state.current_plan['selected_user_prompts_dict'],
            complete_system_instruction=st.session_state.current_plan['complete_system_instruction']
        )

        results = FT.fetch_pg19_data(skip_processed=st.session_state.current_plan['skip_processed'])
        if isinstance(results, str):
            logging.info("results is string")
        elif isinstance(results, list):
            logging.info("results is list")
        # provide_ui_access_to_results(results)

        st.success(f"Successfully built {len(results)} documents and saved them in the output folder {thisdoc_dir}")
        return results


def provide_ui_access_to_results(results):
    if results:
        assembled_documents = results2assembled_pandoc_markdown_with_latex(results)
        for i, document_content in enumerate(assembled_documents):
            codexready_filename = f"ad_hoc_output/codex_{i + 1}"
            try:
                with open(codexready_filename + ".md", "w") as f:
                    f.write(document_content)
                st.info(f"wrote codexready to {codexready_filename}")
            except Exception as e:
                st.error(traceback.format_exc)

            markdown_buffer = BytesIO(document_content.encode())
            download_markdown(codexready_filename, markdown_buffer)
            download_json(codexready_filename, results)

            try:
                # st.write(document_content)
                pdf_buffer = markdown2pdf_buffer(document_content, os.path.join(codexready_filename + ".pdf"))
                # st.write(pdf_buffer)
                if pdf_buffer:  # Check if pdf_buffer is not None
                    download_pdf(codexready_filename, pdf_buffer=pdf_buffer)
                else:
                    st.error("PDF generation failed. Check the logs for details.")

            except Exception as e:
                st.error(f"Error generating or downloading PDF: {e}")
                logging.error(traceback.format_exc())

    return


@st.fragment()
def download_markdown(filename, markdown_buffer=None):
    st.download_button(
        label=f"Download Markdown ({filename}.md)",
        data=markdown_buffer,
        file_name=f"{filename}.md",
        mime="text/markdown"
    )


@st.fragment()
def download_json(filename, results=None):
    json_buffer = BytesIO(json.dumps(results, indent=4).encode())
    st.download_button(
        label=f"Download JSON ({filename}.json)",
        data=json_buffer,
        file_name=f"{filename}.json",
        mime="application/json"
    )


@st.fragment()
def download_pdf(filename, pdf_buffer=None):
    st.download_button(
        label=f"Download PDF ({filename}.pdf)",
        data=pdf_buffer,
        file_name=f"{filename}.pdf",
        mime="application/pdf"
    )




def create_imprint_mission_statement(imprint_name):
    if imprint_name.lower() == "collapsar":
        imprint_mission_statement = """
        
        Collapsar Classics, inspired by the centuries-long popularity of abridgments with readers and the astronomcal marvel of two stars combining into a collapsar, provides condensed reading experiences that distill the essence of each work into an engaging and convenient new format. 
        
        Collapsar books have the following parameters:
 
        - 4" x 6" trim size on high-quality 70-lb paper
        - approximately 350 words per page
        - 36 to 60 pages per book
        - 10,000 - 20,000 words, or 13,000 - 26,000 tokens.
        
    
        "Parts of the book" include humorous and candid Truth in Publishing(tm) disclosures; several different types of abstracts; experimental "image gisting"; learning aids, including mnemonics; a selection of the most important passages in their original wording; a few sample pages from the original book; glossaries for lay and modern readers; several types of indexes; and a specially written "condensed matter" section that captures the spirit and words of the original in a compressed volume.  Every word is reviewed and edited by a highly literate and knowledgeable human.
        
        With Collapsar Classics, you can rediscover the joy of reading—condensed, yet complete. Our meticulous approach ensures every word serves a purpose, whether it's a witty "Truth in Publishing" disclosure, a striking "image gist," or a carefully curated selection of original text. We bring the past alive in a way that's both engaging and insightful, leaving you with a deeper understanding of the book and a desire to explore more.
                
        """

        return imprint_mission_statement

def truncate_plan_values_for_display(plan):
    truncated_plan = plan.copy()
    truncated_plan['context'] = truncated_plan['context'][:500] + "..." if len(
        truncated_plan['context']) > 1000 else truncated_plan['context']
    # drop key user_prompt_dict


    st.json(truncated_plan)


def display_image_row(cols, image_info):
    for col, info in zip(cols, image_info):
        with col:
            image_extension = os.path.splitext(info["path"])[1][1:].lower()
            # Correctly construct the resource path
            image_resource_path = resources.files('Codexes2Gemini.resources.images').joinpath(
                os.path.basename(info["path"]))
            with open(image_resource_path, 'rb') as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode()
                html_content = f"""
                <a href="{info["link"]}" target="_blank">
                    <div class="image-container"><img src="data:image/{image_extension};base64,{encoded_image}"/></div>
                </a>
                <div class="caption">{info["caption"]}</div>
                """
                st.markdown(html_content, unsafe_allow_html=True)


def display_full_context(context_files):
    for filename, content in context_files.items():
        st.subheader(f"File: {filename}")
        st.text_area("Content", value=content, height=300, disabled=True)


def convert_to_pdf(markdown_content):
    if not markdown_content.strip():
        raise ValueError("Markdown content is empty")

    pdf_buffer = BytesIO()
    extra_args = ['--toc', '--toc-depth=2', '--pdf-engine=xelatex']

    try:
        pypandoc.convert_text(
            markdown_content,
            'pdf',
            format='markdown',
            outputfile=pdf_buffer,
            extra_args=extra_args
        )
        pdf_buffer.seek(0)
        return pdf_buffer
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return None


def filter_dict(dictionary, filter_text):
    return {k: v for k, v in dictionary.items() if
            filter_text.lower() in k.lower() or (
                    isinstance(v, dict) and filter_text.lower() in v.get('prompt', '').lower())}


def truncate_context_files(plan: Dict, max_chars=1000) -> Dict:
    truncated_plan = plan.copy()
    truncated_plan["context_files"] = {}
    for filename, content in plan["context_files"].items():
        if len(content) > max_chars:
            truncated_content = content[:max_chars] + f" ... (truncated, full length: {len(content)} characters)"
        else:
            truncated_content = content
        truncated_plan["context_files"][filename] = {
            "content": truncated_content,
            "full_length": len(content),
            "truncated": len(content) > max_chars
        }
    return truncated_plan


def user_space_app(user_space: UserSpace):
    st.title(f"UserSpace: Self")

    st.header("Saved Filters")
    filter_name = st.text_input("Filter Name (optional)")
    filter_data = st.text_area("Filter Data (JSON)")
    if st.button("Save Filter"):
        try:
            user_space.save_filter(filter_name, json.loads(filter_data))
            save_user_space(user_space)
            st.success("Filter saved")
        except json.JSONDecodeError:
            st.error("Invalid JSON for filter data")

    if user_space.filters:
        filter_df = pd.DataFrame(
            [(name, json.dumps(data)[:50] + "...") for name, data in user_space.filters.items()],
            columns=["Name", "Data Preview"]
        )
        st.table(filter_df)
        if st.button("Clear All Filters"):
            user_space.filters = {}
            save_user_space(user_space)
            st.success("All filters cleared")
            st.rerun()

    st.header("Saved Contexts")
    context_filter = st.text_input("Filter contexts")
    filtered_contexts = user_space.get_filtered_contexts(context_filter)

    if filtered_contexts:
        context_df = pd.DataFrame(
            [(name, context.content[:50] + "...", ", ".join(context.tags)) for name, context in
             filtered_contexts.items()],
            columns=["Name", "Content Preview", "Tags"]
        )
        st.table(context_df)
        if st.button("Clear All Contexts"):
            user_space.saved_contexts = {}
            save_user_space(user_space)
            st.success("All contexts cleared")
            st.rerun()


    st.header("Instruction Packs")
    instruction_packs = user_space.get_instruction_packs()

    if instruction_packs:
        pack_df = pd.DataFrame(
            [(name, ", ".join(pack.system_instructions), ", ".join(pack.user_prompts.keys()),
              pack.custom_prompt[:50] + "..." if len(pack.custom_prompt) > 50 else pack.custom_prompt,
              pack.override)
             for name, pack in instruction_packs.items()],
            columns=["Name", "System Instructions", "User Prompt Keys", "Custom Prompt Preview", "Override"]
        )
        st.table(pack_df)

        packs_to_delete = st.multiselect("Select packs to delete", list(instruction_packs.keys()))
        if st.button("Delete Selected Packs") and packs_to_delete:
            for pack_name in packs_to_delete:
                del user_space.instruction_packs[pack_name]
            save_user_space(user_space)
            st.success("Selected instruction packs deleted.")
            st.rerun()
    else:
        st.info("No instruction packs saved yet.")

    st.header("Save Prompts")
    prompt_name = st.text_input("Prompt Name (optional)")
    prompt = st.text_area("Prompt")
    if st.button("Save Prompt"):
        user_space.save_prompt(prompt_name, prompt)
        save_user_space(user_space)
        st.success("Prompt saved")

    if user_space.prompts:
        prompt_df = pd.DataFrame(
            [(name, text[:50] + "...") for name, text in user_space.prompts.items()],
            columns=["Name", "Prompt Preview"]
        )
        st.table(prompt_df)
        if st.button("Clear All Prompts"):
            user_space.prompts = {}
            save_user_space(user_space)
            st.success("All prompts cleared")
            st.rerun()

    st.header("Saved Results")
    st.write(user_space.results)
    if user_space.results:
        result_df = pd.DataFrame(
            [(r["timestamp"], r["results"][:50] + "...") for r in user_space.results],
            columns=["Timestamp", "Result Preview"]
        )
        st.table(result_df)
        if st.button("Clear All Results"):
            user_space.results = []
            save_user_space(user_space)
            st.success("All results cleared")
            st.rerun()

    st.header("Saved Prompt Plans")
    if user_space.prompt_plans:
        table_header = st.columns(2)
        table_header[0].header("Plan")
        table_header[1].header("Download Link")
        username = "self"
        for i, plan in enumerate(user_space.prompt_plans):
            row = st.columns(2)
            with open(f"user_data/{username}/prompt_plan_{i}.json", "w") as f:
                json.dump(plan, f)
            row[0].json(plan, expanded=False)
            row[1].markdown(
                get_binary_file_downloader_html(f"user_data/{username}/prompt_plan_{i}.json", f"Prompt Plan {i + 1}"),
                unsafe_allow_html=True)
        if st.button("Clear All Prompt Plans"):
            user_space.prompt_plans = []
            save_user_space(user_space)
            st.success("All prompt plans cleared")
            st.rerun()

    if st.button("Clear Entire UserSpace"):
        user_space = UserSpace()
        save_user_space(user_space)
        st.success("UserSpace has been cleared.")
        st.rerun()


def run_build_launcher(selected_user_prompts, selected_system_instructions, user_prompt,
                       context_files, mode, thisdoc_dir, output_file, limit,
                       minimum_required_output_tokens, log_level, use_all_user_keys, user_prompts_dict_file_path,
                       add_system_prompt):
    args = {
        'mode': mode,
        'output': output_file,
        'limit': limit,
        'selected_system_instructions': selected_system_instructions,
        'user_prompt': user_prompt,
        'log_level': log_level,
        'use_all_user_keys': use_all_user_keys,
        'minimum_required_output_tokens': minimum_required_output_tokens,
        'thisdoc_dir': thisdoc_dir,
        'list_of_user_keys_to_use': selected_user_prompts,
        'list_of_system_keys': selected_system_instructions,
        'user_prompts_dict_file_path': user_prompts_dict_file_path,
        'selected_user_prompt_keys': st.session_state.current_plan['selected_user_prompt_keys'],
        'selected_user_prompt_values': st.session_state.current_plan['selected_user_prompt_values'],
        'custom_user_prompt': st.session_state.current_plan['custom_user_prompt'],
        'user_prompt_override': st.session_state.current_plan['user_prompt_override'],
    }

    if context_files:
        context_file_paths = []
        for file in context_files:
            with open(file.name, "wb") as f:
                f.write(file.getbuffer())
            context_file_paths.append(file.name)
        args['context_file_paths'] = context_file_paths

    launcher = BuildLauncher()
    results = launcher.main(args)

    st.write("Results:")
    for result in results:
        st.write(result)

    if context_files:
        for file in context_files:
            os.remove(file.name)

    return results


# def display_nested_content(content):
#     if isinstance(content, list):
#         for item in content:
#             display_nested_content(item)
#     elif isinstance(content, str):
#         # Split the content into sections
#         sections = content.split('\n\n')
#         for section in sections:
#             if section.startswith('##'):
#                 # This is a header
#                 st.header(section.strip('# '))
#             elif section.startswith('**'):
#                 # This is a bold section, probably a subheader
#                 st.write(section)
#             elif section.startswith('*'):
#                 # This is a bullet point
#                 st.markdown(section)
#             else:
#                 # This is regular text
#                 st.write(section)
#     else:
#         st.write(content)


def apply_custom_css(css):
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)


custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Google+Sans&display=swap');

body {
    font-family: 'Google Sans', sans-serif;
    font-size: 16px;
    font-weight: 300;
}
"""


def run_streamlit_app():
    st.set_page_config(layout="wide", initial_sidebar_state="expanded", page_title="Codexes2Gemini Streamlit ui Demo",
                       page_icon=":book:")
    st.title("Codexes2Gemini")
    st.markdown("""
    _Humans and AIs working together to make books richer, more diverse, and more surprising._
    """)
    with st.expander("About", expanded=False):
        st.caption(f"Version {__version__}:  {__announcements__}")

    user_space = load_user_space()


    if not hasattr(user_space, 'prompts'):
        st.warning("Loaded UserSpace object is invalid. Creating a new UserSpace.")
        user_space = UserSpace()
        save_user_space(user_space)
    try:
        # Create pages using st.sidebar.selectbox
        page = st.sidebar.selectbox(
            "Select a page",
            ["Create Build Plans", "Dataset Explorer", "Run Saved Plans", "UserSpace"],
        )
        if page == "Create Build Plans":
            final_results = prompts_plan_builder_ui(user_space)
        #   markdown = provide_ui_access_to_results(final_results)
        elif page == "Run Saved Plans":
            upload_build_plan()
        elif page == "Multi-Context Processing":
            multi_context_app = MCU(user_space)
            multi_context_app.render()
        elif page == "UserSpace":
            user_space_app(user_space)
    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.error(traceback.format_exc())



def main(port=1919, themebase="light"):
    sys.argv = ["streamlit", "run", __file__, f"--server.port={port}", f'--theme.base={themebase}',
                f'--server.maxUploadSize=40']
    import streamlit.web.cli as stcli
    stcli.main()
    configure_logger("DEBUG")




if __name__ == "__main__":
    run_streamlit_app()
