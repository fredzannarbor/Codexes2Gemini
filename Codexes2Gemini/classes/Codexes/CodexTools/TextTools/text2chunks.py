# -*- coding: utf-8 -*-


from os import path

from nltk.tokenize import sent_tokenize

from app.utilities.utilities import create_safe_dir_from_file_path


def textfile2text(textfile):
    with open(textfile, 'r') as f:
        text = f.read()
    return text


def roundup(x):
    return x if x % 100 == 0 else x + 100 - x % 1


def chunkize(text, output_dir, chunksize=400):
    chunk_no = 0
    data = []
    prompt = []
    chunk_list = []
    chunk = ''
    d = {}
    total_words, words_in_chunk = 0, 0
    textlist = list(text.split('/n'))
    for t in textlist:
        tokenized_t = sent_tokenize(t)

        paragraph_so_far = ""
        for sentence in tokenized_t:
            words_in_sentence = len(sentence.split())
            words_in_chunk = words_in_chunk + words_in_sentence
            if words_in_chunk >= chunksize:
                chunk = chunk + paragraph_so_far
                chunk_list.append(chunk)
                chunk = ''
                chunk_no = chunk_no + 1
                print(chunk_no)
                total_words += words_in_chunk
                words_in_chunk = 0
            paragraph_so_far = paragraph_so_far + sentence
        chunk = chunk + '\n' + paragraph_so_far

    chunk_list.append(chunk)

    print('chunked text with ', total_words, 'total words into', len(chunk_list), 'chunks', '\n')
    safenames = create_safe_dir_from_file_path(textfile, output_dir)
    thisdoc_dirname = safenames[0]
    thisdoc_basename = safenames[1]
    thisdoc_chunk_path = path.join(thisdoc_dirname + '/' + thisdoc_basename + '._chunks.txt')
    with open(thisdoc_chunk_path, 'w') as f:
        for item in chunk_list:
            f.write("%s\n" % item)

    return thisdoc_chunk_path, chunk_list


if __name__ == "__main__":
    textfile = 'test/text/pillars.txt'
    text = textfile2text(textfile)
    chunklist = chunkize(text, 'output', chunksize=400)
