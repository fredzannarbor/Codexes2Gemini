import json
import logging
import traceback
from importlib import resources
from io import BytesIO
import tempfile
import pypandoc
import streamlit as st
from rich import print


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


# FIX force line wrap if author > 30 charaters
def create_latex_preamble(gemini_title="TBD", gemini_subtitle="TBD", gemini_authors="TBD", paperwidth=4, paperheight=6,
                          top=0.25, bottom=0.25, right=0.25, left=0.5, includehead=True, includefoot=True,
                          documentclass="book", output="pdf_document", fontsize=10, mainfont=None):

    if isinstance(gemini_authors, list):
        gemini_authors_str = "\n".join([f"- {author}" for author in gemini_authors])
    else:
        gemini_authors_str = gemini_authors
    if gemini_subtitle is None:
        gemini_subtitle = " "
    if "\"" or ":" in gemini_authors_str and len(gemini_authors_str > 0):
        gemini_authors_str = gemini_authors_str.replace("\"", "'").replace(":", "")
    # Wrap author field if longer than 30 characters
    if len(gemini_authors_str) > 30:
        gemini_authors_str = f"\\parbox[t]{{\\textwidth}}{{{gemini_authors_str}}}"
    st.session_state.current_plan.update({"gemini_authors_str": gemini_authors_str})
    yaml_preamble = f"""---
title: "{gemini_title}"
author: '{gemini_authors_str}'
subtitle: "{gemini_subtitle}"
header-includes:
  - \\usepackage[paperwidth={paperwidth}in, paperheight={paperheight}in, top={top}in, bottom=0.25in, right=0.25in, left=0.5in, includehead, includefoot]{{geometry}} # 
  - \\usepackage{{fancyhdr}}
  - \\pagestyle{{fancy}}
  - \\fancyhf{{}}
  - \\fancyfoot[C]{{
     \\thepage
     }}
  - \\usepackage{{longtable}} 
  - \\pagenumbering{{arabic}}
documentclass: {documentclass}
output: pdf_document
fontsize: {fontsize}
---

"""
    return yaml_preamble



# TODO make condensed matter longer
# TODO include more random text or full body
# FIX do not include exceprts from the Context

def results2assembled_pandoc_markdown_with_latex(results):
    assembled_documents = []

    for item in results:

        assembled_pandoc_markdown_with_latex = ""

        # --- JSON Parsing Logic Starts Here ---
        # Remove leading/trailing whitespace and quotes
        cleaned_item = item.strip(' "')

        try:
            # Attempt to parse as JSON
            json_data = json.loads(cleaned_item)

            # Handle basic info result (check for keys anywhere in the object)
            if any(key in json_data for key in ["gemini_title", "gemini_authors"]):
                gemini_title = json_data.get("gemini_title", "TBD")
                gemini_subtitle = json_data.get("gemini_subtitle", "TBD")
                gemini_authors = json_data.get("gemini_authors", "TBD")
                gemini_summary = json_data.get("gemini_summary", "TBD")
                st.session_state.current_plan['gemini_title'] = gemini_title
                st.session_state.current_plan['gemini_subtitle'] = gemini_subtitle
                st.session_state.current_plan['gemini_authors'] = gemini_authors
                st.session_state.current_plan['gemini_summary'] = gemini_summary


                # Create and prepend LaTeX preamble
                latex_preamble = create_latex_preamble(gemini_title, gemini_subtitle, gemini_authors)
                assembled_pandoc_markdown_with_latex += latex_preamble + "\n\n"
            else:
                # If it's valid JSON but not the expected format, treat as plain text
                assembled_pandoc_markdown_with_latex += cleaned_item + "\n\n"

        except json.JSONDecodeError:
            # Handle non-JSON elements (e.g., append as plain text)
            #  st.write('list item is string:')
            # st.write(item)
            assembled_pandoc_markdown_with_latex += item + "\n\n"
        # --- JSON Parsing Logic Ends Here ---

        assembled_pandoc_markdown_with_latex = clean_up_markdown(assembled_pandoc_markdown_with_latex)
        assembled_documents.append(assembled_pandoc_markdown_with_latex)

    return assembled_documents


def clean_up_markdown(markdown_content):
    """
    Fixes common errors in markdown
    1. Ensure that all headings # begin their line and are not preceded by a space
    2. Ensure that all headings are preceded and followed by new lines.
    """
    # Ensure headings begin their line and are not preceded by a space
    markdown_content = markdown_content.replace(" #", "\n#")

    # Remove > 2 new lines in a row repeatedly
    while "\n\n\n" in markdown_content:
        markdown_content = markdown_content.replace("\n\n\n", "\n\n")

    return markdown_content


def flatten_and_stringify(data):
    """Recursively flattens nested lists and converts all elements to strings."""
    if isinstance(data, list):
        return ''.join([flatten_and_stringify(item) for item in data])
    else:
        return str(data)


def markdown2pdf_buffer(document_content, unique_filename,
                        extra_args=['--toc', '--toc-depth=2', '--pdf-engine=xelatex']):
    #st.write(extra_args)
    try:
        # Convert to PDF using a temporary file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            pypandoc.convert_text(
                document_content,
                'pdf',
                format='markdown',
                outputfile=temp_file.name,
                extra_args=extra_args
            )

            # Read the content from the temporary file into the buffer
            pdf_buffer = BytesIO(temp_file.read())

        logging.info(f"pdf_output_file saved to {unique_filename + '.pdf'}")
        return pdf_buffer  # Return the buffer

    except FileNotFoundError:
        logging.error("Pypandoc not found. Please install the pypandoc library to generate PDF.")
        st.warning("Pypandoc not found. Please install the pypandoc library to generate PDF.")
        return
