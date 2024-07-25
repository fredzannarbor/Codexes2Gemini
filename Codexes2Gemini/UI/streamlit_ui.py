

import streamlit as st
import json
import os
from Codexes2Gemini.classes.Codexes.Builders.BuildLauncher import BuildLauncher
import sys


def run_streamlit_app():
    """

    This method is used to run an optional Streamlit application for the Codexes2Gemini build launcher. It initializes the Streamlit page configuration, sets the title of the page, and prompts the user for various inputs.  This method has all the functional logic for the streamlit UI.

    Parameters:
        None

    Returns:
        None

    Example usage:
        run_streamlit_app()
    """
    st.set_page_config(layout="wide", initial_sidebar_state="expanded", page_title="Codexes2Gemini Streamlit UI Demo", page_icon=":book:")

    st.title("Build Launcher")

    # User prompt
    user_prompt = st.text_area("User prompt")

    # Context file paths
    context_files = st.file_uploader("Upload context files (txt, pdf, epub, mobi)",
                                     type=['txt', 'pdf', 'epub', 'mobi'],
                                     accept_multiple_files=True)

    # Mode selection
    mode = st.selectbox("Mode of operation", ['part', 'multi_part', 'codex', 'full_codex'])

    thisdoc_dir = st.text_input("Output directory", value=os.path.join(os.getcwd(), 'output'))

    # Output file path
    output_file = st.text_input("Output file path")

    # Output size limit
    limit = st.number_input("Output size limit in tokens", value=10000)

    # Desired output length
    desired_output_length = st.number_input("Minimum required output length", value=2000)

    # File upload for configuration
    config_file = st.file_uploader("Upload JSON configuration file", type="json")

    # Plans JSON file
    plans_json_file = st.file_uploader("Upload JSON file containing multiple plans", type="json")

    # Use all user keys
    use_all_user_keys = st.checkbox("Use all user keys from the user prompts dictionary file specified in the configuration file below")

    # Log level
    log_level = st.selectbox("Log level", ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])

    if st.button("Run BuildLauncher"):
        # Prepare arguments for BuildLauncher
        args = {
            'mode': mode,
            'output': output_file,
            'limit': limit,
            'user_prompt': user_prompt,
            'log_level': log_level,
            'use_all_user_keys': use_all_user_keys,
            'desired_output_length': desired_output_length,
            'thisdoc_dir': thisdoc_dir
        }

        # Handle file uploads
        if config_file:
            config_data = json.load(config_file)
            args['config'] = config_data

        if context_files:
            # Save uploaded files temporarily and pass their paths
            context_file_paths = []
            for file in context_files:
                with open(file.name, "wb") as f:
                    f.write(file.getbuffer())
                context_file_paths.append(file.name)
            args['context_file_paths'] = context_file_paths

        if plans_json_file:
            plans_data = json.load(plans_json_file)
            args['plans_json'] = plans_data
            st.write("Plans data loaded:", plans_data)  # Debug output

        launcher = BuildLauncher()
        results = launcher.main(args)

        # Display results
        st.write("Results:")
        for i, result in enumerate(results):
            st.write(f"{result}")

        # Clean up temporary files
        if context_files:
            for file in context_files:
                os.remove(file.name)

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