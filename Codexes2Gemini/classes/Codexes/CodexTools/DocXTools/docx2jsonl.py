#  Copyright (c) 2023. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com

import argparse
import os

import docx
import pandas as pd

from app.utilities.utilities import create_safe_dir_from_file_path

temp_dir = 'data/temp/'
output_dir = 'output/'


def docx2jsonl(filename, output_dir):
    doc = docx.Document(filename)
    data = []

    safenames = create_safe_dir_from_file_path(filename, output_dir)
    thisdoc_dirname = safenames[0]
    thisdoc_basename = safenames[1]
    for p in doc.paragraphs:
        data.append(p.text)
    df = pd.DataFrame(data, columns=["text"])

    thisdoc_jsonl_path = os.path.join(thisdoc_dirname + '/' + thisdoc_basename + '.jsonl')

    df.to_json(thisdoc_jsonl_path, orient="records", lines=True)

    print('wrote', thisdoc_jsonl_path)

    return thisdoc_jsonl_path, df


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--output_dir', default='output', help='base directory to save output files')
    argparser.add_argument('--filename', default='test/docx/lorem.docx', help='docx file to be processed')
    args = argparser.parse_args()
    output_dir = args.output_dir
    filename = args.filename
    docx2jsonl(filename, output_dir)
