import argparse
import json
import os

import pandas as pd
from doc2json.pdf2json.process_pdf import process_pdf_file


def process_pdf(pdf_file, tempdir, outdir):
    """
    Process a single PDF file.  
    """
    # Process the PDF file
    print("Processing {}".format(pdf_file))
    jsonl_file = process_pdf_file(pdf_file, tempdir, outdir)
    # Load the JSON file
    json_data = json.load(open(jsonl_file))
    # Load the JSON data into a Pandas DataFrame
    df = pd.DataFrame(json_data)
    # Return the DataFrame
    return jsonl_file, df


def create_kdp_metadata_dict(pdf):
    kdp_metadata_dict = {
        - Language *
        - Book
    Title
    - Book
    Subtitle
    - Series *
    - Series
    Number *
    - Edition
    Number *
    - Publisher *
    - Primary
    Author or Contributor *
    - Prefix, First
    Name, Middle
    Name, Last
    Name *
    - Description
    - Publishing
    Rights *
    - Keywords
    - Categories
    }

    if __name__ == "__main__":
        parser = argparse.ArgumentParser()
        parser.add_argument("--infile", help="seed file", default='utilities/s2orc/tests/pdf/2020.acl-main.207.pdf')
        parser.add_argument("--outdir", help="output directory", default='utilities/s2orc/tests/jsonl/')
        parser.add_argument("--tempdir", help="temp directory", default='utilities/s2orc/tests/temp/')

        args = parser.parse_args()
        filename = args.infile
        outdir = args.outdir
        tempdir = args.tempdir

        if not os.path.exists(outdir):
            os.makedirs(outdir)

        if not os.path.exists(tempdir):
            os.makedirs(tempdir)

        jsonl_file, df = process_pdf(filename, tempdir, outdir)
