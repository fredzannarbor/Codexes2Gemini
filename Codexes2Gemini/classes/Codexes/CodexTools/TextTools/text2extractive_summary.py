# given arbitrary text or textfile, does unsupervised keyword extraction
import argparse

import nltk

from app.utilities.gensim_summarizer import gensim_summarizer


def create_extractive_summary_as_list(text, wordcount, output_dir, list2string):
    summary = gensim_summarizer(text, wordcount)

    summary_sentence_list = []
    sentences = nltk.sent_tokenize(summary)
    for sentence in sentences:
        summary_sentence_list.append(sentence)
    with open(output_dir + '/' + 'extractive_summary.txt', 'w') as f:
        f.write(str(summary_sentence_list))
        f.close()
    if list2string == True:
        return "".join(summary_sentence_list)
    else:
        return summary_sentence_list


def argparse_handler():
    argparser = argparse.ArgumentParser()

    argparser.add_argument('--textfile', help='path to text file', default=None)
    argparser.add_argument('--wordcount', help='wordcount', default=1000)
    argparser.add_argument('--output_dir', help='path to output directory', default='output_dir')
    argparser.add_argument('--list2string', help='output converted text as single string, not a list', default=False)

    args = argparser.parse_args()
    textfile = args.textfile
    wordcount = args.wordcount
    output_dir = args.output_dir
    list2string = args.list2string

    return textfile, wordcount, output_dir, list2string


if __name__ == "__main__":

    textfile, wordcount, output_dir, list2string = argparse_handler()

    if textfile == None:
        extractive_summary_list = create_extractive_summary_as_list(textfile, wordcount, output_dir, list2string)
