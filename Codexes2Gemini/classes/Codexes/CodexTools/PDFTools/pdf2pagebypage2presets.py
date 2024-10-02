import argparse

import pandas as pd
from app.utilities.ADEPT_enhance_bulk_PDFs import pdf2text2df
from app.utilities.textdf2aiservices import text_df_to_ai_services


def pdf2pagebypage(file_path, presets, page_limit, output_dir):
    text_tuple = pdf2text2df(file_path, page_limit, "working/public_domain/today")
    text = text_tuple[0]
    text_df = text_tuple[1]
    result = text_df_to_ai_services(text_df, presets)
    result_df = pd.DataFrame(result)
    # result_df.columns = ['page', 'text', 'preset']
    # result_df.to_json(output_dir + "/result.json")
    return result_df


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--input_file", "-i", help="input file", default="test/pdf/Logan3pp.pdf")
    argparser.add_argument("--output_dir", "-o", help="output directory", default="test/json")
    argparser.add_argument("--presets", "-p", help="presets", nargs='+', default=['YouAreSyntheticReader'])
    argparser.add_argument("--page_limit", "-l", help="page limit", default=5)
    args = argparser.parse_args()
    input_file = args.input_file
    output_dir = args.output_dir
    presets = args.presets
    page_limit = args.page_limit

    result_df = pdf2pagebypage(input_file, presets, page_limit, output_dir)
    print(result_df)
    result_df.to_json(output_dir + "/result.json")
    result_df.to_csv(output_dir + "/result.csv")
