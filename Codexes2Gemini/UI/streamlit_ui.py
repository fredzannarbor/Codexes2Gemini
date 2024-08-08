import base64
import json
import os
import random
import sys
import time
import traceback
from importlib import resources
from typing import Dict
from datetime import datetime
from pprint import pprint
import pandas as pd
import streamlit as st
from streamlit_carousel import carousel


#print("Codexes2Gemini location:", Codexes2Gemini.__file__)

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
from Codexes2Gemini.classes.Utilities.utilities import configure_logger
from Codexes2Gemini.classes.user_space import UserSpace, save_user_space, load_user_space
from Codexes2Gemini.classes.Codexes.Builders.PromptPlan import PromptPlan

logger = configure_logger("DEBUG")
logging.info("--- Began logging ---")
user_space = load_user_space()
logger.debug(f"user_space: {user_space}")

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
        with resources.files('Codexes2Gemini.resources.prompts').joinpath(file_name).open('r') as file:
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

def load_json_carousel_file(file_name):
    try:
        with resources.files('Codexes2Gemini.resources.images').joinpath(file_name).open('r') as file:
            return json.load(file)
    except Exception as e:
        st.error(f"Error loading JSON file: {e}")
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


def read_file_content(file):
    try:
        return file.getvalue().decode("utf-8")
    except UnicodeDecodeError:
        st.error(f"Error decoding file {file.name}. Make sure it's a text file.")
        return ""


def multiplan_builder(user_space: UserSpace):
    st.header("Multi-Prompt Codex Analyzer and Builder")

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

    user_prompts_dict = load_json_file("user_prompts_dict.json")
    system_instructions_dict = load_json_file("system_instructions.json")

    # Display image carousel
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
    context_choice = st.radio("Choose context source:", ["Upload New Context", "Select Saved Context", "Skip Context"])

    context_selected = False
    if context_choice == "Upload New Context":
        with st.form("step_1_upload"):
            uploaded_files = st.file_uploader("Upload new context files", accept_multiple_files=True)
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
        truncate_plan_values_for_display(plan)

    # Step 2: Instructions and Prompts
    st.subheader("Step 2: Instructions and Prompts")
    instruction_cols = st.columns(4)
    instructions_images = load_json_carousel_file('instructions_info.json')
    display_image_row(instruction_cols, instructions_images)

    with st.form("step2-instructions-prompts"):
        with st.expander("Enter System Instructions"):
            system_filter = st.text_input("Filter system instructions")
            filtered_system = filter_dict(system_instructions_dict, system_filter)
            selected_system_instructions = st.multiselect(
                "Select system instructions",
                options=list(filtered_system.keys()),
                format_func=lambda x: f"{x}: {filtered_system[x]['prompt'][:50]}..."
            )

        with st.expander("Enter User Prompts"):
            user_filter = st.text_input("Filter user prompts")
            filtered_user = filter_dict(user_prompts_dict, user_filter)
            selected_user_prompt = ""
            selected_user_prompts = st.multiselect(
                "Select user prompts",
                options=list(filtered_user.keys()),
                format_func=lambda x: f"{x}: {filtered_user[x]['prompt'][:50]}..."
            )
            for key in selected_user_prompts:
                selected_user_prompt = selected_user_prompt + "\n" + user_prompts_dict[key]['prompt']
                selected_user_prompt_values = user_prompts_dict[key]['prompt']
            custom_user_prompt = st.text_area("Custom User Prompt (optional)")
            user_prompt_override = st.radio("Override?",
                                            ["Override other user prompts", "Add at end of other user prompts"],
                                            index=1)
            if user_prompt_override == "Override other user prompts":
                user_prompt = custom_user_prompt
            else:
                user_prompt = selected_user_prompt + '/n' + custom_user_prompt

        instructions_submitted = st.form_submit_button("Save Instructions and Continue",
                                                       disabled=not context_selected)

    if instructions_submitted:

        st.session_state.current_plan.update({
            "system_instructions": selected_system_instructions,
            "user_prompts": selected_user_prompts,
            "selected_user_prompt": selected_user_prompt,
            "selected_user_prompt_values": selected_user_prompt_values,
            "custom_user_prompt": custom_user_prompt,
            "user prompt_override": user_prompt_override,
            "user_prompt": user_prompt,
            "user_prompts_dict": user_prompts_dict
        })
        st.success("Instructions and prompts saved.")

    # Step 3: Output Settings
    st.subheader("Step 3: Output Settings")
    with st.form("step3-output-settings"):
        with st.expander("Set Output Requirements"):
            mode_options = ["Single Part of a Book (Part)"]
            mode_mapping = {"Single Part of a Book (Part)": 'part'}
            selected_mode_label = st.selectbox("Create This Type of Codex Object:", mode_options)
            mode = mode_mapping[selected_mode_label]
            maximum_output_tokens = st.number_input("Maximum output size in tokens", value=8000, step=500)
            minimum_required_output = st.checkbox("Ensure Minimum Output", value=False)
            minimum_required_output_tokens = st.number_input("Minimum required output tokens", value=50, step=500)

        with st.expander("Set Output Destinations"):
            thisdoc_dir = st.text_input("Output directory", value=os.path.join(os.getcwd(), 'output', 'c2g'))
            output_file = st.text_input("Output filename base", "output")
            log_level = st.selectbox("Log level", ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
            plan_name = st.text_input("Plan Name", value=st.session_state.current_plan.get('name', ''))

        # Check conditions for enabling the submit button
        context_selected = 'context' in st.session_state.current_plan or context_choice == "Skip Context"
        instructions_selected = (
                len(st.session_state.current_plan.get('system_instructions', [])) > 0 or
                len(st.session_state.current_plan.get('user_prompts', [])) > 0 or
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
        })
        st.session_state.multiplan.append(st.session_state.current_plan)
        st.success(f"Plan '{plan_name}' added to multiplan")
        st.session_state.current_plan = {}

    # Display current multiplan
    if st.session_state.multiplan:
        st.subheader("Current Multiplan")
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
            run_multiplan(st.session_state.multiplan, user_space)
            user_space.save_prompt_plan({"multiplan": st.session_state.multiplan})
            st.success("Multiplan and results saved to your Userspace tab.")


