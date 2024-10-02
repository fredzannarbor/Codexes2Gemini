from __future__ import print_function

import argparse
import csv
import json
import logging

import fitz


def pdfmetadata2dict(filename):
    doc = fitz.open(filename)
    metadata_dict = doc.metadata
    # addfilename = {'filename': filename}
    # metadata_dict = {**metadata_dict, **addfilename}
    # print('records', records)

    return metadata_dict


from PyPDF2 import PdfReader


def pdf2moremetadata(file_path):
    with open(file_path, "rb") as file:
        pdf = PdfReader(file)
        morepdfmetadata = pdf.metadata
        # st.write(metadata)
    return morepdfmetadata


def pdf_decide_if_color_interior_needed(filename):
    doc = fitz.open(filename)
    # inspect each page to determine if color is used
    colorinteriorneeded = False
    for count, page in enumerate(doc):
        if page.uses_color:
            colorinteriorneeded = True
            break
        else:
            colorinteriorneeded = False
    return colorinteriorneeded


def pdfmetadata2text(filename):
    doc = fitz.open(filename)
    metadata_dict = doc.metadata
    metadata_text = json.dumps(metadata_dict)
    # print('records', records)

    return metadata_text


def pdfmetadata2csv(filename, metadata_csv_filename):
    doc = fitz.open(filename)
    metadata_dict = doc.metadata
    metadata_csv_file_path = 'output' + '/' + metadata_csv_filename
    print('metadata file path in pdfall: ', metadata_csv_file_path)
    with open(metadata_csv_filename, 'w') as csvfile:
        fieldnames = metadata_dict.keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(metadata_dict)
    print('leaving pdfall')  # print('records', records)
    return csvfile


def pdfgetlistoftoc(filename, simple=True):
    doc = fitz.open(filename)
    toc = doc.get_toc(simple=simple)
    logging.info(toc)
    return toc


def pdfpagedimensions2list(filename):
    doc = fitz.open(filename)
    pageheight, pagewidth = 0, 0
    pagedimensionslist = []
    for count, page in enumerate(doc):
        pageheight, pagewidth = page.rect.width, page.rect.height
        pagedimensionslist.append([filename, count + 1, pageheight, pagewidth])
        # print(pageheight, pagewidth)

    return pagedimensionslist


def analyze_page_dimensions(pagedimensionslist):
    heightsallequal, widthsallequal, pageresizingneeded = False, False, False
    height, width = pagedimensionslist[0][2], pagedimensionslist[0][3]
    for count, page in enumerate(pagedimensionslist):
        if count == 0:
            height = page[2]
            width = page[3]
        else:
            if page[2] != height:
                heightsallequal = False
                continue
            else:
                heightsallequal = True
            if page[3] != width:
                widthsallequal = False
                continue
            else:
                widthsallequal = True

    pagecount = len(pagedimensionslist)
    print('heights are all equal: ', heightsallequal, 'widths are all equal: ', widthsallequal, 'pagecount: ',
          pagecount)

    if heightsallequal == False or widthsallequal == False:
        pageresizingneeded = True
    else:
        pageresizingneeded = False
    return heightsallequal, widthsallequal, pageresizingneeded, pagecount


def get_modal_page_dimensions(pagedimensionslist):
    height, width = pagedimensionslist[0][2], pagedimensionslist[0][3]
    print(
        'height: ', height, 'width: ', width
    )

    return height, width


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enter CSV delimiter [;] and document filename")
    parser.add_argument('--delimiter', help='CSV delimiter [;]', default=';')
    parser.add_argument('--output_dir', help='output directory', default='working/output_dir')
    parser.add_argument('--filename', help='document filename', default='test/pdf/Lorem_all_arabic.pdf')
    parser.add_argument('--cumulative_filename', help='cumulative filename', default='cumulative_metadata.csv')
    parser.add_argument('--thisdoc_dir', help='thisdoc_dir', default='output/thisdoc_dir')
    args = parser.parse_args()
    output_dir = args.output_dir
    delimiter = args.delimiter  # requested CSV delimiter character
    filename = args.filename
    cumulative_file_name = args.cumulative_filename
    thisdoc_dir = args.thisdoc_dir
    metadata_csv_filename = (thisdoc_dir + '/' + 'metadata.csv')

    print(pdfmetadata2dict(filename))
    print(pdfmetadata2csv(filename, metadata_csv_filename))
    print(pdfgetlistoftoc(filename))
    print(pdfpagedimensions2list(filename))
