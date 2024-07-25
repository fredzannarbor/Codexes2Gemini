import streamlit as st
import json
import os
from Codexes2Gemini.classes.Codexes.Builders.BuildLauncher import BuildLauncher
import sys
from importlib import resources

def load_json_file(file_name):
    try:
        with resources.files('Codexes2Gemini.resources.prompts').joinpath(file_name).open('r') as file:
            return json.load(file)
    except Exception as e:
        st.error(f"Error loading JSON file: {e}")
        return {}

def filter_dict(dictionary, filter_text):
    return {k: v for k, v in dictionary.items() if filter_text.lower() in k.lower()}

def tab1_user_parameters():
    st.header("Enrich and Build Codexes")

    # Context file paths
    context_files = st.file_uploader("Upload context files (txt, pdf, epub, mobi)",
                                     type=['txt', 'pdf', 'epub', 'mobi'],
                                     accept_multiple_files=True)

    # Load user prompts dictionary and system instructions
    user_prompts_dict = load_json_file("user_prompts_dict.json")
    system_instructions_dict = load_json_file("system_instructions.json")

    # User prompts filtering and selection
    st.subheader("User Prompts")
    user_prompts_filter = st.text_input("Filter user prompts", "")
    filtered_user_prompts = filter_dict(user_prompts_dict, user_prompts_filter)
    selected_user_prompts = st.multiselect(
        "Select user prompts",
        options=list(filtered_user_prompts.keys()),
        default=[]
    )

    # Display selected user prompts
    if selected_user_prompts:
        st.write("Selected user prompts:")
        for prompt in selected_user_prompts:
            st.text(user_prompts_dict[prompt])

    # System instructions filtering and selection
    st.subheader("System Instructions")
    system_instructions_filter = st.text_input("Filter system instructions", "")
    filtered_system_instructions = filter_dict(system_instructions_dict, system_instructions_filter)
    selected_system_instructions = st.multiselect(
        "Select system instructions",
        options=list(filtered_system_instructions.keys()),
        default=[]
    )

    # Display selected system instructions
    if selected_system_instructions:
        st.write("Selected system instructions:")
        for instruction in selected_system_instructions:
            st.text(system_instructions_dict[instruction])

    # User prompt
    user_prompt = st.text_area("Custom user prompt (optional)")

    # Mode selection
    mode = st.selectbox("Mode of operation", ['part', 'multi_part', 'codex', 'full_codex'])

    thisdoc_dir = st.text_input("Output directory", value=os.path.join(os.getcwd(), 'output'))

    # Output file path
    output_file = st.text_input("Output file path")

    # Output size limit
    limit = st.number_input("Output size limit in tokens", value=10000)

    # Desired output length
    desired_output_length = st.number_input("Minimum required output length", value=2000)

    # Log level
    log_level = st.selectbox("Log level", ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])

    # Use all user keys
    use_all_user_keys = st.checkbox("Use all user keys from the user prompts dictionary file")

    if st.button("Run BuildLauncher"):
        run_build_launcher(selected_user_prompts, selected_system_instructions, user_prompt,
                           context_files, mode, thisdoc_dir, output_file, limit,
                           desired_output_length, log_level, use_all_user_keys)


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
    # Here you can add fields and logic to create multiplan files


def run_build_launcher(selected_user_prompts, selected_system_instructions, user_prompt,
                       context_files, mode, thisdoc_dir, output_file, limit,
                       desired_output_length, log_level, use_all_user_keys):
    args = {
        'mode': mode,
        'output': output_file,
        'limit': limit,
        'user_prompt': user_prompt,
        'log_level': log_level,
        'use_all_user_keys': use_all_user_keys,
        'desired_output_length': desired_output_length,
        'thisdoc_dir': thisdoc_dir,
        'list_of_user_keys_to_use': ','.join(selected_user_prompts),
        'list_of_system_keys': ','.join(selected_system_instructions)
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


def run_build_launcher_with_config(config_data):
    launcher = BuildLauncher()
    results = launcher.main(config_data)

    st.write("Results:")
    for result in results:
        st.write(result)


def run_streamlit_app():
    st.set_page_config(layout="wide", initial_sidebar_state="expanded", page_title="Codexes2Gemini Streamlit UI Demo",
                       page_icon=":book:")

    st.title("Codexes2Gemini")
    st.write("_Humans and large-context language models making books richer, more diverse, and more surprising._")

    tab1, tab2, tab3 = st.tabs(["Self-Serve", "Run Build Plans", "Create Build Plans"])

    with tab1:
        tab1_user_parameters()

    with tab2:
        tab2_upload_config()

    with tab3:
        tab3_create_multiplan()


def main(port=1455):
    """
    Run the Streamlit application.

    This method has one job: launch streamlit.  All the functional logic is in run_streamlit_app.

    Parameters:
    - port (int): The port to run the Streamlit application on. Default is 1455.

    Returns:
    None
    """
    sys.argv = ["streamlit", "run", __file__, f"--server.port={port}"]
    import streamlit.web.cli as stcli
    stcli.main()


if __name__ == "__main__":
    run_streamlit_app()