import sys
import random

import streamlit as st
import json
from typing import Dict, List, Counter
import base64
from importlib import resources
import pandas as pd
import os

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Add the parent of the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from Codexes2Gemini.classes.Codexes.Builders.BuildLauncher import BuildLauncher
from Codexes2Gemini.classes.user_space import UserSpace, save_user_space, load_user_space


def load_json_file(file_name):
    try:
        with resources.files('Codexes2Gemini.resources.prompts').joinpath(file_name).open('r') as file:
            return json.load(file)
    except Exception as e:
        st.error(f"Error loading JSON file: {e}")
        return {}


def filter_dict(dictionary, filter_text):
    return {k: v for k, v in dictionary.items() if
            filter_text.lower() in k.lower() or (isinstance(v, str) and filter_text.lower() in v.lower())}

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


def tab1_user_parameters(user_space: UserSpace):
    st.header("Enrich and Build Codexes")

    context_files = st.file_uploader("Upload context files (txt)",
                                     type=['txt'],
                                     accept_multiple_files=True)
    context_file_names = [c.name for c in context_files]

    user_prompts_dict = load_json_file("user_prompts_dict.json")
    system_instructions_dict = load_json_file("system_instructions.json")

    with st.expander("Filter, Select, and Add System Prompts", expanded=True):
        st.subheader("System Instructions")

        if 'system_instructions_filter' not in st.session_state:
            st.session_state.system_instructions_filter = ""
        if 'filtered_system_instructions' not in st.session_state:
            st.session_state.filtered_system_instructions = system_instructions_dict
        if 'system_selected_tag' not in st.session_state:
            st.session_state.system_selected_tag = None


        system_tag_freq = create_tag_frequencies(system_instructions_dict)
        display_tag_cloud(system_tag_freq, "system_tag")

        # Check if a tag was clicked
        params = st.query_params
        if "system_tag" in params:
            clicked_tag = params["system_tag"]
            st.session_state.filtered_system_instructions = {k: v for k, v in system_instructions_dict.items() if
                                                             clicked_tag in v['tags']}
            st.session_state.system_selected_tag = clicked_tag
            st.query_params.clear()  # Clear the query parameter
            st.toast(f"Showing prompts tagged with: {clicked_tag}")
            st.rerun()

        system_instructions_filter = st.text_input("Filter system instructions",
                                                   value=st.session_state.system_instructions_filter)
        if system_instructions_filter != st.session_state.system_instructions_filter:
            st.session_state.system_instructions_filter = system_instructions_filter
            st.session_state.filtered_system_instructions = filter_dict(system_instructions_dict,
                                                                        system_instructions_filter)

        all_system_instructions = list(st.session_state.filtered_system_instructions.keys()) + list(
            user_space.filters.keys())

        if st.session_state.system_selected_tag:
            st.info(f"Filtering for tag: {st.session_state.system_selected_tag}")

        selected_system_instructions = st.multiselect(
            "Select system instructions",
            options=all_system_instructions,
            default=[]
        )

        add_system_prompt = st.text_area("Add to system prompt (optional)")

        if selected_system_instructions:
            st.write("Selected system instructions:")
            for instruction in selected_system_instructions:
                if instruction in system_instructions_dict:
                    st.write(system_instructions_dict[instruction]['prompt'])
                elif instruction in user_space.filters:
                    st.write(user_space.filters[instruction])

    with st.expander("Filtering, Select and Add User Prompts", expanded=True):
        st.subheader("User Prompts")

        if 'user_prompts_filter' not in st.session_state:
            st.session_state.user_prompts_filter = ""
        if 'filtered_user_prompts' not in st.session_state:
            st.session_state.filtered_user_prompts = user_prompts_dict
        if 'user_selected_tag' not in st.session_state:
            st.session_state.user_selected_tag = None

        user_tag_freq = create_tag_frequencies(user_prompts_dict)
        display_tag_cloud(user_tag_freq, "user_tag")

        # Check if a tag was clicked
        if "user_tag" in params:
            clicked_tag = params["user_tag"]
            st.session_state.filtered_user_prompts = {k: v for k, v in user_prompts_dict.items() if
                                                      clicked_tag in v['tags']}
            st.session_state.user_selected_tag = clicked_tag
            st.query_params.clear()  # Clear the query parameter
            st.toast(f"Showing prompts tagged with: {clicked_tag}")
            st.rerun()

        user_prompts_filter = st.text_input("Filter user prompts", value=st.session_state.user_prompts_filter,
                                            help="Filter for prompts containing this term")
        if user_prompts_filter != st.session_state.user_prompts_filter:
            st.session_state.user_prompts_filter = user_prompts_filter
            st.session_state.filtered_user_prompts = filter_dict(user_prompts_dict, user_prompts_filter)

        all_user_prompts = list(st.session_state.filtered_user_prompts.keys()) + list(user_space.prompts.keys())

        if st.session_state.user_selected_tag:
            st.info(f"Filtering for tag: {st.session_state.user_selected_tag}")

        selected_user_prompts = st.multiselect(
            "Select user prompts",
            options=all_user_prompts,
            default=[]
        )

        if selected_user_prompts:
            st.write("Selected user prompts:")
            for prompt in selected_user_prompts:
                if prompt in user_prompts_dict:
                    st.write(user_prompts_dict[prompt]['prompt'])
                elif prompt in user_space.prompts:
                    st.write(user_space.prompts[prompt])

        use_all_user_keys = st.checkbox("Use all user keys from the user prompts dictionary file")

        user_prompt = st.text_area("Custom user prompt (optional)")

        user_prompt_override = st.radio("Override?",
                                        ["Override other user prompts", "Add at end of other user prompts"], index=1)
        if user_prompt_override == "Override other user prompts":
            selected_user_prompts = []
    with st.expander("Set Goals"):
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

        thisdoc_dir = st.text_input("Output directory", value=os.path.join(os.getcwd(), 'output/c2g'))

        output_file = st.text_input("Output file path", "output")

        limit = st.number_input("Output size limit in tokens", value=10000)

        desired_output_length = st.number_input("Minimum required output length", value=1000)

        log_level = st.selectbox("Log level", ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])

    user_prompts_dict_file_path = resources.files('Codexes2Gemini.resources.prompts').joinpath("user_prompts_dict.json")
    if st.button("Run BuildLauncher"):
        result = run_build_launcher(selected_user_prompts, selected_system_instructions, user_prompt,
                                    context_files, mode, thisdoc_dir, output_file, limit,
                                    desired_output_length, log_level, use_all_user_keys, user_prompts_dict_file_path,
                                    add_system_prompt)

        # Save result and prompt plan to user space
        user_space.save_result(result[0])
        user_space.save_prompt_plan({
            "mode": mode,
            "user_prompts": selected_user_prompts,
            "system_instructions": selected_system_instructions,
            "custom_prompt": user_prompt,
            "desired_output_length": desired_output_length
        })
        save_user_space(user_space)
        st.success("Result and Prompt Plan saved to UserSpace")

    with st.expander("Debugging Information"):
        st.info(
            f"**Submitting**:\n"
            f"- **Selected User Prompts**: {selected_user_prompts}\n"
            f"- **Selected System Instructions**: {selected_system_instructions}\n"
            f"- **User Prompt**: {user_prompt}\n"
            f"- **Context Files**: {context_files}\n"
            f"- **Mode**: {mode}\n"
            f"- **Thisdoc Directory**: {thisdoc_dir}\n"
            f"- **Output File**: {output_file}\n"
            f"- **Limit**: {limit}\n"
            f"- **Desired Output Length**: {desired_output_length}\n"
            f"- **Log Level**: {log_level}\n"
            f"- **Use All User Keys**: {use_all_user_keys}"
        )

