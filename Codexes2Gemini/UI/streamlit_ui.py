import sys
import random

import streamlit as st
import json
from typing import Dict, List, Counter
import base64
from importlib import resources
import pandas as pd
import os
import tempfile
import google.generativeai as genai


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


def self_serve_single_plan(user_space: UserSpace):
    st.header("Enrich and Build Codexes")

    context_files = st.file_uploader("Upload context files (txt)",
                                     type=['txt'],
                                     accept_multiple_files=True, help="Maximum 2 million tokens")
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

def count_tokens(context, model='models/gemini-1.5-flash-001'):
    model = genai.GenerativeModel()
    return model.count_tokens(context)


def multi_plan_builder(user_space: UserSpace):
    st.header("Multi-Plan Builder")

    if 'multiplan' not in st.session_state:
        st.session_state.multiplan = []

    # Load prompt dictionaries
    user_prompts_dict = load_json_file("user_prompts_dict.json")
    system_instructions_dict = load_json_file("system_instructions.json")

    # Form for creating a new prompt plan
    with st.form("new_prompt_plan"):
        st.subheader("Create New Prompt Plan")
        plan_name = st.text_input("Plan Name")
        mode = st.selectbox("Mode", ['part', 'multi_part', 'codex', 'full_codex'])
        context_files = st.file_uploader("Upload context files", accept_multiple_files=True)

        # System instructions selection
        st.subheader("System Instructions")
        system_filter = st.text_input("Filter system instructions")
        filtered_system = filter_dict(system_instructions_dict, system_filter)
        selected_system_instructions = st.multiselect(
            "Select system instructions",
            options=list(filtered_system.keys()),
            format_func=lambda x: f"{x}: {filtered_system[x]['prompt'][:50]}..."
        )

        # User prompts selection
        st.subheader("User Prompts")
        user_filter = st.text_input("Filter user prompts")
        filtered_user = filter_dict(user_prompts_dict, user_filter)
        selected_user_prompts = st.multiselect(
            "Select user prompts",
            options=list(filtered_user.keys()),
            format_func=lambda x: f"{x}: {filtered_user[x]['prompt'][:50]}..."
        )

        custom_user_prompt = st.text_area("Custom User Prompt (optional)")
        desired_output_length = st.number_input("Desired Output Length", min_value=1, value=1000)

        submitted = st.form_submit_button("Add Plan")
        if submitted:
            context_contents = {}
            for file in context_files:
                context_contents[file.name] = file.getvalue().decode("utf-8")

            new_plan = {
                "name": plan_name,
                "mode": mode,
                "context_files": context_contents,
                "system_instructions": selected_system_instructions,
                "user_prompts": selected_user_prompts,
                "custom_user_prompt": custom_user_prompt,
                "desired_output_length": desired_output_length
            }
            st.session_state.multiplan.append(new_plan)
            st.success(f"Plan '{plan_name}' added to multiplan")

    # Display current multiplan
    if st.session_state.multiplan:
        st.subheader("Current Multiplan")
        for i, plan in enumerate(st.session_state.multiplan):
            st.write(f"Plan {i + 1}: {plan['name']}")
            st.json(truncate_context_files(plan))
            if st.button(f"Remove Plan {i + 1}"):
                st.session_state.multiplan.pop(i)
                st.rerun()

    # Save and run multiplan
    if st.session_state.multiplan:
        if st.button("Run Multiplan"):
            run_multiplan(st.session_state.multiplan)
            user_space.save_prompt_plan({"multiplan": st.session_state.multiplan})
            save_user_space(user_space)
            st.success("Multiplan saved to UserSpace")


