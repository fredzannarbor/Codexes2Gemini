import argparse

import pandas as pd


def load_BISAC_data_table(path2df):
    df = pd.read_csv(path2df)

    return df


# @st.cache_data
def am_I_a_valid_BISAC_code(checkthiscode=None, usethisdf=None):
    # checks is string is BISAC *code*, e.g. ANT002000
    if checkthiscode is None:
        return None
    if usethisdf is None:
        return None
    if checkthiscode in usethisdf['Code'].values:
        print(f"{checkthiscode}: True")
        return True
    else:
        print(f"{checkthiscode}: False")
        return None


def am_I_a_valid_BISAC_description(checkthisdescription=None, usethisdf=None):
    # checks ifs string is an exact BISAC description, e.g. ANTIQUES & COLLECTIBLES / Art
    if checkthisdescription is None:
        return None
    if usethisdf is None:
        return None

    if checkthisdescription in usethisdf['Description'].values:
        print(f"{checkthisdescription}: True")
        return True
    else:
        print(f"{checkthisdescription}: False")
        return False


def BISAC_code2BISAC_description(code, df):
    # function that takes a BISAC code and
    # returns the BISAC code and description
    if code is None:
        return None
    if df is None:
        return None

    description = df[df['Code'] == code]['Description'].values[0]
    print(f"BISAC code {code} is {description}")
    return description
    # get the BISAC codes that match the text


def text2validBISAC(text, df):
    if text is None:
        return None
    if df is None:
        return None

    matches = df[df['Description'].str.contains(text)]
    if len(matches) == 0:
        return None
    return matches.loc['Code']


def list_of_text_descriptions2valid_BISAC(list_of_text, df):
    if list_of_text is None:
        return None
    if df is None:
        return None
    # get the BISAC codes that match the text
    matches = []
    for l in list_of_text:
        r = am_I_a_valid_BISAC_description(l, df)
        matches.append(r)
    if len(matches) == 0:
        return None
    print(f"matches:  {matches}")
    return matches


def read_list_of_BISACs_from_file(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
        print(f"read {len(lines)} lines of BISAC descriptions")
    return lines


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--description', type=str, default="HISTORY / Military / Naval", help='BISAC slash taxonomy')
    parser.add_argument('--code', type=str, default="HIS027150", help='BISAC code')
    parser.add_argument('--path2df', type=str, default="resources/data_tables/BISG/BISAC.csv",
                        help='path to BISAC data table')
    parser.add_argument('--list_of_text', type=str, default="HISTORY / Military / Naval", help='list of text')
    args = parser.parse_args()
    description = args.description
    code = args.code
    path2df = args.path2df
    list_of_text = args.list_of_text
    df = load_BISAC_data_table(path2df)

    lines = read_list_of_BISACs_from_file("resources/data_tables/BISG/example_BISACs.txt")
    lines_test = list_of_text_descriptions2valid_BISAC(lines, df)
    description = am_I_a_valid_BISAC_description('ANT002000', usethisdf=df)
    checkresult = am_I_a_valid_BISAC_code(code, df)
    description = BISAC_code2BISAC_description(code, df)