def tab2_upload_config():
    st.header("Upload Plan Files")

    config_file = st.file_uploader("Upload JSON configuration file", type="json")

    if config_file is not None:
        config_data = json.load(config_file)
        st.json(config_data)

        if st.button("Run BuildLauncher with Uploaded Config"):
            run_build_launcher_with_config(config_data)


def tab3_create_multiplan():
    st.header("Create PromptPlan Multiplan Files")

    st.write("This feature is not yet implemented.")


def user_space_app(user_space: UserSpace):
    st.title("UserSpace")

    # Filters
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

    # Display saved filters
    if user_space.filters:
        filter_df = pd.DataFrame(
            [(name, json.dumps(data)[:50] + "...") for name, data in user_space.filters.items()],
            columns=["Name", "Data Preview"]
        )
        st.table(filter_df)

    # Prompts
    st.header("Saved Prompts")
    prompt_name = st.text_input("Prompt Name (optional)")
    prompt = st.text_area("Prompt")
    if st.button("Save Prompt"):
        user_space.save_prompt(prompt_name, prompt)
        save_user_space(user_space)
        st.success("Prompt saved")

    # Display saved prompts
    if user_space.prompts:
        prompt_df = pd.DataFrame(
            [(name, text[:50] + "...") for name, text in user_space.prompts.items()],
            columns=["Name", "Prompt Preview"]
        )
        st.table(prompt_df)

    # Context Files
    st.header("Saved Context Files")
    context_name = st.text_input("Context Group Name")
    context_files = st.text_area("Context Files (one path per line)")
    if st.button("Save Context Files"):
        user_space.save_context_files(context_name, context_files.split('\n'))
        save_user_space(user_space)
        st.success("Context files saved")

    # Display saved context files
    if user_space.context_files:
        context_df = pd.DataFrame(
            [(name, ", ".join(files[:3]) + ("..." if len(files) > 3 else ""))
             for name, files in user_space.context_files.items()],
            columns=["Name", "Files Preview"]
        )
        st.table(context_df)

    # Results
    st.header("Saved Results")
    if user_space.results:
        result_df = pd.DataFrame(
            [(r["timestamp"], r["result"][:50] + "...") for r in user_space.results],
            columns=["Timestamp", "Result Preview"]
        )
        st.table(result_df)

        for i, result in enumerate(user_space.results):
            with open(f"result_{i}.txt", "w") as f:
                f.write(result["result"])
            st.markdown(get_binary_file_downloader_html(f"result_{i}.txt", f"Result {i + 1}"), unsafe_allow_html=True)

    # Prompt Plans
    st.header("Saved Prompt Plans")
    if user_space.prompt_plans:
        for i, plan in enumerate(user_space.prompt_plans):
            st.write(f"Prompt Plan {i + 1}")
            st.json(plan)
            with open(f"prompt_plan_{i}.json", "w") as f:
                json.dump(plan, f)
            st.markdown(get_binary_file_downloader_html(f"prompt_plan_{i}.json", f"Prompt Plan {i + 1}"),
                        unsafe_allow_html=True)


