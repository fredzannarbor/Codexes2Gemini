# given arbitrary text or textfile, does unsupervised keyword extraction

import argparse

# from summarizer import Summarizer
import app.utilities.PKsum2.summarize as summarize


def create_extractive_summary_as_list(text, sentences, output_dir, list2string):
    summary_sentence_list = []

    min_length = sentences
    simplesummarizer = summarize.SimpleSummarizer()
    summary_sentence_list = simplesummarizer.summarize(text, min_length)
    print(summary_sentence_list)
    with open(output_dir + '/' + 'extractive_summary.txt', 'w') as f:
        f.write(str(summary_sentence_list))
        f.close()
    if list2string == True:
        return "".join(summary_sentence_list)
    else:
        return summary_sentence_list


def argparse_handler():
    argparser = argparse.ArgumentParser()

    argparser.add_argument('--textfile', help='path to text file', default='test/text/granddaughter.txt')
    argparser.add_argument('--sentences', help='number of sentences', default=5)
    argparser.add_argument('--output_dir', help='path to output directory', default='output')
    argparser.add_argument('--list2string', help='output converted text as single string, not a list', default=False)

    args = argparser.parse_args()
    text = args.text
    sentences = args.sentences
    output_dir = args.output_dir
    list2string = args.list2string

    return text, sentences, output_dir, list2string


if __name__ == "__main__":
    text, sentences, output_dir, list2string = argparse_handler()
    print(text, sentences, output_dir, list2string)
    results = create_extractive_summary_as_list(text, sentences, output_dir, list2string)
    print(len(results))
    print(results)
