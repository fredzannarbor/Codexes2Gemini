import os
import sys

import pandas as pd

# from app.utilities.gensim_summarizer import gensim_summarizer
from app.utilities.gpt3complete import (gpt3complete, post_process_text, presets_parser)
from app.utilities.text2extractive_summary import create_extractive_summary_as_list

# import sleep
#


'''
    The following fields are required on the KDP Details page.

    - Language*
    - Book Title
    - Book Subtitle
    - Series*
    - Series Number*
    - Edition Number*
    - Publisher*
    - Primary Author or Contributor*
    - Prefix, First Name, Middle Name, Last Name*
    - Description
    - Publishing Rights*
    - Keywords
    - Categories

    The fields marked with an asterisk are clerical in nature and simply require accurately entering known information. **The remaining fields need to be created by the author or publisher.** This task can be both vitally important to the book's sales and quite time-consuming.
    '''


def common_presets_for_metadata():
    common_presets = {'TitleFromDescription': 'Title & Subtitle',
                      'BibliographicKeywordsGenerator': 'Bibliographic Keywords',
                      'BookDescriptionWriter': 'Book Detail Page Description',
                      'BISAC_CategoryRecommender': "BISAC Categories", "BlurbWriter": "Back Cover Blurb Writer", }
    return common_presets


def create_title_metadata_using_openai(summary_sentences_string, output_dir='output', engine="text-curie-001"):
    # returns result list df
    print('summary_sentences_string', summary_sentences_string)
    preset_dict = common_presets_for_metadata()
    print(preset_dict)

    result_list = []

    KDP_presets = ["TitleFromDescription", "BibliographicKeywordsGenerator", "BookDescriptionWriter",
                   "BISAC_CategoryRecommender", "BlurbWriter"]

    KDP_results_df = pd.DataFrame({'Title Ideas': pd.Series(dtype='str'),
                                   'Bibliographic Keywords': pd.Series(dtype='str'),
                                   'Description': pd.Series(dtype='str'), 'BISAC categories': pd.Series(dtype='str'),
                                   'Blurb': pd.Series(dtype='str'), })

    if KDP_presets:
        actual_responses = []
        for preset in KDP_presets:
            current_presetdf = presets_parser(preset)[0]
            preset_result_df = pd.DataFrame()

            try:
                print(engine)

                current_response = gpt3complete(preset, summary_sentences_string, engine, echo_on=True)
                actual_responses.append(current_response)
                current_response_text = current_response[0]['choices'][0]['text']
                current_response_text = post_process_text(current_response_text)
                completion_heading = f"{current_presetdf['completion_heading'].iloc[0]}"
                append_item = (completion_heading, current_response_text)
                result_list.append(append_item)

            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
        actual_responses_df = pd.DataFrame(actual_responses)
        actual_responses_df.to_json(f'{output_dir}/actual_responses.json')
    result_list_df = pd.DataFrame(result_list)
    return result_list_df


def create_series_metadata_using_openai(summary_sentences_string):
    '''
    Additional metadata is required for books that are part of a series. If you are in doubt as to whether a book should be considered part of a series, note that over time Amazon has added a lot of features to support them.  Series sell.
    '''

    series_result_list = []
    new_series = True
    main_content = True
    if new_series:
        if main_content == 'Yes':

            series_dict = {'SeriesTitleOnlyGenerator': 'Series Title Ideas',
                           'SeriesTitleandDescriptionGenerator': 'Series Title & Description  Ideas',
                           'SeriesSequelTitles': 'Series Sequel Ideas',
                           'SeriesDescriptionGenerator': 'Series Description'}
            series_presets = ["SeriesTitleOnlyGenerator", 'SeriesDescriptionGenerator',
                              "SeriesTitleandDescriptionGenerator"]
            if series_presets:
                for preset in series_presets:
                    series_presetdf = presets_parser(preset)

                    series_response = gpt3complete(preset, summary_sentences_string, engine="text-davinci-003")

                    series_result_list.append(series_response[0]
                                              ['choices'][0]['text'])

    return series_result_list


if __name__ == "__main__":
    filename = ('app/utilities/data/granddaughter.txt')
    with open(filename, 'r') as f:
        teststring = f.read()
    synopsis = create_extractive_summary_as_list(teststring, 1000, 'output', True)
    print(len(synopsis.split(' ')))
    print('synopsis is', synopsis)
    results = create_KDP_title_metadata(synopsis)
