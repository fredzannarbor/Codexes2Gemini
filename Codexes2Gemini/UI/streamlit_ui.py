import sys
import streamlit as st
import json
import os
from importlib import resources

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Add the parent of the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from Codexes2Gemini.classes.Codexes.Builders.BuildLauncher import BuildLauncher

def load_json_file(file_name):
    """
    Load a JSON file and return its contents as a dictionary.

    Parameters:
    file_name (str): The name of the JSON file to load.

    Returns:
    dict: The contents of the JSON file as a dictionary.

    Raises:
    None.

    Example:
    >>> load_json_file("data.json")
    {'key1': 'value1', 'key2': 'value2'}
    """
    try:
        with resources.files('Codexes2Gemini.resources.prompts').joinpath(file_name).open('r') as file:
            return json.load(file)
    except Exception as e:
        st.error(f"Error loading JSON file: {e}")
        return {}

def filter_dict(dictionary, filter_text):
    """
    Filters a dictionary based on the presence of a given text in the keys.

    Args:
        dictionary (dict): The dictionary to be filtered.
        filter_text (str): The text to be searched in the dictionary keys.

    Returns:
        dict: A new dictionary containing only the key-value pairs that match the filter_text,
            regardless of case.

    Example:
        >>> my_dict = {'apple': 1, 'banana': 2, 'orange': 3, 'coconut': 4}
        >>> filter_dict(my_dict, 'an')
        {'banana': 2, 'orange': 3}

    """
    return {k: v for k, v in dictionary.items() if filter_text.lower() in k.lower()}

def tab1_user_parameters():

    st.header("Enrich and Build Codexes")

    # Context file paths
    context_files = st.file_uploader("Upload context files (txt)",
                                     type=['txt'],
                                     accept_multiple_files=True)
    context_file_names = []
    for c in context_files:
        context_file_names.append(c.name)

    # Load user prompts dictionary and system instructions
    user_prompts_dict = load_json_file("user_prompts_dict.json")
    system_instructions_dict = load_json_file("system_instructions.json")

    with st.expander("Filter, Select, and Add System Prompts"):
        st.subheader("System Instructions")
        system_instructions_filter = st.text_input("Filter system instructions", "nimble")
        filtered_system_instructions = filter_dict(system_instructions_dict, system_instructions_filter)
        selected_system_instructions = st.multiselect(
            "Select system instructions",
            options=list(filtered_system_instructions.keys()),
            default=[]
        )

        add_system_prompt = st.text_area("Add to system prompt (optional)")

        # Display selected system instructions
        if selected_system_instructions:
            st.write("Selected system instructions:")
            for instruction in selected_system_instructions:
                st.write(system_instructions_dict[instruction])

    # add user-supplied system message



    # Collapsible element for user prompts filtering and selection
    with st.expander("Filtering, Select and Add User Prompts"):
        st.subheader("User Prompts")
        user_prompts_filter = st.text_input("Filter user prompts", "abstracts")
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
                st.write(user_prompts_dict[prompt])

        # Use all user keys
        use_all_user_keys = st.checkbox("Use all user keys from the user prompts dictionary file")

        # Custom user prompt
        user_prompt = st.text_area("Custom user prompt (optional)")

        # Custom user prompt overrides all other user prompts
        user_prompt_override = st.radio("Override?",
                                        ["Override other user prompts", "Add at end of other user prompts"], index=1)
        if user_prompt_override == "Override other user prompts":
            selected_user_prompts = []

    with st.expander("Set Goals"):
        # Mode selection

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

        # Output file path
        output_file = st.text_input("Output file path", "output")

        # Output size limit
        limit = st.number_input("Output size limit in tokens", value=10000)

        # Desired output length
        desired_output_length = st.number_input("Minimum required output length", value=1000)

        # Log level
        log_level = st.selectbox("Log level", ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])

    user_prompts_dict_file_path = resources.files('Codexes2Gemini.resources.prompts').joinpath("user_prompts_dict.json")
    if st.button("Run BuildLauncher"):
        run_build_launcher(selected_user_prompts, selected_system_instructions, user_prompt,
                           context_files, mode, thisdoc_dir, output_file, limit,
                           desired_output_length, log_level, use_all_user_keys, user_prompts_dict_file_path, add_system_prompt)
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
    # Here you can add fields and logic to create multiplan files


def run_build_launcher(selected_user_prompts, selected_system_instructions, user_prompt,
                       context_files, mode, thisdoc_dir, output_file, limit,
                       desired_output_length, log_level, use_all_user_keys, user_prompts_dict_file_path, add_system_prompt):
    """

    Run Build Launcher method.

    Executes the BuildLauncher.main() method with the specified arguments and handles the results.

    Parameters:
    - selected_user_prompts (list): List of selected user prompts.
    - selected_system_instructions (list): List of selected system instructions.
    - user_prompt (str): User input prompt.
    - context_files (list): List of context files.
    - mode (str): Mode of operation.
    - thisdoc_dir (str): Directory of the current document.
    - output_file (str): File path of the output.
    - limit (int): Limit of generated outputs.
    - desired_output_length (int): Desired output length.
    - log_level (str): Log level.
    - use_all_user_keys (bool): Flag indicating whether to use all user keys.

    Returns:
    None

    """
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


def run_build_launcher_with_config(config_data):
    """

    Runs the build launcher with the given configuration data.

    Parameters:
    - config_data: The configuration data for the build launcher.

    Returns:
    None

    Example usage:
    config_data = {
        'param1': value1,
        'param2': value2,
        ...
    }
    run_build_launcher_with_config(config_data)

    """
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
    font-family: 'Google Sans'', sans;
    font-size: 16px;
    font-weight: 300;
}
"""



def run_streamlit_app():
    """
    Runs the Codexes2Gemini Streamlit UI app.

    This method sets the page configuration for the app, including layout, sidebar state, page title, and page icon. It then displays a title and a brief description of the app. Next, it creates three tabs for different sections of the app: "Self-Serve", "Run Build Plans", and "Create Build Plans".

    In the "Self-Serve" tab, the method calls the `tab1_user_parameters()` function to display the user parameters section.

    In the "Run Build Plans" tab, the method calls the `tab2_upload_config()` function to display the configuration upload section.

    In the "Create Build Plans" tab, the method calls the `tab3_create_multiplan()` function to display the multiplan creation section.

    Parameters:
        None

    Returns:
        None
    """
    st.set_page_config(layout="wide", initial_sidebar_state="expanded", page_title="Codexes2Gemini Streamlit UI Demo",
                       page_icon=":book:")
    apply_custom_css(custom_css)
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