import inspect
import sys
print("Python path:")
for path in sys.path:
    print(path)
import os

print("Current working directory:", os.getcwd())
import random
import streamlit as st
import json
from typing import Dict, List, Counter
import base64
from importlib import resources
import pandas as pd

import Codexes2Gemini
print("Codexes2Gemini location:", Codexes2Gemini.__file__)

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
#from ..classes.user_space import UserSpace, save_user_space, load_user_space

print("UserSpace methods:", dir(UserSpace))
user_space = load_user_space()
print("user_space methods:", dir(user_space))
print("user_space type:", type(user_space))
YOUR_API_KEY = os.environ['GOOGLE_API_KEY']

def load_json_file(file_name):
    try:
        with resources.files('Codexes2Gemini.resources.prompts').joinpath(file_name).open('r') as file:
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

def tab2_upload_config():
    st.header("Upload Plan Files")

    config_file = st.file_uploader("Upload JSON configuration file", type="json")

    if config_file is not None:
        config_data = json.load(config_file)
        st.json(config_data)

        if st.button("Run BuildLauncher with Uploaded Config"):
            if 'multiplan' in config_data:
                for plan in config_data['multiplan']:
                    if 'context_files' in plan:
                        context = "\n".join(plan['context_files'].values())
                        plan['context'] = context

                    if 'minimum_required_output_tokens' not in plan or plan['minimum_required_output_tokens'] is None:
                        plan['minimum_required_output_tokens'] = 1000

            run_build_launcher_with_config(config_data)

def count_tokens(text, model='models/gemini-1.5-pro'):
    model = genai.GenerativeModel(model)
    response = model.count_tokens(text)
    return response.total_tokens

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

def multi_plan_builder(user_space: UserSpace):
    st.header("Multi-Prompt Codex Analyzer and Builder")

    if 'multiplan' not in st.session_state:
        st.session_state.multiplan = []

    user_prompts_dict = load_json_file("user_prompts_dict.json")
    system_instructions_dict = load_json_file("system_instructions.json")

    with st.form("new_prompt_plan"):
        st.subheader("Create New Prompt Plan")
        plan_name = st.text_input("Plan Name")

        st.subheader("Context")
        context_filter = st.text_input("Filter saved contexts")
        filtered_contexts = user_space.get_filtered_contexts(context_filter)
        selected_saved_context = st.selectbox(
            "Select a saved context",
            options=[""] + list(filtered_contexts.keys()),
            format_func=lambda x: f"{x}: {filtered_contexts[x].content[:50]}..." if x else "None"
        )

        context_files = st.file_uploader("Upload new context files", accept_multiple_files=True,
                                         help="May be up to 10M tokens of text or ~40MB (!)")

        context_content = ""
        total_tokens = 0
        total_mb = 0

        if selected_saved_context:
            context_content = filtered_contexts[selected_saved_context].content

        if context_files:
            new_content = "\n\n".join([read_file_content(file) for file in context_files])
            context_content += ("\n\n" + new_content) if context_content else new_content

        if context_content:
            total_tokens = count_tokens(context_content)
            total_mb = tokens_to_millions(total_tokens)
            st.info(f"Total tokens in context: {total_tokens:,} (approximately {total_mb:.2f} MB)")

        new_context_name = st.text_input("Save this context as (optional)")
        new_context_tags = st.text_input("Context tags (comma-separated, optional)")
        if st.form_submit_button("Save New Context"):
            if new_context_name and context_content:
                user_space.save_context(new_context_name, context_content, new_context_tags.split(',') if new_context_tags else None)
                save_user_space(user_space)
                st.success(f"Context '{new_context_name}' saved successfully.")

        with st.expander("Enter System Instructions"):
            st.subheader("System Instructions")
            system_filter = st.text_input("Filter system instructions")
            filtered_system = filter_dict(system_instructions_dict, system_filter)
            selected_system_instructions = st.multiselect(
                "Select system instructions",
                options=list(filtered_system.keys()),
                format_func=lambda x: f"{x}: {filtered_system[x]['prompt'][:50]}..."
            )

        with st.expander("Enter User Prompts"):
            st.subheader("User Prompts")
            user_filter = st.text_input("Filter user prompts")
            filtered_user = filter_dict(user_prompts_dict, user_filter)
            selected_user_prompts = st.multiselect(
                "Select user prompts",
                options=list(filtered_user.keys()),
                format_func=lambda x: f"{x}: {filtered_user[x]['prompt'][:50]}..."
            )

            custom_user_prompt = st.text_area("Custom User Prompt (optional)")

        with st.expander("Set Output Destinations"):
            mode_options = [
                "Single Part of a Book (Part)",
                "Multiple Parts of a Book (Multi-Part)",
                "Basic Codex (Codex)",
                "Comprehensive Codex (Full Codex)"
            ]
            mode_mapping = {
                "Single Part of a Book (Part)": 'part',
                "Multiple Parts of a Book (Multi-Part)": 'multi_part',
                "Basic Codex (Codex)": 'codex',
                "Comprehensive Codex (Full Codex)": 'full_codex'
            }
            selected_mode_label = st.selectbox("Create This Type of Codex Object:", mode_options)
            mode = mode_mapping[selected_mode_label]

            if not os.path.exists(os.path.join(os.getcwd(), 'output', 'c2g')):
                os.makedirs(os.path.join(os.getcwd(), 'output', 'c2g'), exist_ok=True)

            thisdoc_dir = st.text_input("Output directory", value=os.path.join(os.getcwd(), 'output', 'c2g'))
            if not os.path.exists(thisdoc_dir):
                try:
                    os.makedirs(thisdoc_dir, exist_ok=True)
                except:
                    logging.error(f"Could not create directory {thisdoc_dir}, falling back to 'output/c2g'")
                    thisdoc_dir = os.path.join(os.getcwd(), 'output', 'c2g')

            output_file = st.text_input("Output filename base", "output")

        with st.expander("Set Output Requirements"):
            with st.container(border=True):
                limit = st.number_input("Maximum output size in tokens", value=8000, step=500)
                ensure_output_limit = st.checkbox("Ensure Minimum Output Tokens", value=False)
                minimum_required_output_tokens = st.number_input("Minimum required output tokens", value=500, step=500,
                                                                 help="latest Gemini-1.5 max is 8192")
                st.warning(
                    "Important: the above limits will be applied to *all* prompts in this plan. If you need a prompt to have a different limit, it must have its own plan.")

            log_level = st.selectbox("Log level", ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])

        submitted = st.form_submit_button("Add Plan")
        if submitted:
            new_plan = {
                "name": plan_name,
                "mode": mode,
                "context": context_content,
                "context_total_tokens": total_tokens,
                "context_total_mb": total_mb,
                "system_instructions": selected_system_instructions,
                "user_prompts": selected_user_prompts,
                "custom_user_prompt": custom_user_prompt,
                "ensure_output_limit": ensure_output_limit,
                "minimum_required_output_tokens": minimum_required_output_tokens,
                "limit": limit,
                "log_level": log_level,
                "output_file": output_file,
                "thisdoc_dir": thisdoc_dir
            }
            st.session_state.multiplan.append(new_plan)
            st.success(
                f"Plan '{plan_name}' added to multiplan (Context: {total_tokens:,} tokens, approximately {total_mb:.3f} M)")

    if st.session_state.multiplan:
        st.subheader("Current Multiplan")
        for i, plan in enumerate(st.session_state.multiplan):
            with st.expander(f"Plan {i + 1}: {plan['name']}"):
                truncated_plan = plan.copy()
                truncated_plan['context'] = truncated_plan['context'][:1000] + "..." if len(truncated_plan['context']) > 1000 else truncated_plan['context']
                st.json(truncated_plan)
                if st.button(f"View Full Context for Plan {i + 1}"):
                    st.text_area("Full Context", value=plan['context'], height=300)
                if st.button(f"Remove Plan {i + 1}"):
                    st.session_state.multiplan.pop(i)
                    st.rerun()

    if st.session_state.multiplan:
        if st.button("Run Multiplan"):
            run_multiplan(st.session_state.multiplan, user_prompts_dict)
            user_space.save_prompt_plan({"multiplan": st.session_state.multiplan})
            save_user_space(user_space)
            st.success("Multiplan saved to UserSpace")

