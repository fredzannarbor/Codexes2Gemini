#  Copyright (c) 2024. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com
import glob
import os

import fitz  # Import PyMuPDF


def convert_pdf_to_postscript(pdf_path, ps_path):
    doc = fitz.open(pdf_path)
    doc.save(ps_path, garbage=4, deflate=True, incremental=False)
    doc.close()  # Close the document to free resources


def pdf2postscript(pdf_directory, ps_directory):
    # Make sure the output directory exists
    os.makedirs(ps_directory, exist_ok=True)
    # Loop over all PDF files in the directory
    for pdf_file in glob.glob(os.path.join(pdf_directory, "*.pdf")):
        # Construct the path for the output PostScript file
        ps_file = os.path.join(ps_directory, os.path.basename(pdf_file).replace('.pdf', '.ps'))
        # Convert the PDF to PostScript
        convert_pdf_to_postscript(pdf_file, ps_file)


if __name__ == '__main__':
    # Directory containing PDF files
    pdf_directory = "output/test/ntrl2ps"
    # Directory to save PostScript files
    ps_directory = "output/test/ntrlps"
    pdf2postscript(pdf_directory, ps_directory)
