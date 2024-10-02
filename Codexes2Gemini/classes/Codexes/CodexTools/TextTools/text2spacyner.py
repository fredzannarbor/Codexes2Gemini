import argparse
import json

import pandas as pd
import spacy

NER = spacy.load("en_core_web_sm")


def extract_NER_from_text(text):
    doc = NER(text)

    # st.write(doc.ents)
    return doc.ents


def argparse_handler():
    argparser = argparse.ArgumentParser()

    argparser.add_argument('--text', help='', default="All good men must come to the aid of the party.")
    argparser.add_argument('--textfile', help='path to text file', default=None)
    argparser.add_argument('--output_dir', help='path to output directory', default='output')

    args = argparser.parse_args()
    text = args.text
    textfile = args.textfile
    output_dir = args.output_dir

    return text, textfile, output_dir


if __name__ == "__main__":

    text, textfile, output_dir = argparse_handler()
    if textfile != None:
        text = open(textfile, 'r').read()
        entities = extract_NER_from_text(text)
    elif text:
        entities = extract_NER_from_text(text)
    else:
        print('No text provided')
        exit()

    if entities:

        entities_list = []
        for entity in entities:
            entities_list.append({'text': entity.text, 'label': entity.label_})
        with open(output_dir + '/entities.json', 'w') as f:
            json.dump(entities_list, f)
        df = pd.DataFrame.from_dict(entities_list, orient='index')
        df.to_json(output_dir + '/entities.json')
        df.to_excel(output_dir + '/entities.xlsx')
