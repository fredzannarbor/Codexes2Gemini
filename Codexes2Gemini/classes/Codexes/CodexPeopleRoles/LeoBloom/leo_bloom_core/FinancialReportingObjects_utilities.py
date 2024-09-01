import os

import pandas as pd

"""
Selected helper utilities for the FinancialReportingObjects class module
"""


def load_spreadsheet(filename):
    """
    Load a spreadsheet file into a pandas DataFrame.

    Parameters:
    filename (str): File path to the spreadsheet.


    Returns:
    DataFrame: pandas DataFrame with the spreadsheet data.

    Try utf-8 encoding first for csv, then ISO-8859-1, then Win-1252

    """
    # Check the file extension
    _, extension = os.path.splitext(filename)

    if extension == '.csv':
        encoding_options = ['utf-8', 'ISO-8859-1', 'Win-1252']
        for encoding in encoding_options:
            try:
                df = pd.read_csv(filename, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue

    elif extension == ".xlsx":
        df = pd.read_excel(filename, engine='openpyxl')

    elif extension == ".xls":
        df = pd.read_excel(filename)

    return df


def add_amazon_buy_links(df):
    df['amazon_buy_link'] = 'https://www.amazon.com/dp/' + df['isbn_10_bak'].astype(str) + '?tag=ai4bookloversgpt-20'
    return df
