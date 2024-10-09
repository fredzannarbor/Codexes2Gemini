import base64
import io
import json
import os
import random
import sys
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
from docx import Document

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

from Codexes2Gemini.classes.Codexes.Builders.BuildLauncher import BuildLauncher
from Codexes2Gemini.classes.Utilities.classes_utilities import configure_logger
from Codexes2Gemini.classes.user_space import UserSpace, save_user_space, load_user_space
from Codexes2Gemini import __version__, __announcements__
from Codexes2Gemini.ui.build_from_dataset_of_codexes import prompts_plan_builder_ui as PPB
from Codexes2Gemini.ui.ui_utilities import results2assembled_pandoc_markdown_with_latex, flatten_and_stringify

logger = configure_logger("DEBUG")
logging.info("--- Began logging ---")
user_space = load_user_space()
#logger.debug(f"user_space: {user_space}")

GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']


# TODO - enable revised_rows = st.data_editor







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
    # construct path the right way
    prompts_resource_path = resources.files('resources.prompts').joinpath(file_name)
    try:
        with prompts_resource_path.open('r') as file:
            # st.info("loaded prompts from source directory")
            return json.load(file)
    except Exception as e:
        with open(f"resources/images/{file_name}", "r") as file:
            return file.read()
    except Exception as e:
        st.error(f"Error loading JSON file: {e}")
        return {}


def load_image_file(file_name):
    try:
        with resources.files('resources.images').joinpath(file_name).open('rb') as file:
            return file.read()
    except Exception as e:
        with open(f"resources/images/{file_name}", "r") as file:
            return file.read()
    except Exception as e:
        st.error(f"Error loading image file: {e}")
        return

def load_json_carousel_file(file_name):
    try:
        with resources.files('resources.images').joinpath(file_name).open('r') as file:
            return json.load(file)
    except Exception as e:
        with open(f"resources/images/{file_name}", "r") as file:
            # st.info("loaded images from source directory")
            return json.load(file)
    except Exception as e:
        st.error(f"Error loading image file: {e}")
        return {}


def get_binary_file_downloader_html(bin_file, file_label='File'):
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}">Download {file_label}</a>'
    return href


def create_tag_frequencies(prompts):
    all_tags = [tag for prompt in prompts.values() for tag in prompt['tags']]
    return Counter(all_tags)


def display_tag_cloud(tag_freq, key_prefix):
    max_freq = max(tag_freq.values())
    min_freq = min(tag_freq.values())

    tag_cloud_html = ""
    for tag, freq in sorted(tag_freq.items()):
        font_size = 1 + (freq - min_freq) / (max_freq - min_freq) * 1.5
        color = f"rgb({random.randint(100, 200)}, {random.randint(100, 200)}, {random.randint(100, 200)})"
        tag_html = f'<a href="?{key_prefix}={tag}" target="_self" style="font-size: {font_size}em; color: {color}; text-decoration: none; margin-right: 10px;">{tag}</a>'
        tag_cloud_html += tag_html

    st.markdown(tag_cloud_html, unsafe_allow_html=True)


def upload_build_plan():
    st.header("Upload Plan File")

    config_file = st.file_uploader("Upload JSON configuration file", type="json")
    if config_file is not None:
        plans = json.load(config_file)

        if 'multiplan' in plans:
            st.subheader("Review Contents of Uploaded Plan File")
            for index, plan in enumerate(plans['multiplan']):
                st.write(f"**Plan {index + 1}**")
                truncated_plan = plan.copy()
                if 'context' in truncated_plan:
                    truncated_plan['context'] = truncated_plan['context'][:1000] + "..." if len(
                        truncated_plan['context']) > 1000 else truncated_plan['context']
                st.json(truncated_plan, expanded=False)

            if st.button("Run Uploaded Plans"):


                run_multiplan(plans['multiplan'], user_space)


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


import tempfile

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