def run_multiplan(multiplan):
    launcher = BuildLauncher()
    results = []
    for plan in multiplan:
        # Create temporary files for context
        temp_context_files = []
        for filename, content in plan['context_files'].items():
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                temp_file.write(content)
                temp_context_files.append(temp_file.name)

        # Load the user prompts dictionary
        user_prompts_dict = load_json_file("user_prompts_dict.json")

        # Prepare the user prompts
        user_prompts = []
        for prompt_key in plan['user_prompts']:
            if prompt_key in user_prompts_dict:
                user_prompts.append(user_prompts_dict[prompt_key]['prompt'])

        # Add the custom user prompt if it exists
        if plan['custom_user_prompt']:
            user_prompts.append(plan['custom_user_prompt'])

        # Join all user prompts into a single string
        combined_user_prompt = "\n".join(user_prompts)

        print(combined_user_prompt)

        # Convert the plan to the format expected by BuildLauncher
        launcher_plan = {
            'mode': plan['mode'],
            'context_file_paths': temp_context_files,
            'output': f"output_{plan['name']}.md",
            'limit': plan['desired_output_length'],
            'selected_system_instructions': plan['system_instructions'],
            'user_prompt': combined_user_prompt,
            'list_of_user_keys_to_use': plan['user_prompts'],
            'desired_output_length': plan['desired_output_length'],
        }

        try:
            result = launcher.main(launcher_plan)
            results.append(result)
        finally:
            # Clean up temporary files
            for temp_file in temp_context_files:
                os.unlink(temp_file)

    st.subheader("Multiplan Results")
    # for i, result in enumerate(results):
    #     st.write(f"Result for Plan {i + 1}:")
    #     st.write(result)
    st.write(results)

# Helper functions
def filter_dict(dictionary, filter_text):
    return {k: v for k, v in dictionary.items() if
            filter_text.lower() in k.lower() or (
                        isinstance(v, dict) and filter_text.lower() in v.get('prompt', '').lower())}


def load_json_file(file_name):
    try:
        with resources.files('Codexes2Gemini.resources.prompts').joinpath(file_name).open('r') as file:
            return json.load(file)
    except Exception as e:
        st.error(f"Error loading JSON file: {e}")
        return {}

def truncate_context_files(plan: Dict) -> Dict:
    """
    Nondestructively replaces the value of plan["context_files"] with a version truncated after 50 Gemini tokens.

    Args:
        plan: A dictionary representing a prompt plan.

    Returns:
        A new dictionary with the truncated context files.
    """

    truncated_plan = plan.copy()  # Create a copy to avoid modifying the original

    for filename, content in truncated_plan["context_files"].items():
        # Tokenize the content using the Gemini API tokenizer


        truncated_content = content[:240] + " ..." # Truncate the content based on token count
        truncated_plan["context_files"][filename] = truncated_content

    return truncated_plan



def filter_dict(dictionary, filter_text):
    return {k: v for k, v in dictionary.items() if
            filter_text.lower() in k.lower() or (
                        isinstance(v, dict) and filter_text.lower() in v.get('prompt', '').lower())}


def load_json_file(file_name):
    try:
        with resources.files('Codexes2Gemini.resources.prompts').joinpath(file_name).open('r') as file:
            return json.load(file)
    except Exception as e:
        st.error(f"Error loading JSON file: {e}")
        return {}

def user_space_app(user_space: UserSpace):
    st.title("UserSpace")

    # Add a button to clear the entire user space
    if st.button("Clear Entire UserSpace"):
            user_space = UserSpace()  # Create a new, empty UserSpace
            save_user_space(user_space)
            st.success("UserSpace has been cleared.")
            st.rerun()  # Rerun the app to reflect the changes

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
        if st.button("Clear All Filters"):
            user_space.filters = {}
            save_user_space(user_space)
            st.success("All filters cleared")
            st.rerun()

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
        if st.button("Clear All Prompts"):
            user_space.prompts = {}
            save_user_space(user_space)
            st.success("All prompts cleared")
            st.rerun()

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
        if st.button("Clear All Context Files"):
            user_space.context_files = {}
            save_user_space(user_space)
            st.success("All context files cleared")
            st.rerun()

    # Results
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
        if st.button("Clear All Prompt Plans"):
            user_space.prompt_plans = []
            save_user_space(user_space)
            st.success("All prompt plans cleared")
            st.rerun()

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
    tab1, tab2, tab3, tab4 = st.tabs(["Multi-Prompt Codex Builder", "Run Build Plans", "Self-Serve", "UserSpace"])

    with tab1:
        multi_plan_builder(user_space)

    with tab3:
        self_serve_single_plan(user_space)

    with tab2:
        tab2_upload_config()



    with tab4:
        user_space_app(user_space)

def main(port=1455):
    sys.argv = ["streamlit", "run", __file__, f"--server.port={port}"]
    import streamlit.web.cli as stcli
    stcli.main()


if __name__ == "__main__":
    run_streamlit_app()