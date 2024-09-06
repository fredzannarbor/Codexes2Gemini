import csv
import json
import os
import random

import streamlit as st

# import google.generativeai as genai
from Codexes2Gemini.classes.Codexes.Builders import Codexes2Parts
from Codexes2Gemini.classes.Codexes.Builders.PromptsPlan import PromptsPlan

# Configuration
N = 3  # Number of random documents to process
METADATA_FILE = "/Users/fred/bin/Codexes2Gemini/Codexes2Gemini/private/pg19/metadata.csv"
DATA_DIRS = [
    "/Users/fred/bin/Codexes2Gemini/Codexes2Gemini/private/pg19/test/test",
    "/Users/fred/bin/Codexes2Gemini/Codexes2Gemini/private/pg19/train/train",
    "/Users/fred/bin/Codexes2Gemini/Codexes2Gemini/private/pg19/validation/validation",
]

# Initialize Codexes2Parts class
CODEXES2PARTS = Codexes2Parts()


@st.cache_data
def create_file_index(metadata_file, data_dirs):
    """Creates a file index for efficient lookup of text files."""
    file_index = {}
    with open(metadata_file, "r") as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            textfilename = row[0]
            for data_dir in data_dirs:
                filepath = os.path.join(data_dir, f"{textfilename}.txt")
                if os.path.exists(filepath):
                    file_index[textfilename] = filepath
                    break
    # write file index
    with open("output/collapsar/file_index.json", "w") as f:
        json.dump(file_index, f)

    return file_index


def fetch_pg19_metadata(METADATA_FILE, DATA_DIRS, N):
    """Main function to process and enhance PG19 dataset."""

    with open(METADATA_FILE, "r") as f:
        reader = csv.reader(f)
        next(reader)  # Skip header row
        rows = list(reader)
    selected_rows = random.sample(rows, N)

    return selected_rows


def fetch_rows_pg19_data(selected_rows, output_file_path="output/collapsar"):
    # check that file_index exists, is valid json, and has length > 1
    file_index_path = os.path.join(output_file_path, "file_index.json")
    if os.path.isfile(file_index_path):
        # read json file
        file_index = json.load(open(file_index_path, "r"))
        st.info(f"read file_index from {file_index_path}")
    else:
        st.error("file_index does not exist, creating")
        METADATA_FILE = "/Users/fred/bin/Codexes2Gemini/Codexes2Gemini/private/pg19/metadata.csv"
        DATA_DIRS = [
            "/Users/fred/bin/Codexes2Gemini/Codexes2Gemini/private/pg19/test/test",
            "/Users/fred/bin/Codexes2Gemini/Codexes2Gemini/private/pg19/train/train"
        ]

        file_index = create_file_index(METADATA_FILE, DATA_DIRS)

    results = []
    for row in selected_rows:
        textfilename = row[0]
        filepath = file_index[textfilename]
        if filepath is None:
            print(f"Warning: Could not find file for {textfilename}")
            continue
        with open(filepath, "r") as f:
            context = f.read()
            # fetched_contexts.append(context)
            st.session_state.current_plan.update({"context": context, "row": row})
            plan = PromptsPlan(**st.session_state.current_plan)
            satisfactory_results = CODEXES2PARTS.process_codex_to_book_part(plan)
            # st.write(satisfactory_results)
            results.append(satisfactory_results)

    return results


def process_single_context(plan):
    """Processes a single document using Codexes2Parts."""

    safety_settings = CODEXES2PARTS.safety_settings
    generation_config = CODEXES2PARTS.generation_config
    model = CODEXES2PARTS.create_model("gemini-1.5-flash-001", safety_settings, generation_config, cache=None)
    # st.write(plan['context'][:250])
    # st.write(plan['complete_system_instruction'])
    # st.write('---', plan['complete_user_prompt'], '---')
    # loop through prompts

    response = CODEXES2PARTS.gemini_get_response(plan, plan['complete_system_instruction'],
                                                 plan['complete_user_prompt'], plan['context'], model)
    # st.write(response.text)
    return response.text


if __name__ == "__main__":
    selected_rows = fetch_pg19_metadata(METADATA_FILE, DATA_DIRS, N)
    fetch_row_pg19_data(METADATA_FILE, DATA_DIRS, N)