def multiplan_builder(user_space: UserSpace):
    st.header("Analyze and Build")

    # Initialize session state variables
    if 'multiplan' not in st.session_state:
        st.session_state.multiplan = []
    if 'current_plan' not in st.session_state:
        st.session_state.current_plan = {}
    if 'name' not in st.session_state['current_plan']:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        st.session_state.current_plan['name'] = f"New Plan_{timestamp}"
    if 'context_files' not in st.session_state:
        st.session_state.context_files = []
    if 'context_tokens_total' not in st.session_state:
        st.session_state.context_tokens_total = 0
    if 'context_mb_total' not in st.session_state:
        st.session_state.context_mb_total = 0


    user_prompts_dict = load_json_file("user_prompts_dict.json")
    system_instructions_dict = load_json_file("system_instructions.json")

    with st.container():
        st.markdown("""
            <style>
            .fixed-height-container { height: 250px; overflow-y: hidden; }
            .image-container img { height: 200px; width: auto; object-fit: cover; }
            .caption { text-align: left; margin-top: 5px; }
            </style>
        """, unsafe_allow_html=True)

        cols = st.columns(4)
        image_info = load_json_carousel_file('image_info.json')
        display_image_row(cols, image_info)

    # Step 1: Context Selection
    st.subheader("Step 1: Context Selection")
    context_choice = st.radio("Choose context source:", ["Select Saved Context", "Upload New Context","Skip Context"])

    context_selected = False
    if context_choice == "Upload New Context":
        with st.form("step_1_upload"):
            uploaded_files = st.file_uploader("Upload new context files", accept_multiple_files=True,
                                              help="'.txt', '.pdf', '.docx', '.doc', '.json' are supported")
            new_context_name = st.text_input("New context name")
            new_context_tags = st.text_input("Context tags (comma-separated, optional)")
            new_context_submitted = st.form_submit_button("Save New Context")

            if new_context_submitted and uploaded_files:
                # Process and save new context
                context_content = "\n\n".join([read_file_content(file) for file in uploaded_files])
                user_space.save_context(new_context_name, context_content,
                                        new_context_tags.split(',') if new_context_tags else None)
                save_user_space(user_space)
                st.success(f"Context '{new_context_name}' saved successfully.")
                # st.write(context_content)
                total_tokens = count_tokens(context_content)
                total_mb = tokens_to_millions(total_tokens)
                st.session_state.current_plan.update({
                    "context": context_content,
                    "context_total_tokens": total_tokens,
                    "context_total_mb": total_mb
                })
                context_selected = True

    elif context_choice == "Select Saved Context":
        with st.form("step_1_select"):
            context_filter = st.text_input("Filter saved contexts")
            filtered_contexts = user_space.get_filtered_contexts(context_filter)
            selected_saved_context = st.selectbox(
                "Select a saved context",
                options=[""] + list(filtered_contexts.keys()),
                format_func=lambda x: f"{x}: {filtered_contexts[x].content[:50]}..." if x else "None"
            )
            context_submitted = st.form_submit_button("Select This Context")

            if context_submitted and selected_saved_context:
                context_content = filtered_contexts[selected_saved_context].content
                total_tokens = count_tokens(context_content)
                total_mb = tokens_to_millions(total_tokens)
                st.session_state.current_plan.update({
                    "context": context_content,
                    "context_total_tokens": total_tokens,
                    "context_total_mb": total_mb
                })
                st.success(f"Context '{selected_saved_context}' selected successfully.")
                context_selected = True

    elif context_choice == "Skip Context":
        context_selected = True

    # Display current context info
    if 'context' in st.session_state.current_plan and len(st.session_state.current_plan['context']) > 0:
        st.info(f"Current context: {st.session_state.current_plan['context_total_tokens']:,} tokens "
                f"(approximately {st.session_state.current_plan['context_total_mb']:.3f} MB)")
        plan = st.session_state.current_plan


    # Step 2: Instructions and Prompts
    st.subheader("Step 2: Instructions and Prompts")
    instruction_cols = st.columns(4)
    instructions_images = load_json_carousel_file('instructions_info.json')
    display_image_row(instruction_cols, instructions_images)

    with st.form("step2-instructions-prompts"):
        with st.expander("Enter System Instructions"):
            system_filter = st.text_input("Filter system instructions")
            filtered_system = filter_dict(system_instructions_dict, system_filter)
            selected_system_instruction_values = []
            selected_system_instruction_keys = st.multiselect(
                "Select system instructions",
                options=list(filtered_system.keys()),
                format_func=lambda x: f"{x}: {filtered_system[x]['prompt'][:50]}..."
            )
            for key in selected_system_instruction_keys:
                selected_system_instruction_values.append(system_instructions_dict[key]['prompt'])

            complete_system_instruction = "\n".join(selected_system_instruction_values)

        with st.expander("Enter User Prompts"):
            user_filter = st.text_input("Filter user prompts")
            filtered_user = filter_dict(user_prompts_dict, user_filter)

            selected_user_prompt_keys = st.multiselect(
                "Select user prompt keys",
                options=list(filtered_user.keys()),
                format_func=lambda x: f"{x}: {filtered_user[x]['prompt'][:50]}..."
            )

            selected_user_prompt_values = [filtered_user[key]['prompt'] for key in selected_user_prompt_keys]
            selected_user_prompts_dict = {key: filtered_user[key]['prompt'] for key in selected_user_prompt_keys}

            custom_user_prompt = st.text_area("Custom User Prompt (optional)")
            user_prompt_override = st.radio("Override?",
                                            ["Override other user prompts", "Add at end of other user prompts"],
                                            index=1)

            if user_prompt_override == "Override other user prompts":
                complete_user_prompt = custom_user_prompt
            else:
                selected_user_prompt_keys.append("custom_user_prompt")
                selected_user_prompt_values.append(custom_user_prompt)
                complete_user_prompt = "\n".join(selected_user_prompt_values)

            user_prompt_override_bool = user_prompt_override == "Override other user prompts"

        instructions_submitted = st.form_submit_button("Save Instructions and Continue",
                                                       disabled=not context_selected)
            #
        
    if instructions_submitted:
        st.session_state.current_plan.update({
            "selected_system_instruction_keys": selected_system_instruction_keys,
            "selected_system_instruction_values": selected_system_instruction_values,
            "complete_system_instruction": complete_system_instruction,
            'selected_user_prompt_keys': selected_user_prompt_keys,
            'selected_user_prompt_values': selected_user_prompt_values,
            'custom_user_prompt': custom_user_prompt,
            'user_prompt_override': user_prompt_override_bool,
            'complete_user_prompt': complete_user_prompt,
            'user_prompts_dict': user_prompts_dict,
            'selected_user_prompts_dict': selected_user_prompts_dict
        })

        st.success("Instructions and prompts saved.")
        # truncate_plan_values_for_display(plan)

    # Step 3: Output Settings
    st.subheader("Step 3: Output Settings")
    with st.form("step3-output-settings"):
        with st.expander("Set Output Requirements"):
            mode_options = ["Single Part of a Book (Part)", "Full Codex (Codex)"]  # Add "Codex" option
            mode_mapping = {"Single Part of a Book (Part)": 'part',
                            "Full Codex (Codex)": 'codex'}  # Add mapping for "Codex"
            selected_mode_label = st.selectbox("Create This Type of Codex Object:", mode_options)
            mode = mode_mapping[selected_mode_label]
            if mode != 'codex':
                maximum_output_tokens = st.number_input("Maximum output size in tokens", value=8000, step=500)
                minimum_required_output = st.checkbox("Ensure Minimum Output", value=False)
                minimum_required_output_tokens = st.number_input("Minimum required output tokens", value=50, step=500)
            else:
                maximum_output_tokens = 10000000
                minimum_required_output = False
                minimum_required_output_tokens = 50
            require_json_output = st.checkbox("Require JSON Output", value=False)

        with st.expander("Set Output Destinations"):
            thisdoc_dir = st.text_input("Output directory", value=os.path.join(os.getcwd(), 'output', 'c2g'))
            output_file = st.text_input("Output filename base", "output")
            log_level = st.selectbox("Log level", ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
            plan_name = st.text_input("Plan Name", value=st.session_state.current_plan.get('name', ''))

        # Check conditions for enabling the submit button
        context_selected = 'context' in st.session_state.current_plan or context_choice == "Skip Context"
        instructions_selected = (
                len(st.session_state.current_plan.get('selected_system_instruction_keys', [])) > 0 or
                len(st.session_state.current_plan.get('selected_user_prompt_keys', [])) > 0 or
                len(st.session_state.current_plan.get('custom_user_prompt', '')) > 0
        )
        submit_disabled = not (context_selected and instructions_selected)

        plan_submitted = st.form_submit_button("Accept Output Settings", disabled=submit_disabled)

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
            "require_json_output": require_json_output
        })
        st.session_state.multiplan.append(st.session_state.current_plan)
        st.success(f"Plan '{plan_name}' added to multiplan")
        st.session_state.current_plan = {}
    # Display current multiplan
    if st.session_state.multiplan:
        st.subheader("Current Plans")
        for i, plan in enumerate(st.session_state.multiplan):

            with st.expander(f"Plan {i + 1}: {plan['name']}"):

                truncate_plan_values_for_display(plan)

                col1, col2 = st.columns(2)
                with col1:
                    if 'context' in plan and st.button(f"View Full Context for Plan {i + 1}"):
                        st.text_area("Full Context", value=plan['context'], height=300)
                with col2:
                    if st.button(f"Remove Plan {i + 1}"):
                        st.session_state.multiplan.pop(i)
                        st.rerun()

        # Run multiplan button
        if st.button("Run Multiplans"):
            job_results = run_multiplan(st.session_state.multiplan, user_space)
            user_space.save_prompt_plan({"multiplan": st.session_state.multiplan})
            st.success("Multiplan and results saved to your Userspace tab.")
            final_results = process_results(job_results)
            st.write(final_results)