def run_multiplan(multiplan, user_prompts_dict):
    launcher = BuildLauncher()
    results = []
    for plan in multiplan:
        user_prompts = []
        for prompt_key in plan['user_prompts']:
            if prompt_key in user_prompts_dict:
                user_prompts.append(user_prompts_dict[prompt_key]['prompt'])

        if plan['custom_user_prompt']:
            user_prompts.append(plan['custom_user_prompt'])

        combined_user_prompt = "\n".join(user_prompts)

        launcher_plan = {
            'mode': plan['mode'],
            'context': plan['context'],
            'output': f"output_{plan['name']}.md",
            'limit': plan['minimum_required_output_tokens'],
            'selected_system_instructions': plan['system_instructions'],
            'user_prompt': combined_user_prompt,
            'list_of_user_keys_to_use': plan['user_prompts'],
            'minimum_required_output_tokens': plan['minimum_required_output_tokens'],
        }

        try:
            result = launcher.main(launcher_plan)
            results.append(result)
        except Exception as e:
            st.error(f"Error processing plan '{plan['name']}': {str(e)}")

    st.subheader("Multiplan Results")
    st.write(results)

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
            [(name, context.content[:50] + "...", ", ".join(context.tags)) for name, context in filtered_contexts.items()],
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
    if user_space.results:
        result_df = pd.DataFrame(
            [(r["timestamp"], r["result"][:50] + "...") for r in user_space.results],
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

def run_build_launcher_with_config(config_data):
    launcher = BuildLauncher()
    results = launcher.main(config_data)

    st.write("Results:")
    for result in results:
        st.write(result)

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
        multi_plan_builder(user_space)

    with tab2:
        tab2_upload_config()

    with tab4:
        user_space_app(user_space)

def main(port=1455, themebase="light"):
    sys.argv = ["streamlit", "run", __file__, f"--server.port={port}", f'--theme.base={themebase}', f'--server.maxUploadSize=40']
    import streamlit.web.cli as stcli
    stcli.main()
    configure_logger("DEBUG")

if __name__ == "__main__":
    run_streamlit_app()