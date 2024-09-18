import json
from importlib import resources

import streamlit as st


def filter_dict(dictionary, filter_text):
    return {k: v for k, v in dictionary.items() if
            filter_text.lower() in k.lower() or (
                    isinstance(v, dict) and filter_text.lower() in v.get('prompt', '').lower())}


def load_json_file(file_name):
    try:
        with resources.files('resources.prompts').joinpath(file_name).open('r') as file:
            return json.load(file)
    except Exception as e:
        st.error(f"Error loading JSON file: {e}")
        return {}


def results2assembled_pandoc_markdown_with_latex(results):
    """
    Assembles results into separate Pandoc Markdown documents with LaTeX preambles.

    Args:
        results: A list of lists, where each inner list represents a document's results.

    Returns:
        A list of strings, each representing a complete Pandoc Markdown document.
    """

    assembled_documents = []  # List to store complete documents

    try:
        if not isinstance(results, list):
            st.warning("results is not a list")
            return []

        for result_set in results:
            assembled_pandoc_markdown_with_latex = ""  # Initialize for each document

            json_string = result_set[0]
            # check if json_string is json
            try:
                json_data = json.loads(json_string)
            except Exception as e:
                st.error("Can't extract json data from result")
                st.error(traceback.format_exc())
                continue

            # check if this is a basic info result
            if "gemini_title" or "gemini_authors" in json_string:
                # Extract values from JSON
                gemini_title = json_data.get("gemini_title", "TBD")
                gemini_subtitle = json_data.get("gemini_subtitle", "TBD")
                gemini_authors = json_data.get("gemini_authors", "TBD")

                # Create LaTeX preamble for this document
                latex_preamble = create_latex_preamble(gemini_title, gemini_subtitle, gemini_authors)

                # Append preamble to the document's content
                assembled_pandoc_markdown_with_latex += latex_preamble

            for i in range(1, len(result_set)):
                assembled_pandoc_markdown_with_latex += result_set[i] + "\n\n"

            # Add the complete document to the list
            assembled_documents.append(assembled_pandoc_markdown_with_latex)

    except Exception as e:
        st.error(e)
        st.error(traceback.format_exc())

    return assembled_documents  # Return the list of assembled documents