def truncate_plan_values_for_display(plan):
    truncated_plan = plan.copy()
    truncated_plan['context'] = truncated_plan['context'][:500] + "..." if len(
        truncated_plan['context']) > 1000 else truncated_plan['context']
    # drop key user_prompt_dict
    truncated_plan['user_prompts_dict'] = {"prompt": "User prompt dict passed into function, available in debug log"}

    st.json(truncated_plan)


def display_image_row(cols, image_info):
    for col, info in zip(cols, image_info):
        #st.write(image_info)
        with col:
            image_extension = os.path.splitext(info["path"])[1][1:].lower()
            # Correctly construct the resource path

            image_resource_path = resources.files('resources.images').joinpath(
                os.path.basename(info["path"]))
            # check if it exists
            if not image_resource_path.exists():
                image_resource_path = resources.files('resources.images').joinpath(
                    os.path.basename(info["path"]))
            #st.write(image_resource_path)
            with open(image_resource_path, 'rb') as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode()
                html_content = f"""
                <a href="{info["link"]}" target="_blank">
                    <div class="image-container"><img src="data:image/{image_extension};base64,{encoded_image}"/></div>
                </a>
                <div class="caption">{info["caption"]}</div>
                """
                st.markdown(html_content, unsafe_allow_html=True)

