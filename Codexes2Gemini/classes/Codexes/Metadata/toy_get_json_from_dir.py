import json
import logging
import os
import csv
import re
import uuid
import streamlit as st
import pandas as pd
import shutil


class Codexes2LSI_ACS_Metadata():
    def gemini_create_lsi_acs_csv(directory):
        """
        Loops through a directory, extracts data from JSON files, and creates a CSV file that has metadata needed for LSI ACS upload.

        Args:
            directory (str): The path to the directory containing the JSON files.
        """

        csv_header = ['Non-Empty Key/Value Pairs',
                      'Lightning Source Account #', 'Metadata Contact Dictionary', 'Parent ISBN', 'ISBN or SKU',
                      'Rendition',
                      'Title', 'Publisher', 'Imprint', 'Cover/Jacket Submission Method', 'Text Block Submission Method',
                      'Contributor One', 'Contributor One Role', 'Reserved 1', 'Reserved 2', 'Reserved 3', 'Reserved 4',
                      'Custom Trim Width (inches)', 'Custom Trim Height (inches)', 'Weight(Lbs)', 'Reserved5',
                      'Reserved6',
                      'Reserved7', 'Reserved8', 'Marketing Image', 'Pages', 'Pub Date', 'Street Date',
                      'Territorial Rights',
                      'Contributor Two', 'Contributor Two Role', 'Contributor Three', 'Contributor Three Role',
                      'Edition Number',
                      'Edition Description', 'Jacket Path / Filename', 'Interior Path / Filename',
                      'Cover Path / Filename',
                      'Annotation / Summary', 'Reserved (Special Instructions)',
                      'LSI Special Category  (please consult LSI before using', 'Stamped Text LEFT',
                      'Stamped Text CENTER',
                      'Stamped Text RIGHT', 'Order Type Eligibility', 'Returnable', 'BISAC Category', 'Language Code',
                      'LSI FlexField1 (please consult LSI before using)',
                      'LSI FlexField2 (please consult LSI before using)',
                      'LSI FlexField3 (please consult LSI before using)',
                      'LSI FlexField4 (please consult LSI before using)',
                      'LSI FlexField5 (please consult LSI before using)', 'Reserved11', 'Reserved12',
                      'BISAC Category 2',
                      'BISAC Category 3', 'Publisher Reference ID', 'Reserved9', 'Reserved10', 'Carton Pack Quantity',
                      'Contributor One BIO', 'Contributor One Affiliations', 'Contributor One Professional Position',
                      'Contributor One Location', 'Contributor One Location Type Code', 'Contributor One Prior Work',
                      'Keywords',
                      'Thema Subject 1', 'Thema Subject 2', 'Thema Subject 3', 'Regional Subjects', 'Audience',
                      'Min Age',
                      'Max Age', 'Min Grade', 'Max Grade', 'Short Description', 'Table of Contents', 'Review Quote(s)',
                      '# Illustrations', 'Illustration Notes', 'Series Name', '# in Series', 'color_interior',
                      'US Suggested List Price', 'US Wholesale Discount', 'UK Suggested List Price',
                      'UK Wholesale Discount (%)',
                      'EU Suggested List Price (mode 2)', 'EU Wholesale Discount % (Mode 2)',
                      'AU Suggested List Price (mode 2)',
                      'AU Wholesale Discount % (Mode 2)', 'CA Suggested List Price (mode 2)',
                      'CA Wholesale Discount % (Mode 2)',
                      'GC Suggested List Price (mode 2)', 'GC Wholesale Discount % (Mode 2)',
                      'USBR1 Suggested List Price (mode 2)',
                      'USBR1 Wholesale Discount % (Mode 2)', 'USDE1 Suggested List Price (mode 2)',
                      'USDE1 Wholesale Discount % (Mode 2)', 'USRU1 Suggested List Price (mode 2)',
                      'USRU1 Wholesale Discount % (Mode 2)', 'USPL1 Suggested List Price (mode 2)',
                      'USPL1 Wholesale Discount % (Mode 2)', 'USCN1 Suggested List Price (mode 2)',
                      'USCN1 Wholesale Discount % (Mode 2)', 'USKR1 Suggested List Price (mode 2)',
                      'USKR1 Wholesale Discount % (Mode 2)', 'USIN1 Suggested List Price (mode 2)',
                      'USIN1 Wholesale Discount % (Mode 2)', 'USJP2 Suggested List Price(mode 2)',
                      'USJP2 Wholesale Discount % (Mode 2)', 'UAEUSD Suggested List Price (mode 2)',
                      'UAEUSD Wholesale Discount % (Mode 2)'
                      ]

        csv_data = [csv_header]  # Start with the header row

        add_to_processing_metadata_df = pd.DataFrame(
            columns=["textfilename", "title", "year_of_publication", "URI", "summary"])

        for filename in os.listdir(directory):
            if re.match(r'^\d+\.json$', filename):
                filepath = os.path.join(directory, filename)
                with open(filepath, 'r') as f:
                    try:
                        alldata = json.load(f)
                        print(f"Processing {filepath}")
                        data, gemini_authors_str, gemini_subtitle, gemini_summary, gemini_title, gemini_year_of_publication, textfilename = gemini_extract_basic_info_from_saved_file(
                            alldata, filename)
                    except json.JSONDecodeError:
                        print(f"Error: Invalid JSON in file: {filepath}, skipping ....")
                        st.error(f"Error: Invalid JSON in file: {filepath}, skipping ....")

                # Extract the basename without extension for Publisher Reference ID
                publisher_ref_id = os.path.splitext(filename)[0]
                non_empty_count = len(alldata['results'])
                csv_data = append_row_data_to_lsi_acs(csv_data, data, gemini_authors_str, gemini_subtitle,
                                                      gemini_title,
                                                      non_empty_count, publisher_ref_id)

                processing_metadata_row = [textfilename, gemini_title, gemini_year_of_publication, "",
                                           gemini_summary]
                # append metadata row to add_to_processed_metadata_df
                add_to_processing_metadata_df.loc[len(add_to_processing_metadata_df)] = processing_metadata_row

        # create unique job name with four characters
        job_id = str(uuid.uuid4())[0:4]
        with open('LSI_ACS_metadata_' + job_id + '.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(csv_data)
        print(f"wrote {len(csv_data)} rows to {job_id}LSI_ACS_metadata_{job_id}.csv")
        add_to_processing_metadata_df.to_csv(f'processed_data/add_to_processing_metadata_{job_id}.csv', index=False)
        return

    def append_row_data_to_lsi_acs(csv_data, data, gemini_authors_str, gemini_subtitle, gemini_title, non_empty_count,
                                   publisher_ref_id):
        csv_row = [
            non_empty_count, '6024045', '', '', '',
            'POD: B&W 4 x 6 in or 152 x 102 mm Perfect Bound on White w/Matte Lam',
            gemini_title + " " + gemini_subtitle, 'W. Frederick Zimmerman', 'Collapsar Classics', 'ftp',
            'ftp', gemini_authors_str, 'A', '', '', '', '', '4', '6', '', '', '', '', '', '', '', '', '',
            '', 'Fred Zimmerman', 'F', '', '', '', '', '', '', '', data.get('gemini_summary', ''), '', '',
            '', '', '', '', 'Yes', '', 'ENG', '', '', '', '', '', '', '', '', '', publisher_ref_id, '', '',
            '',
            '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
            '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
        csv_data.append(csv_row)
        logging.info(f"appended row {publisher_ref_id} to csv_data")
        return csv_data

    def gemini_extract_basic_info_from_saved_file(alldata, filename):
        data = alldata["results"][0]  # Access the first element of the "results" list
        data = json.loads(data)  # Parse the inner JSON string
        print(data)
        textfilename = basename_without_extension = os.path.splitext(os.path.basename(filename))[0]
        gemini_title = data.get("gemini_title", " ")
        gemini_subtitle = data.get("gemini_subtitle", " ")
        if gemini_title is None:
            gemini_title = " "
        if gemini_subtitle is None:
            gemini_subtitle = " "
        gemini_authors = data.get("gemini_authors", "")
        if isinstance(gemini_authors, list):
            gemini_authors_str = ", ".join(gemini_authors)  # Join authors with commas
        else:
            gemini_authors_str = gemini_authors
        gemini_year_of_publication = data.get("gemini_year_of_publication", 2024)
        gemini_summary = data.get("gemini_summary", "")
        return data, gemini_authors_str, gemini_subtitle, gemini_summary, gemini_title, gemini_year_of_publication, textfilename

    def copy_json_files(source_dir, dest_dir, keyword="gemini_title"):
        """Copies JSON files containing a specific keyword to a destination directory.

        Args:
          source_dir: The directory to search for JSON files.
          dest_dir: The directory to copy matching files to.
          keyword: The keyword to search for within the JSON files.
        """

        os.makedirs(dest_dir, exist_ok=True)  # Create dest_dir if it doesn't exist

        for filename in os.listdir(source_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(source_dir, filename)
                with open(filepath, 'r') as f:
                    try:
                        data = json.load(f)
                        if keyword in json.dumps(data):
                            shutil.copy2(filepath, dest_dir)  # Copy with metadata
                            print(f"Copied: {filename} to {dest_dir}")
                    except json.JSONDecodeError:
                        print(f"Skipping invalid JSON file: {filepath}")


def gemini_get_column_values(missing_columns=None):
    """
    Use gemini to get values for each row in specified columns, e.g. BISAC codes
    """
    if missing_columns is None:
        if missing_columns is None:
            raise ValueError("You must specify at least one column to fill in.")



if __name__ == "__main__":
    # copy_json_files('processed_data', 'trancheOct31', "gemini_title")
    gemini_create_lsi_acs_csv('/Users/fred/bin/nimble/Codexes2Gemini/trancheOct31')
