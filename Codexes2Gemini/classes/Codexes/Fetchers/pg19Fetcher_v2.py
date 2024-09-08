import csv
import json
import os
import random
import pandas as pd
from datetime import datetime
import streamlit as st

from Codexes2Gemini.classes.Codexes.Builders import Codexes2Parts
from Codexes2Gemini.classes.Codexes.Builders.PromptsPlan import PromptsPlan


# TODO - make forms honor selected row(s) thorughout session

class PG19FetchAndTrack:
    def __init__(self, metadata_file, data_dirs,
                 processed_csv='processed_metadata.csv',
                 output_dir='processed_data',
                 number_of_context_files_to_process=3):  # Default N to 3
        self.metadata_file = metadata_file
        self.data_dirs = data_dirs
        self.processed_csv = processed_csv
        self.output_dir = output_dir
        self.number_of_context_files_to_process = number_of_context_files_to_process
        self.load_processed_metadata()
        self.CODEXES2PARTS = Codexes2Parts()  # Initialize Codexes2Parts here

    def load_processed_metadata(self):
        if os.path.exists(self.processed_csv):
            self.processed_df = pd.read_csv(self.processed_csv)
        else:
            self.processed_df = pd.DataFrame(columns=['textfilename', 'processed', 'processing_date', 'output_json'])

    @st.cache_data  # Cache this for efficiency
    def create_file_index(_self):
        """Creates a file index for efficient lookup of text files."""
        file_index = {}
        with open(_self.metadata_file, "r") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                textfilename = row[0]
                for data_dir in _self.data_dirs:
                    filepath = os.path.join(data_dir, f"{textfilename}.txt")
                    if os.path.exists(filepath):
                        file_index[textfilename] = filepath
                        break
        return file_index

    def fetch_pg19_data(self):
        """Fetches and processes PG19 data, tracking progress."""
        file_index = self.create_file_index()
        if not st.session_state.current_plan["selected_rows"]:
            selected_rows = self.fetch_pg19_metadata(self.number_of_context_files_to_process)

        for row in selected_rows:
            textfilename = row[0]

            # Check if already processed
            if self.processed_df[self.processed_df['textfilename'] == textfilename]['processed'].any():
                print(f"Skipping already processed file: {textfilename}")
                continue

            filepath = file_index.get(textfilename)
            if filepath is None:
                print(f"Warning: Could not find file for {textfilename}")
                continue

            with open(filepath, "r") as f:
                context = f.read()

            # Process the context (replace with your actual processing logic)
            results = self.process_single_context(context, row)

            # Save results to JSON
            self.save_results_to_json(textfilename, results)

            # Update processed metadata
            self.update_processed_metadata(textfilename)

        self.save_processed_metadata()

    def fetch_pg19_metadata(self, number_of_context_files_to_process):
        """Fetches metadata for N random PG19 entries."""
        with open(self.metadata_file, "r") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header row
            rows = list(reader)
            return random.sample(rows, number_of_context_files_to_process)  # first random

    def process_single_context(self, context, row):
        """Processes a single context and returns the results."""
        # ... (Your logic to process the context using Codexes2Parts goes here) ...
        # For example:
        st.session_state.current_plan.update({"context": context, "row": row})
        plan = PromptsPlan(**st.session_state.current_plan)
        satisfactory_results = self.CODEXES2PARTS.process_codex_to_book_part(plan)
        return satisfactory_results

    def save_results_to_json(self, textfilename, results):
        """Saves results to a JSON file."""
        output_json_filename = f"{textfilename}.json"
        output_json_path = os.path.join(self.output_dir, output_json_filename)
        os.makedirs(self.output_dir, exist_ok=True)

        with open(output_json_path, 'w') as f:
            json.dump({
                'textfilename': textfilename,
                'processing_date': datetime.now().isoformat(),
                'results': results
            }, f, indent=4)

    def update_processed_metadata(self, textfilename):
        """Updates the processed metadata DataFrame."""
        new_row = pd.DataFrame({
            'textfilename': [textfilename],
            'processed': [True],
            'processing_date': [datetime.now()],
            'output_json': [f"{textfilename}.json"]
        })
        self.processed_df = pd.concat([self.processed_df, new_row], ignore_index=True)

    def save_processed_metadata(self):
        """Saves the processed metadata to a CSV file."""
        self.processed_df.to_csv(self.processed_csv, index=False)