def run_multiplan(multiplan, user_space):
    st.info("Beginning to run multiplan")
    launcher = BuildLauncher()

    results = []
    for i, plan in enumerate(multiplan):

        launcher_plan = {
            'mode': plan['mode'],
            'context': plan['context'],
            'output': f"output_{plan['name']}.md",
            'selected_system_instructions': plan['selected_system_instruction_keys'],
            'user_prompt': plan['complete_user_prompt'],
            'selected_user_prompt_values': plan['selected_user_prompt_values'],
            'list_of_user_keys_to_use': plan['selected_user_prompt_keys'],
            'maximum_output_tokens': plan['maximum_output_tokens'],
            'minimum_required_output': plan['minimum_required_output'],
            'minimum_required_output_tokens': plan['minimum_required_output_tokens'],
            'complete_user_prompt': plan['complete_user_prompt'],
            'complete_system_instruction': plan['complete_system_instruction'],
            'selected_system_instructions': plan['selected_system_instruction_keys'],
            'selected_user_prompts_dict': plan['selected_user_prompts_dict'],
            'user_prompts_dict': plan['user_prompts_dict'],
            'log_level': plan['log_level'],
            'require_json_output': plan['require_json_output'],
        }

        try:
            result = launcher.main(launcher_plan)
            results.append(result)
        except Exception as e:
            if "Invalid operation: The `response.parts` quick accessor requires a single candidate" in str(e):
                st.error(f"Error processing plan '{plan['name']}': {str(e)}")
                try:
                    # Assuming 'result' is accessible here and contains the response object
                    st.write("Prompt Feedback:", result.prompt_feedback)
                except Exception as feedback_error:
                    st.error(f"Error accessing prompt feedback: {feedback_error}")
            else:
                st.error(f"Error processing plan '{plan['name']}': {str(e)}")
                st.code(traceback.format_exc())
            continue
    st.subheader("Multiplan Results")
    user_space.add_result('results', results)
    save_user_space(user_space)

    # Add download options for JSON, Markdown, and PDF results
    for i, result_item in enumerate(results):
        st.markdown(f"**Result {i + 1}:**")
        display_nested_content(result_item)

    # for j, result in enumerate(result_list):
    results_filename = f"result_{i + 1}_"
    # markdown display
    return results



