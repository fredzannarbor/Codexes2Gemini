import streamlit as st
import json
import os
import sys
from pathlib import Path
from importlib import import_module
from types import ModuleType

# Get the project root directory
project_root = Path(__file__).parents[1].resolve()
classes_dir = project_root / "classes"

# Add project root and classes directory to sys.path
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(classes_dir))


# Custom importer
class CustomImporter:
    @staticmethod
    def find_spec(fullname, path, target=None):
        if fullname in ["PartsBuilder", "CodexBuilder", "PromptPlan", "Codexes2PartsOfTheBook"]:
            return import_module(f"classes.SyntheticBookProduction.{fullname}").__spec__
        return None


# Add the custom importer to sys.meta_path
sys.meta_path.insert(0, CustomImporter)

# Now import BuildLauncher
from classes.SyntheticBookProduction.BuildLauncher import BuildLauncher
from classes.SyntheticBookProduction.PromptPlan import PromptPlan


def main():
    st.title("Book Part and Codex Generator Launcher")

    # File upload for configuration
    config_file = st.file_uploader("Upload JSON configuration file", type="json")

    # Mode selection
    mode = st.selectbox("Mode of operation", ['part', 'multi_part', 'codex', 'full_codex'])

    # Context file paths
    context_files = st.file_uploader("Upload context files (txt, pdf, epub, mobi)",
                                     type=['txt', 'pdf', 'epub', 'mobi'],
                                     accept_multiple_files=True)

    thisdoc_dir = st.text_input("Output directory", value=os.path.join(os.getcwd(), 'output'))

    # Output file path
    output_file = st.text_input("Output file path")

    # Output size limit
    limit = st.number_input("Output size limit in tokens", value=10000)

    # User prompt
    user_prompt = st.text_area("User prompt")

    # Log level
    log_level = st.selectbox("Log level", ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])

    # Use all user keys
    use_all_user_keys = st.checkbox("Use all user keys from the user prompts dictionary file")

    # Desired output length
    desired_output_length = st.number_input("Desired output length", value=5000)

    # Plans JSON file
    plans_json_file = st.file_uploader("Upload JSON file containing multiple plans", type="json")

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

        # In your Streamlit script (UI/streamlit_codex2gemini_ui.py)

        if plans_json_file:
            plans_data = json.load(plans_json_file)
            args['plans_json'] = plans_data
            st.write("Plans data loaded:", plans_data)  # Debug output

        launcher = BuildLauncher()
        results = launcher.main(args)

        # Display results
        st.write("Results:")
        for i, result in enumerate(results):
            st.text_area(f"Result {i + 1}", result, height=200)

        # Clean up temporary files
        if context_files:
            for file in context_files:
                os.remove(file.name)


if __name__ == "__main__":
    main()