def run_build_launcher(selected_user_prompts, selected_system_instructions, user_prompt,
                       context_files, mode, thisdoc_dir, output_file, limit,
                       desired_output_length, log_level, use_all_user_keys, user_prompts_dict_file_path,
                       add_system_prompt):
    args = {
        'mode': mode,
        'output': output_file,
        'limit': limit,
        'selected_system_instructions': selected_system_instructions,
        'user_prompt': user_prompt,
        'log_level': log_level,
        'use_all_user_keys': use_all_user_keys,
        'desired_output_length': desired_output_length,
        'thisdoc_dir': thisdoc_dir,
        'list_of_user_keys_to_use': selected_user_prompts,  # Pass the list directly
        'list_of_system_keys': selected_system_instructions,  # Pass the list directly
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

    # Try to load existing UserSpace
    user_space = load_user_space()

    # Check if 'prompts' attribute exists
    if not hasattr(user_space, 'prompts'):
        st.warning("Loaded UserSpace object is invalid. Creating a new UserSpace.")
        user_space = UserSpace()
        save_user_space(user_space)

    # Rest of the function remains the same
    tab1, tab2, tab3, tab4 = st.tabs(["Self-Serve", "Run Build Plans", "Create Build Plans", "UserSpace"])

    with tab1:
        tab1_user_parameters(user_space)

    with tab2:
        tab2_upload_config()

    with tab3:
        tab3_create_multiplan()

    with tab4:
        user_space_app(user_space)


def main(port=1455):
    sys.argv = ["streamlit", "run", __file__, f"--server.port={port}"]
    import streamlit.web.cli as stcli
    stcli.main()


if __name__ == "__main__":
    run_streamlit_app()