def truncate_plan_values_for_display(plan):
    truncated_plan = plan.copy()
    truncated_plan['context'] = truncated_plan['context'][:1000] + "..." if len(
        truncated_plan['context']) > 1000 else truncated_plan['context']
    # drop key user_prompt_dict
    truncated_plan['user_prompts_dict'] = {"prompt": "User prompt dict passed into function, available in debug log"}

    st.json(truncated_plan)


def display_image_row(cols, image_info):
    for col, info in zip(cols, image_info):
        with col:
            st.markdown(
                f'<a href="{info["link"]}" target="_blank">'
                f'<div class="image-container"><img src="data:image/png;base64,{image_to_base64(info["path"])}"/></div>'
                f'</a>'
                f'<div class="caption">{info["caption"]}</div>',
                unsafe_allow_html=True
            )
    st.markdown('</div>', unsafe_allow_html=True)


def run_multiplan(multiplan, user_space):
    print("--- Beginning to Run Multiplan ---")
    launcher = BuildLauncher()
    results = []
    #print(type(multiplan))
    for plan in multiplan:
        print(plan['mode'])
        launcher_plan = {
            'mode': plan['mode'],
            'context': plan['context'],
            'output': f"output_{plan['name']}.md",
            'selected_system_instructions': plan['system_instructions'],
            'user_prompt': plan['user_prompt'],
            'selected_user_prompt_values': plan['selected_user_prompt_values'],
            'list_of_user_keys_to_use': plan['user_prompts'],
            'maximum_output_tokens': plan['maximum_output_tokens'],
            'minimum_required_output': plan['minimum_required_output'],
            'minimum_required_output_tokens': plan['minimum_required_output_tokens'],
            'user_prompts_dict': plan['user_prompts_dict']
        }
        logger.debug(truncate_plan_values_for_display(launcher_plan))
        try:
            result = launcher.main(launcher_plan)
            st.write(f"Result for {plan['name']}")
        except Exception as e:
            st.error(f"Error processing plan '{plan['name']}': {str(e)}")
            st.write(traceback.format_exc())
        results.append(result)
        st.write(results)
    st.subheader("Multiplan Results")
    user_space.add_result('results', results)
    st.write(user_space.results)
    save_user_space(user_space)

def display_full_context(context_files):
    for filename, content in context_files.items():
        st.subheader(f"File: {filename}")
        st.text_area("Content", value=content, height=300, disabled=True)


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
    st.title("UserSpace")

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

    st.header("Saved Prompts")
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
    #st.write(user_space.results)
    # if user_space.results:
    #     result_df = pd.DataFrame(
    #         [(r["timestamp"], r["results"][:50] + "...") for r in user_space.results],
    #         columns=["Timestamp", "Result Preview"]
    #     )
    #     st.table(result_df)
    #     if st.button("Clear All Results"):
    #         user_space.results = []
    #         save_user_space(user_space)
    #         st.success("All results cleared")
    #         st.rerun()

    st.header("Saved Prompt Plans")
    if user_space.prompt_plans:
        table_header = st.columns(2)
        table_header[0].header("Plan")
        table_header[1].header("Download Link")

        for i, plan in enumerate(user_space.prompt_plans):
            row = st.columns(2)
            with open(f"prompt_plan_{i}.json", "w") as f:
                json.dump(plan, f)
            row[0].json(plan, expanded=False)
            row[1].markdown(get_binary_file_downloader_html(f"prompt_plan_{i}.json", f"Prompt Plan {i + 1}"),
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
    st.set_page_config(layout="wide", initial_sidebar_state="expanded", page_title="Codexes2Gemini Streamlit UI Demo",
                       page_icon=":book:")
    st.title("Codexes2Gemini")
    st.write("_Humans and large-context language models making books richer, more diverse, and more surprising._")

    user_space = load_user_space()

    if not hasattr(user_space, 'prompts'):
        st.warning("Loaded UserSpace object is invalid. Creating a new UserSpace.")
        user_space = UserSpace()
        save_user_space(user_space)

    tab1, tab2, tab4 = st.tabs(["Multi-Prompt Codex Builder", "Run Build Plans", "UserSpace"])

    with tab1:
        multiplan_builder(user_space)

    with tab2:
        upload_build_plan()

    with tab4:
        user_space_app(user_space)


def main(port=1455, themebase="light"):
    sys.argv = ["streamlit", "run", __file__, f"--server.port={port}", f'--theme.base={themebase}',
                f'--server.maxUploadSize=40']
    import streamlit.web.cli as stcli
    stcli.main()
    configure_logger("DEBUG")


if __name__ == "__main__":
    run_streamlit_app()
