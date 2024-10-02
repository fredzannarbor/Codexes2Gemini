#  Copyright (c) 2023. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com

import argparse
import os
from string import punctuation

import docx


def make_filename_safe(docxfilename):
    thisdoc_basename = os.path.basename(docxfilename)
    # replace all punctuation with underscores
    convert_to_underscores = punctuation
    translate_table = str.maketrans(convert_to_underscores, '_' * len(convert_to_underscores))
    thisdoc_filename = thisdoc_basename.translate(translate_table)[:-4]
    print('thisdoc_filename: ' + thisdoc_filename)
    return thisdoc_filename


def docx2txtfile(filename, output_filename=None):
    doc = docx.Document(filename)
    paragraphs_list = []

    # turn documen into a list of paragraphs
    # naively - no special handling of tables, etc.
    for p in doc.paragraphs:
        paragraphs_list.append(p.text)

    if output_filename is None:
        new_filename = str(make_filename_safe(docxfile))

    else:
        new_filename = output_filename
    with open(output_dir + '/' + new_filename + '.txt', 'w') as f:
        f.write('\n'.join(paragraphs_list))

    return new_filename


def argparse_handler():
    argparser = argparse.ArgumentParser()

    argparser.add_argument('--docxfile', help='path to text file',
                           default='editorial/Syzmanski/Outer_Space_Warfare_Foreign_Perspectives-2022-01-18_1_.docx')
    argparser.add_argument('--paras_limit', help='limit number of paragraphs displayed on return', default=20)
    argparser.add_argument('--output_dir', help='path to output directory', default='output')
    argparser.add_argument('--list2string', help='output converted text as single string, not a list', default=False)
    argparser.add_argument('--output_filename', help='output file name - user should provide extension',
                           default='textfile.txt')

    args = argparser.parse_args()
    docxfile = args.docxfile
    paras_limit = args.paras_limit
    output_dir = args.output_dir
    list2string = args.list2string
    output_filename = args.output_filename

    return docxfile, paras_limit, output_dir, list2string, output_filename


if __name__ == "__main__":
    docxfile, paras_limit, output_dir, list2string, output_filename = argparse_handler()

    new_filename = docx2txtfile(docxfile, output_filename=None)
    print('text file saved to: ' + output_dir + '/' + new_filename + '.txt')
