import argparse

from sumy.nlp.tokenizers import Tokenizer
from sumy.parsers.plaintext import PlaintextParser
from sumy.summarizers.lex_rank import LexRankSummarizer
from sumy.utils import get_stop_words


def sumy_summarize(text, sentences_count=10):
    # text in, text out

    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LexRankSummarizer()
    summarizer.stop_words = get_stop_words("english")
    summary = summarizer(parser.document, sentences_count)
    # SUMMARY AS TEXT
    summary_text = '\n\n'.join([str(sentence) for sentence in summary])

    return summary_text


def chunking_sumy_summarize(text, sentences_count, max_chunk_size=20000,
                            min_chunk_size=100, min_chunks=None, max_chunks=None):
    # split text into chunks
    chunks = []
    words = text.split()
    for i in range(0, len(words), max_chunk_size):
        chunks.append(' '.join(words[i:i + max_chunk_size]))
    print(f"Breaking document of {len(words)} words into {len(chunks)} chunks")
    # feed each chunk to summarizer
    summaries = []
    count = 1
    for chunk in chunks:
        print(f"summarizing chunk #{count} of {len(chunk.split())} words")
        summaries.append(sumy_summarize(chunk, sentences_count))
        count += 1

    # join chunks back together
    summary = '\n'.join(summaries)

    # count sentences in summary
    sentences = summary.split('.')

    sentences_in_summary = len(sentences)
    # reduce summary if sentences_count is too high
    if sentences_in_summary > sentences_count:
        summary = sumy_summarize(summary, sentences_count)

    extractive_synopsis = sumy_summarize(sentences, 5)

    return summary, chunks, extractive_synopsis


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--filepath", type=str, help="Filepath to file", default="test/text/lorem.txt")
    argparser.add_argument("--text", type=str, help="Text to summarize",
                           default=None)
    argparser.add_argument("--sentences_count", type=int, help="Number of sentences to summarize", default=10)
    # boolean flag
    argparser.add_argument("--chunking", action="store_true", help="Use chunking to summarize long text")
    args = argparser.parse_args()
    sentences_count = args.sentences_count
    chunking = args.chunking
    if args.text is not None:
        text = args.text
    if args.filepath is not None:
        with (open(args.filepath, "r")) as f:
            text = f.read()
            # print(text)
    print("chunking flag", args.chunking)
    # print(text[:100])
    if args.chunking:
        chunked_result = chunking_sumy_summarize(text, sentences_count)
        # print(chunked_result)
        print(chunked_result[0])
        # print('chunked result', chunked_result)
    else:
        result = sumy_summarize(args.text, args.sentences_count)
        print(len(result))
        # print('result', result)
