#  Copyright (c) 2023. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com

import argparse
import os

import docx

from app.utilities.utilities import create_safe_dir_from_file_path


def docx2txt(filename, output_dir):
    paragraphs_list = []

    doc = docx.Document(filename)

    # print('before utility function')
    paths = create_safe_dir_from_file_path(filename, output_dir)
    thisdoc_dirname = paths[0]
    thisdoc_basename = paths[1]
    # print(thisdoc_dirname, 'in docx2txt')

    thisdoc_text_path = os.path.join(thisdoc_dirname + '/' + thisdoc_basename + '.txt')

    for p in doc.paragraphs:
        paragraphs_list.append(p.text)
    print('returning', len(paragraphs_list), 'paragraphs to ', thisdoc_text_path)
    return paragraphs_list, thisdoc_text_path


def argparse_handler():
    argparser = argparse.ArgumentParser()

    argparser.add_argument('--docxfile', help='path to text file',
                           default='editorial/Syzmanski/Outer_Space_Warfare_Foreign_Perspectives-2022-01-18_1_.docx')
    argparser.add_argument('--paras_limit', help='limit number of paragraphs displayed on return', default=20)
    argparser.add_argument('--output_dir', help='path to output directory', default='output_dir')
    argparser.add_argument('--list2string', help='output converted text as single string, not a list', default=False)

    args = argparser.parse_args()
    docxfile = args.docxfile
    paras_limit = args.paras_limit
    output_dir = args.output_dir
    list2string = args.list2string

    return docxfile, paras_limit, output_dir, list2string


if __name__ == "__main__":
    docxfile, paras_limit, output_dir, list2string = argparse_handler()
    text = docx2txt(docxfile, output_dir)
    # print(text[:paras_limit])
