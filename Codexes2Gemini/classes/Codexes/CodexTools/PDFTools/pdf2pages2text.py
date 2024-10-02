#  Copyright (c) 2023. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com

import argparse
import logging
import os
import re

import fitz
import nltk
from nltk.corpus import stopwords

from app.utilities.utilities import smart_print, set_logging_level

# from app.utilities.utilities import am_I_running_under_streamlit
# from classes.ADEPT.SinglePDFProcessor import smart_print
set_logging_level("INFO")


def ProperNounExtractor(text):
    listofwords = []
    # logging.info('PROPER NOUNS EXTRACTED :')

    sentences = nltk.sent_tokenize(text)
    for sentence in sentences:
        words = nltk.word_tokenize(sentence)
        words = [word for word in words if word not in set(stopwords.words('english'))]
        tagged = nltk.pos_tag(words)
        for (word, tag) in tagged:
            if tag == 'NNP':  # If the word is a proper noun
                # logging.info(word)
                listofwords.append(word)
    return listofwords


def tokenize_text_removing_new_lines_inside_sentences(text):
    tokens = nltk.sent_tokenize(text)
    # logging.info(text)
    new_tokens = []
    for t in tokens:
        # logging.info (t, "\n")
        t = re.sub('([a-z])\n([a-z])', '\\1 \\2', t)
        t = re.sub('(Japanese[ ]{2,}[A-Z])', '\\n\\1', t)
        new_tokens.append((t))
    # logging.info('-----------------')
    # logging.info(new_tokens)
    final_text = ' '.join(new_tokens)
    return final_text


def pdf_pages_to_text_to_files(pdf_file_path, output_dir, limit, list2string=False):
    pdf_text_dict = {}
    pdf_text_list = ['']
    count = 0
    with fitz.open(pdf_file_path) as doc:
        try:
            text = ""

            for count, page in enumerate(doc, 1):
                smart_print(f"Converting page {count} of {len(doc)} in PDF to text", both=True)
                text = page.get_text()

                tokenized_text = tokenize_text_removing_new_lines_inside_sentences(text)

                text_file_path = output_dir + '/' + os.path.basename(pdf_file_path) + '_' + str(count) + '.txt'
                smart_print(text_file_path)
                with open(text_file_path, 'w') as f:
                    f.write(text)
                    f.close()
                add2dict = {count: text}
                pdf_text_dict.update(add2dict)
                pdf_text_list.append(text)
                if count == limit:
                    break
        except Exception as e:
            smart_print(e)
            return None
    # logging.info(pdf_text_list)
    if list2string == True:
        return "".join(pdf_text_list)
    else:
        logging.info('by default, returning text as list of strings')
    return pdf_text_list


def pdf_pages_to_list_of_text_strings(pdf_file_path, limit=10, thisdoc_dir="output"):
    # get name of module : name of function
    # whereIam = where_am_I_running_to_string()
    # logging.info(whereIam)
    pdf_text_list = []
    count = 0
    # check if pdf is searchable
    extracted_text = ''.join([page.get_text("text") for page in fitz.open(pdf_file_path).pages()])
    doc_type = "text" if extracted_text else "scan"
    logging.info("Document type: %s" % doc_type)
    doc = fitz.Document(pdf_file_path)
    pagecountmsg = 'pages: ' + str(doc.page_count)

    text = ""
    if doc_type != "text":
        logging.warning(f'document {pdf_file_path} is scanned only, needs OCR, this will take longer')
    for count, page in enumerate(doc, 1):
        if count > int(limit):
            break
        if doc_type == "text":
            if count % 20 == 0:
                message = f"converting page {count} to text"
                logging.info(message)
                convertedtext = page.get_text()
            else:
                # logging.info('OCRing page', count)
                convertedtext = page.get_text()
            pdf_text_list.append(convertedtext)
        else:

            if count % 20 == 0:
                counterrormsg = 'OCRing page ' + str(count) + ' to text'
                logging.info(counterrormsg)
                convertedtext = page.get_textpage_ocr().extractText()
                # logging.info(convertedtext)
            else:
                # logging.info('OCRing page', count)
                convertedtext = page.get_textpage_ocr().extractText()
            pdf_text_list.append(convertedtext)
    with open(thisdoc_dir + '/' + 'pages2textstrings.txt', 'w') as f:
        text = "".join(pdf_text_list)
        f.write(text)
        f.close()
    logging.info('... leaving pdf2pages2text<')
    return pdf_text_list


if __name__ == "__main__":

    argparser = argparse.ArgumentParser()
    argparser.add_argument('--pdf_file_path', help='path to pdf file',
                           default="/Users/fred/bin/nimble/unity/app/data/9781608881819_txt_v1.pdf")
    # argparser.add_argument('--pdf_file_path', help='path to pdf file', default="/Users/fred/bin/nimble/unity/SC-2021-00002_C05097836.pdf")
    argparser.add_argument('--output_dir', help='path to output directory', default='output')
    argparser.add_argument('--limit', help='limit', default=10)
    argparser.add_argument('--find_proper_nouns', help='find proper nouns', default=False)
    argparser.add_argument('--output_pages_as_files', help='output pages as files', default=False)
    argparser.add_argument('-l', '--log_level', default='ERROR', help='Set logging level',
                           required=False)
    args = argparser.parse_args()
    pdf_file_path = args.pdf_file_path
    output_dir = args.output_dir
    find_proper_nouns = args.find_proper_nouns
    output_pages_as_files = args.output_pages_as_files
    limit = args.limit
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    pdf_text_list = ['']
    pdf_text_list = pdf_pages_to_list_of_text_strings(pdf_file_path, limit)

    if output_pages_as_files:
        pdf_pages_to_text_to_files(pdf_file_path, thisdoc_dir, limit)
        logging.info('outputted pages as text files to output_dir')
    else:
        # no output files
        logging.warning("did not output pages as text files")

    if find_proper_nouns:
        cumulative_proper_nouns = []
        for i in range(len(pdf_text_list)):
            a = ProperNounExtractor((pdf_text_list[i]))
            cumulative_proper_nouns.append(a)

        # get uniques from cumulative_proper_nouns
        uniques = []
        for i in range(len(cumulative_proper_nouns)):
            if i % 100 == 0:
                logging.info('sifting for uniques in first', i, 'cumulative proper nouns')
            for j in range(len(cumulative_proper_nouns[i])):
                if cumulative_proper_nouns[i][j] not in uniques:
                    uniques.append(cumulative_proper_nouns[i][j])

        sorted_uniques = sorted(uniques)
        logging.info(sorted_uniques)
        # write uniques to file one line at a time
        with open(output_dir + '/' + os.path.basename(pdf_file_path) + '_proper_nouns.txt', 'w') as f:
            for item in sorted_uniques:
                f.write("%s\n" % item)
            f.close()
    else:
        logging.info("not looking for proper nouns")