def process_results(results):
    if results:
        assembled_documents = results2assembled_pandoc_markdown_with_latex(results)
        for i, document_content in enumerate(assembled_documents):
            codexready_filename = f"output/codexready_{i + 1}_"
            try:
                with open(codexready_filename + ".md", "w") as f:
                    f.write(document_content)
                st.info(f"wrote codexready to {codexready_filename}")
            except Exception as e:
                st.error(traceback.format_exc)
    all_results_filename = datetime.now().strftime('%Y%m%d_%H%M%S')
    st.success("All contexts processed.")

    markdown_content = ''
    if isinstance(results, list):
        # st.info('is list')
        for result in results:
            if isinstance(result, list):
                markdown_content += flatten_and_stringify(result)
            elif isinstance(result, str):
                markdown_content += result
            else:
                # Handle non-string results as needed (e.g., convert to string)
                markdown_content += str(result)
    elif isinstance(results, str):
        st.info('is str')
        markdown_content = results
    else:
        st.error("Unexpected result type. Cannot generate Markdown.")
    # Markdown download
    # st.write(markdown_content[0:100])
    markdown_buffer = BytesIO(markdown_content.encode())

    @st.fragment()
    def download_markdown(filename):
        st.download_button(
            label=f"Download Markdown ({filename}.md)",
            data=markdown_buffer,
            file_name=f"{filename}.md",
            mime="text/markdown"
        )

    download_markdown(all_results_filename)

    @st.fragment()
    def download_json(filename):
        json_buffer = BytesIO(json.dumps(results, indent=4).encode())
        st.download_button(
            label=f"Download JSON ({filename}.json)",
            data=json_buffer,
            file_name=f"{filename}.json",
            mime="application/json"
        )

    download_json(all_results_filename)




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
        result_list = user_space.results["result"][0][0]  # Access the nested list
        result_df = pd.DataFrame(
            [(user_space.results["time"], r[:50] + "...") for r in result_list],  # Iterate over the correct list
            columns=["Timestamp", "Result Preview"]
        )
        result_df['Timestamp'] = pd.to_datetime(result_df['Timestamp'], unit='s').dt.strftime('%Y-%m-%d-%H-%M-%S')
        st.table(result_df)

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
        'user_prompts_dict_file_path': user_prompts_dict_file_path
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


def display_nested_content(content):
    if isinstance(content, list):
        for item in content:
            display_nested_content(item)
    elif isinstance(content, str):
        # Split the content into sections
        sections = content.split('\n\n')
        for section in sections:
            if section.startswith('##'):
                # This is a header
                st.header(section.strip('# '))
            elif section.startswith('**'):
                # This is a bold section, probably a subheader
                st.write(section)
            elif section.startswith('*'):
                # This is a bullet point
                st.markdown(section)
            else:
                # This is regular text
                st.write(section)
    else:
        st.write(content)

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
    ## _Humans and AIs working together to make books richer, more diverse, and more surprising._
    """)
    with st.expander("About", expanded=False):
        st.caption(f"Version {__version__}:  {__announcements__}")

    user_space = load_user_space()
    # ensure_availability_of_required_resources()
    if not hasattr(user_space, 'prompts'):
        st.warning("Loaded UserSpace object is invalid. Creating a new UserSpace.")
        user_space = UserSpace()
        save_user_space(user_space)

        # Create pages using st.sidebar.selectbox
    page = st.sidebar.selectbox(
        "Select a page",
        ["Create Build Plans", "Dataset of Codexes => New Dataset of Codexes", "Run Saved Plans", "UserSpace"],
    )
    if page == "Create Build Plans":
        multiplan_builder(user_space)
    elif page == "Dataset of Codexes => New Dataset of Codexes":
        PPB(user_space)
    elif page == "Run Saved Plans":
        upload_build_plan()
    # elif page == "Multi-Context Processing":
    #     multi_context_app = MCU(user_space)
    #     multi_context_app.render()
    elif page == "UserSpace":
        user_space_app(user_space)


def main(port=1455, themebase="light"):
    sys.argv = ["streamlit", "run", __file__, f"--server.port={port}", f'--theme.base={themebase}',
                f'--server.maxUploadSize=40']
    import streamlit.web.cli as stcli
    stcli.main()
    configure_logger("DEBUG")


if __name__ == "__main__":
    run_streamlit_app()
