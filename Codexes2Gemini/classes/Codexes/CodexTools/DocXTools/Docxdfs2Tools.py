#  Copyright (c) 2023. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com


import os

import pandas as pd

from app.utilities.gpt3complete import chatcomplete
from app.utilities.utilities import make_basename_safe

# from classes.SyntheticReaders.RatingUtilities import

'''
1. This class accepts dataframes generated from docx objects by DocxCodex2Objects
2. It adds columns to the dataframes that are useful for LLM.
3. It sends the dataframe to the tools and receives the results.
'''


class Docxdfs2Tools:
    '''
    We need the following attributes for the class.
    1. What dataframe types are supported
    --combined_df
    --image_df
    --list_of_tables
    '''

    def __init__(self, combined_df, image_df, list_of_tables):
        # lists of combined_dfs
        self.combined_df = combined_df
        self.image_df = image_df
        self.list_of_tables = list_of_tables

    def dfvalidate(df):
        # validate file is valid dataframe
        try:
            df = pandas.DataFrame(df)
        except Exception as e:
            return False
        return True

    def docxdfs2presets(self, docxdfs: list, presets: list, rows=10, beginning_row=0, ending_row=10,
                        model="gpt-3.5-turbo"):
        for df in docxdfs:
            if isinstance(docxdfs, list):
                results = []
                for df in docxdfs:
                    print('iterating through df rows')
                    print(docxdfs, presets, rows, beginning_row, ending_row)
                    # iterate through df rows
                    for index, row in df.iterrows():
                        text = row['para_text']
                        # send text to presets
                        for preset in presets:
                            response_text = chatcomplete(preset, text, model=model)
                            result = response_text
                            print(result)
                            # add result to current row of df
                            df.loc[index, preset] = result
                        if index > rows:
                            break
                print(df.head(5))
            return docxdfs

    def tuplefile2results(self, tuplefile, rows=3):
        # read csv that contains tuples that are completion parameters
        # send each tuple to GPT-3
        # return results
        # open csv or excel file
        # if there is no file, create a dataframe by that name
        if os.path.exists(tuplefile):
            print(f'Found {tuplefile}')
        else:
            print(f'No file found named {tuplefile}')
            return
        if tuplefile.endswith('.csv'):
            df = pd.read_csv(tuplefile)
        if tuplefile.endswith('.xlsx'):
            df = pd.read_excel(tuplefile)
        if tuplefile.endswith('.xls'):
            df = pd.read_excel(tuplefile)

        # iterate through df rows
        source_df_file = ''
        writefilenames = []
        for index, row in df.iterrows():
            if row['docxfilename'] == source_df_file:
                row['docxfilename'] = f"source_df_{index}.csv"
            source_df_file = row['docxfilename']
            if os.path.exists(source_df_file):
                print(f'Found {source_df_file}')
                source_df = pd.read_csv(source_df_file)
            else:
                print(f'No file found named {source_df_file}')
                source_df = pd.DataFrame()
                source_df.to_csv(source_df_file)
            # get parameters from column heading
            # hardcode for now
            for index2, row2 in source_df.iterrows():
                # send tuple to GPT-3
                prompt = row['prompt']
                response_text = chatcomplete(row['preset'], prompt, "gpt-3.5-turbo-16k")
                # add result to current row of df
                df.loc[index, 'result'] = response_text
                if index > rows:
                    # save source_df to output file
                    writefilename = make_basename_safe(source_df_file) + '.csv'
                    try:
                        source_df.to_csv(writefilename)
                    except Exception as e:
                        print(e)
                    writefilenames.append
                    print(f'Wrote {writefilename}')
                    print(source_df.head(5))
                    break
            print(f"wrote files {writefilenames}")
        return
