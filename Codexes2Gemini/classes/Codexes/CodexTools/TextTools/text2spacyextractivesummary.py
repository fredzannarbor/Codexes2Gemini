import argparse
import json
import re
from heapq import nlargest
from string import punctuation

import pandas as pd
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
from sumy.parsers.plaintext import PlaintextParser


def remove_URL(text):
    """Remove URLs from a text string"""
    return re.sub(r"http\S+", "", text)


def sumy_summarize(text):
    parser = PlaintextParser.from_string(document, Tokenizer("english"))
    summarizer = LexRankSummarizer()
    summarizer.stop_words = get_stop_words("english")
    summary = summarizer(parser.document, SENTENCES_COUNT)
    return summary


def spacy_summarize(text, percentage_summarized, output_dir='output', output_filename="extractive_summary.txt",
                    sentences_to_extract=None, max_words_in_summary=1750):
    words_in_text = len(text.split())

    target_percentage = round((max_words_in_summary / words_in_text) * 0.90, 3)
    print("max words in summary / words in text = ", max_words_in_summary, "/", words_in_text)
    print("target percentage = ", target_percentage)
    percentage_summarized = target_percentage

    try:
        # print('loading spacy model...')
        nlp = spacy.load('en_core_web_sm')
        nlp.max_length = int(len(text) * 1.10)
        print('loading doc into nlp...')
        doc = nlp(text)

        wordscounted = 0
        tokens = [token.text for token in doc]
        word_frequencies = {}
        # rint('beginning to loop through words in doc using spacy model ...')
        for word in doc:
            wordscounted += 1
            if word.text.lower() not in list(STOP_WORDS):
                if word.text.lower() not in punctuation:
                    # if "http" not in word.text.lower():
                    if word.text not in word_frequencies.keys():
                        word_frequencies[word.text] = 1
                    else:
                        word_frequencies[word.text] += 1
            if wordscounted % 5000 == 0:
                print('{} words fed into summarizer'.format(wordscounted))

        max_frequency = max(word_frequencies.values())
        for word in word_frequencies.keys():
            word_frequencies[word] = word_frequencies[word] / max_frequency

        sentence_tokens = [sent for sent in doc.sents]
        sentence_scores = {}
        sentences_counted = 0
        sentence_lengths = []
        for sent in sentence_tokens:
            if len(sent) <= 10000:
                sentence_lengths.append(len(sent))
                for word in sent:
                    if word.text.lower() in word_frequencies.keys():
                        if sent not in sentence_scores.keys():
                            sentence_scores[sent] = word_frequencies[word.text.lower()]
                        else:
                            sentence_scores[sent] += word_frequencies[word.text.lower()]
                sentences_counted += 1
                if sentences_counted % 1000 == 0:
                    print('{} sentences fed into summarizer'.format(sentences_counted))
                len(sentence_tokens)

        # save sentence_scores dict as file
        df = pd.DataFrame.from_dict(sentence_scores, orient='index')
        df.to_json(output_dir + '/sentence_scores.json')
        df.to_excel(output_dir + '/sentence_scores.xlsx')
        if sentences_to_extract == None:
            sentences_to_extract = int(len(sentence_tokens) * percentage_summarized)
        else:
            sentences_to_extract = int(sentences_to_extract)
        select_length = sentences_to_extract
        # if select_length < 5:
        #     select_length = 5

        summary = nlargest(select_length, sentence_scores, key=sentence_scores.get)

        final_summary = [word.text for word in summary]

        summary = '\n'.join(final_summary)
        print('summary length = ', len(summary.split()))

        # save final summary as json
        with open(output_dir + '/summary.json'.format('output'), 'w') as f:
            json.dump(final_summary, f)
    except Exception as e:
        print('Error in spacy summarizer: ', e)
        summary = 'Error in spacy summarizer'
    return summary


def argparse_handler():
    argparser = argparse.ArgumentParser()

    argparser.add_argument('--text', help='', default="All good men must come to the aid of the party.")
    argparser.add_argument('--textfile', help='path to text file', default=None)
    argparser.add_argument('--wordcount', help='wordcount', default=1000)
    argparser.add_argument('--percentage', help='percentage of sentences to extract', default=0.01)
    argparser.add_argument('--output_dir', help='path to output directory', default='output_dir')
    argparser.add_argument('--list2string', help='output converted text as single string, not a list', default=False)

    args = argparser.parse_args()
    text = args.text
    textfile = args.textfile
    wordcount = args.wordcount
    output_dir = args.output_dir
    list2string = args.list2string
    percentage = args.percentage

    return text, textfile, wordcount, percentage, output_dir, list2string


if __name__ == "__main__":

    text, textfile, wordcount, percentage, output_dir, list2string = argparse_handler()

    if textfile != None:
        text = open(textfile, 'r').read()

    if text:
        results = spacy_summarize(text, percentage, max_words_in_summary=1750)
        # print(results)
