# -*- coding: utf-8 -*-
# script to extract a range of pages from a pdf file

import os

from PyPDF2 import PdfFileWriter, PdfFileReader

# Note: index starts at 1 and is inclusive of the end.
# The following will extract page 3 of the pdf file.
pdfs = {'BMC PP template.pdf': ({'start': 3, 'end': 3},)}


def get_pages(filename, startpage, endpage, savepath):
    startpage = int(startpage)
    endpage = int(endpage)
    pdf_reader = PdfFileReader(open(filename, 'rb'))
    pdf_writer = PdfFileWriter()
    print(f'Extracting pages {startpage} to {endpage} from {filename}')
    basefile = os.path.basename(filename)
    print('basefile: ', basefile)
    if basefile.startswith('978'):
        print('basefile starts with 978')
        output_filename = f'{basefile[0:12]}_sample_pages_{startpage}_to_{endpage}.pdf'
        print(f'Output filename: {output_filename[0:12]}_sample_pages_{startpage}_to_{endpage}.pdf')
    else:
        max = len(basefile)
        print(max)
        output_filename = f'{basefile[0:max]}_sample_pages_{startpage}_to_{endpage}.pdf'

    while startpage <= endpage:
        pdf_writer.addPage(pdf_reader.getPage(startpage - 1))
        startpage += 1
    if not os.path.exists(savepath):
        os.makedirs(savepath)

    target_file = os.path.join(savepath, output_filename)

    print(f'Saving to {target_file}')
    with open(target_file, 'wb') as out:
        pdf_writer.write(out)

    return target_file


import fitz  # PyMuPDF


def extract_pages_from_pdf(input_file, output_file, start_page, end_page):
    """
    Extract pages from a PDF using the PyMuPDF module.

    :param input_file: Path to the input PDF file.
    :param output_file: Path to the output PDF file.
    :param start_page: Start page (0-based index).
    :param end_page: End page (0-based index).
    :return: None
    """
    # Ensure start and end pages are in correct order
    if start_page > end_page:
        raise ValueError("Start page should be less than or equal to end page.")

    # Open the source PDF file
    src_pdf = fitz.open(input_file)

    # Validate page range
    if start_page < 0 or end_page >= len(src_pdf):
        raise ValueError("Invalid page range specified.")

    # Create a new PDF to store the extracted pages
    output_pdf = fitz.open()

    # Loop through specified range and add pages to the new PDF
    for page_num in range(start_page, end_page + 1):
        page = src_pdf[page_num]
        output_pdf.insert_pdf(src_pdf, from_page=page_num, to_page=page_num)

    # Save the new PDF
    output_pdf.save(output_file)

    # Close the PDFs
    src_pdf.close()
    output_pdf.close()

    return output_pdf


if __name__ == "__main__":
    filename, startpage, endpage, savepath = '/Users/fred/unity/assets/interior_pdf/9781608882465_Sybil_v13_allisbns.pdf', 13, 30, '/Users/fred/unity/scratch'
    try:
        get_pages(filename, startpage, endpage, savepath)
    except Exception as e:
        print(e)
