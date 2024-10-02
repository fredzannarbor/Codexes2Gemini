import argparse

from abbreviations import schwartz_hearst


def text2abbreviations(text, most_common_definition=True, first_definition=False):
    abbreviations = schwartz_hearst.extract_abbreviation_definition_pairs(text)
    return abbreviations


if __name__ == "__main__":
    text = "The quick brown fox jumps over the lazy dog."

    argparser = argparse.ArgumentParser()
    argparser.add_argument('--text', help='text to be processed', default=text)
    argparser.add_argument('--most_common_definition', help='output most common definition', default=True)
    argparser.add_argument('--first_definition', help='output first definition', default=False)
    argparser.add_argument('--output_dir', help='path to output directory', default='output')
    argparser.add_argument('--filename', help='filename', default='test/txt/granddaughter.txt')
    args = argparser.parse_args()

    if args.filename:
        results = text2abbreviations(args.filename, args.most_common_definition, args.first_definition)
    else:
        results = text2abbreviations(args.text, args.most_common_definition, args.first_definition)

    print(results)
    # output dir should be thisdoc_dir when called
    with open(args.output_dir + '/abbreviations.txt', 'w') as f:
        f.write(str(results))
