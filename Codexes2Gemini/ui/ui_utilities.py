import datetime
import json
import logging
import os
import subprocess
from importlib import resources
from io import BytesIO
import tempfile
import pandas as pd
import pypandoc
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


# FIX force line wrap if author > 30 charaters
def create_latex_preamble(gemini_title="TBD", gemini_subtitle="TBD", gemini_authors="TBD", paperwidth=4, paperheight=6,
                          top=0.25, bottom=0.25, right=0.25, left=0.5, includehead=True, includefoot=True,
                          documentclass="book", output="pdf_document", fontsize=10, mainfont=None):

    if isinstance(gemini_authors, list):
        gemini_authors_str = ", ".join([f"{author}" for author in gemini_authors])
    else:
        gemini_authors_str = gemini_authors
    if gemini_subtitle is None:
        gemini_subtitle = " "

        # FIX unescaped single quotes in LATEX YAML, example:
    """

    ---
title: "THE
ADVOCATE"
author: '\parbox[t]{\textwidth}{CHARLES HEAVYSEGE,
Author of 'Saul', 'Jephthah's Daughter.'
&c., &c., &c.}'
subtitle: "A NOVEL"
    """
    if "\"" or ":" in gemini_authors_str and len(gemini_authors_str > 0):
        gemini_authors_str = gemini_authors_str.replace("\"", "'").replace(":", "")
    # Wrap author field if longer than 30 characters
    gemini_authors_no_latex_str = gemini_authors_str.replace("\\", "")
    if len(gemini_authors_str) > 30:
        gemini_authors_str = f"\\parbox[t]{{\\textwidth}}{{{gemini_authors_str}}}"
    st.session_state.current_plan.update({"gemini_authors_no_latex_str": gemini_authors_no_latex_str})
    st.session_state.current_plan.update({"gemini_authors_str": gemini_authors_str})
    yaml_preamble = f"""---
title: "{gemini_title}"
author: '{gemini_authors_str}'
subtitle: "{gemini_subtitle}"
header-includes:
  - \\usepackage[paperwidth={paperwidth}in, paperheight={paperheight}in, top={top}in, bottom={bottom}in, right={right}in, left={left}in, includehead, includefoot]{{geometry}} # 
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


def get_version_as_dict():
    try:
        mtime = os.path.getmtime('.git/FETCH_HEAD')
    except OSError:
        mtime = 0
    last_modified_date = datetime.fromtimestamp(mtime)

    version_line = subprocess.check_output(["git", "describe", "--long"]).decode("utf-8").strip()

    last_commit_message = str(subprocess.check_output(['git', 'log', '-1', '--pretty=%B']).decode('utf-8').strip())

    update_line = last_modified_date.strftime("%Y-%m-%d %H:%M:%S")
    current_branch = 'unknown'
    branches = subprocess.check_output(['git', 'branch']).decode('utf-8').strip().split('\n')
    # loop through list and select the current branch
    for branch in branches:
        if branch.startswith('*'):
            current_branch = branch[2:]

    data = {"version": version_line, "current branch": current_branch, "last updated": update_line,
            'most recent commit message': last_commit_message}
    # data = version_line, update_line, last_commit_message

    datalist = [version_line, current_branch, update_line, last_commit_message]

    df = pd.DataFrame(data, index=[0]).T.rename(columns={0: ''})

    return data
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
