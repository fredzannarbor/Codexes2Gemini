# given arbitrary text, does unsupervised keyword extraction
import argparse
import logging

import yake
from fuzzywuzzy import process


def create_keyword_list_yake(text, output_dir="app/data/keyword_lists", language="en", max_ngram_size=3,
                             deduplication_thresold=80, deduplication_algo='seqm', windowSize=1, numOfKeywords=10,
                             calculate_number_of_target_keywords=False, inverse_index_verbosity=1000):
    keyword_list, kw_only_list = [], []
    logging.info(f'automatically calculating goal number of index keywords: {calculate_number_of_target_keywords}')
    if calculate_number_of_target_keywords == True:
        word_count = 100000  # reasonable default

        inverse_index_verbosity = 333  # range from 10 to 1000, with 10 being the most verbose, 1000 being the least

        word_list = text.split()
        word_count = len(word_list)
        target_number_of_index_entries = round((word_count / inverse_index_verbosity), 0)

        logging.info(f'target number of index entries {target_number_of_index_entries}')
        numOfKeywords = target_number_of_index_entries
    else:
        logging.info(f'using number of keywords passed into function by user {numOfKeywords}')
    try:
        custom_kw_extractor = yake.KeywordExtractor(lan=language, n=max_ngram_size, dedupLim=0.9,
                                                    dedupFunc=deduplication_algo, windowsSize=windowSize,
                                                    top=numOfKeywords, features=None)
        keywords = custom_kw_extractor.extract_keywords(text)
        logging.info('custom kw extractor was successful')
    except Exception as e:
        logging.error(f'error in custom keyword extraction: {e}')

    logging.info('about to loop through keywords')
    for count, kw in enumerate(keywords):
        if count % 20 == 0:
            logging.info(f'{count} keywords generated')
        keyword_list.append(kw)
    logging.debug(f'keyword list {keyword_list}')
    for item in keyword_list:
        kw = item[0]
        kw_only_list.append(kw)
        logging.debug(f'keywords: {kw}')

    logging.warning(str(len(kw_only_list)) + 'keywords created in first pass')

    deduped = process.dedupe(kw_only_list, threshold=80)
    logging.warning(str(len(deduped)) + ' keywords after deduping')
    # print(deduped)
    deduped_with_scores = {}
    for d in deduped:
        for key, value in keywords:
            if d == key:
                deduped_with_scores.update({key: value})

    return keyword_list, kw_only_list, deduped, deduped_with_scores


def eliminate_exact_duplicates(keyword_list):
    keyword_list_set = set(keyword_list)
    keyword_list_set = list(keyword_list_set)
    return keyword_list_set


def drop_fuzzy_phrase_matches(keyword_list, threshold=0.9):
    df1 = pd.read_excel('Top 10 richest.xlsx', sheet_name="Sheet1")
    df2 = pd.read_excel('Top 10 richest.xlsx', sheet_name="Sheet2")

    df1['name_from_df2'] = df1['Name'].apply(lambda x: process.extractOne(x, df2['Name'].to_list(), score_cutoff=80))
    name_from_df2_list = df1['name_from_df2'].to_list()
    name_from_df2_list = [_[0] if _ != None else None for _ in name_from_df2_list]
    df1['name_from_df2'] = name_from_df2_list

    df1 = df1.merge(df2, left_on='name_from_df2', right_on='Name', suffixes=('', '_2'))
    df1.drop(['Name_2', 'name_from_df2'], axis=1, inplace=True)

    return df1


if __name__ == "__main__":

    argparser = argparse.ArgumentParser(description='Extract keywords from text')
    argparser.add_argument('--text', help='text to extract keywords from',
                           default="All good things come to those who wait.")

    argparser.add_argument('--textfile', help='text file to extract keywords from', default='test/text/pillars.txt')
    argparser.add_argument('--output_dir', help='output directory to save keyword list to',
                           default="app/data/keyword_lists")
    argparser.add_argument('--language', help='language to use for keyword extraction', default="en")
    argparser.add_argument('--max_ngram_size', help='max ngram size to use for keyword extraction', default=3)
    argparser.add_argument('--deduplication_thresold', help='deduplication threshold to use for keyword extraction',
                           default=80)
    argparser.add_argument('--deduplication_algo', help='deduplication algorithm to use for keyword extraction',
                           default='seqm')
    argparser.add_argument('--windowSize', help='window size to use for keyword extraction', default=1)
    argparser.add_argument('--numOfKeywords', help='number of keywords to use for keyword extraction', default=10)
    argparser.add_argument('--calculate_number_of_target_keywords',
                           help='calculate target number of keywords to use for keyword extraction', default="False")
    argparser.add_argument('--inverse_index_verbosity',
                           help='index verbosity denominator, max verbosity = 10, min = 1000', default=333)

    args = argparser.parse_args()
    text = args.text
    textfile = args.textfile
    output_dir = args.output_dir
    language = args.language
    max_ngram_size = args.max_ngram_size
    deduplication_thresold = args.deduplication_thresold
    deduplication_algo = args.deduplication_algo
    windowSize = args.windowSize
    numOfKeywords = args.numOfKeywords
    calculate_number_of_target_keywords = args.calculate_number_of_target_keywords
    inverse_index_verbosity = args.inverse_index_verbosity

    if textfile is not None:
        with open(textfile, 'r') as f:
            text = f.read()

    create_keyword_list_yake(text, output_dir, language="en", max_ngram_size=3,
                             deduplication_thresold=deduplication_thresold, deduplication_algo='seqm', windowSize=1,
                             numOfKeywords=10, calculate_number_of_target_keywords=calculate_number_of_target_keywords,
                             inverse_index_verbosity=1000)
