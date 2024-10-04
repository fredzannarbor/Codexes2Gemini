import json
import logging
from datetime import datetime, timedelta
from textwrap import shorten
from importlib import resources
import streamlit as st

import pandas as pd
import traceback


def load_data_table(file_name):
    data_table_resource_path = resources.files('resources.data_tables.LSI').joinpath(file_name)
    try:
        with data_table_resource_path.open('r') as file:
            data_table = pd.read_csv(file)
            return data_table
    except Exception as e:
        with f"resources/data_tables/LSI/{file_name}".open('r') as file:
            data_table = pd.read_csv(file)
            return data_table
    except Exception as e:
        logging.error(
            f"Could not load rendition.csv from either package or local file sysytem -- i.e. resources. or resources/")
        st.error((
                     f"Could not load rendition.csv from either package or local file sysytem -- i.e. resources. or resources/"))
        exit()


# class DistributorMetadata:
def book_metadata_json2distributor_format_targets(self, distributor_format_target="LSI", thisdoc_dir=''):
    with open("resources/json/book_metadata_objects.json", "r") as f:
        book_metadata_objects = json.load(f)
        # print(book_metadata_objects)

    KDP_targets = book_metadata_objects[1]["KDP required fields"]
    LSI_targets = book_metadata_objects[2]["LSI required fields"]
    LSI_ACS_required_fields = book_metadata_objects[3]["LSI ACS required fields"]

    return KDP_targets, LSI_targets, LSI_ACS_required_fields


def find_first_tuesday(year, month, day):
    d = datetime(year, int(month), 7)
    offset = -d.weekday()  # weekday = 0 means monday
    return d + timedelta(offset)


# find first tuesday of next month
def find_first_tuesday_of_next_month(year, month, day):
    d = datetime(year, int(month), 7)
    offset = -d.weekday()  # weekday = 0 means monday
    return d + timedelta(offset + 28)


# find tuesday N weeks ahead
def find_tuesday_N_weeks_ahead(year, month, day, N):
    d = datetime(year, int(month), 7)
    offset = -d.weekday()  # weekday = 0 means monday
    return d + timedelta(offset + (N * 7))


def initialize_LSI_ACS_variables(metadatas):
    rendition_booktype_pair = 'POD: 8.5 x 11 in or 280 x 216 mm Case Laminate on White'
    LSI_ACS_publisher = 'W. Frederick Zimmerman'
    imprint = 'Nimble Books LLC'
    usd2gbp = 0.88  # create function
    safeISBN = str(metadatas['ISBN'].replace('-', '')[0])
    jacket_filepath = ''
    interior_filepath = safeISBN + '_interior.pdf'
    cover_filepath = safeISBN + '_cover.pdf'
    return rendition_booktype_pair, LSI_ACS_publisher, imprint, usd2gbp, jacket_filepath, interior_filepath, cover_filepath


def get_LSI_ACS_keywords(metadatas, source="Keywords"):
    if source == "Keywords":
        keywords_list = metadatas.get('keywords_text_list')
        keywords = [keyword.lstrip('\n') for keyword in keywords_list]
    elif source == "Bibliographic Keyword Phrases":
        keywords = metadatas.get('Bibliographic_Keyword_Phrases')
        print('bkb keywords: ', keywords)
        if keywords:
            keywords = [keyword.lstrip('\n') for keyword in keywords][1:]
            keywords = ';'.join(keywords)
        else:
            keywords = ""
    else:
        print("no source for automatic keywords")
        keywords = ""

    # ensure keywords is a list for the following loop.
    if isinstance(keywords, str):
        keywords = keywords.split(';')

    keyphrases = [shorten(keyword, width=450, placeholder="...") for keyword in keywords]

    metadatas.update({'keywords': keyphrases})
    metadatas.update({'source': source})
    # print(metadatas)
    return metadatas


def get_rendition_index(rendition_string, color_interior=True):
    rendition_costs_df = load_data_table("rendition_costs.csv")

    # Change 'rendition_name' to the actual rendition string and 'color' to the actual color interior value
    rendition_name = rendition_string
    rendition_costs_df['color_interior'] = rendition_costs_df['color_interior'].astype(bool)

    color = color_interior
    # print(rendition_costs_df)
    print(rendition_name)
    print(f"color interior: {color_interior}")
    cols = rendition_costs_df.columns
    filtered = rendition_costs_df[rendition_costs_df['rendition_string'] == rendition_string]
    # print(filtered.head())
    # Select rows where color_interior matches
    matching_rows = filtered[filtered['color_interior'] == color_interior]
    # print(filtered['color_interior'].head())
    # print(type(color_interior))
    # If there is no matching rows, return an empty DataFrame
    if matching_rows.empty:
        print('mr empty')
        return matching_rows

    # Find the minimum unit cost
    print('finding unit cost')
    min_unit_cost = matching_rows['unit_cost'].min()
    print(min_unit_cost)
    # Select rows with the minimum unit cost
    min_cost_rows = matching_rows[matching_rows['unit_cost'] == min_unit_cost]
    print(f"there are {len(min_cost_rows)} formats with this minimum unit cost")
    # If there is a tie on unit cost, break with 'cost per page' by sorting
    sorted_rows = min_cost_rows.sort_values('cost_per_page', ascending=True)
    print(sorted_rows)
    # Return the first row of the sorted DataFrame
    print(sorted_rows.iloc[0])
    return sorted_rows.iloc[0]


def estimate_price(rendition_costs_index, pagecount, color_interior, profit_goal=10):
    try:
        rendition_costs_df = pd.read_csv('resources/data_tables/LSI/rendition_costs.csv')
    except FileNotFoundError:
        print("The file 'resources/data_tables/LSI/rendition_costs.csv' doesn't exist.")
        return

    pagecount = int(pagecount)
    if pagecount is not None:
        try:
            rendition_costs_index = int(rendition_costs_index)
            assert 0 <= rendition_costs_index < len(rendition_costs_df)
        except ValueError:
            print("rendition_costs_index must be convertible to an integer.")
            return
        except AssertionError:
            print("rendition_costs_index must be within the data frame.")
            return

        costperpage = rendition_costs_df.iloc[rendition_costs_index, 3]
        costperunit = rendition_costs_df.iloc[rendition_costs_index, 2]
        printing_cost = costperunit + (pagecount * costperpage)
        print(f"costperpage is ${costperpage}, costperunit is ${costperunit}")
        print(f"pagecount is {pagecount}")
        print(f"printing cost is {printing_cost}")

        if profit_goal == 0:
            print("Profit goal can't be zero.")
            return
        print(f"profit goal is ${profit_goal}")

        return (profit_goal + printing_cost) / 0.7
    else:
        return 99.00


def get_recommended_BISAC_categories(metadatas):
    try:
        BISACs = metadatas['BISAC_CategoryRecommender'].split(';')
        BISACs = [BISAC.lstrip('\n') for BISAC in BISACs]
        controlled_vocabulary_BISACs = []
        for b in BISACs:
            # look up BISAC codes in BISACs.json
            # use fuzzy matching to get controlled vocabulary values
            newBISACpair = {'BISAC': b, 'controlled vocabulary': 'TBD'}
            # print('not yet able to fuzzy match BISAC codes')
            controlled_vocabulary_BISACs.append(newBISACpair)
        print(f"found {len(BISACs)} BISACs exactly matching controlled vocabulary")
        print(controlled_vocabulary_BISACs)
    except Exception as e:
        metadatas['Recommended BISAC Categories'] = "TBD"
        BISACs = metadatas['Recommended BISAC Categories']
        controlled_vocabulary_BISACs = "TBD"

    return BISACs, controlled_vocabulary_BISACs


def get_rendition_string(metadatas):
    # KISS version
    # print(metadatas.keys())
    height, width = metadatas['pageheights'], metadatas['pagewidths']
    print('height: ', height, 'width: ', width)
    if height == 8.5 and width == 11.0:
        rendition_string = 'POD: 8.5 x 11 in or 280 x 216 mm Perfect Bound on White'
    else:
        rendition_string = 'POD: 8.5 x 11 in or 280 x 216 mm Perfect Bound on White'
    # TODO: add all pairs, or a lookup table in sources_of_truth
    return rendition_string


def create_draft_book_description(metadatas):
    try:
        book_description = metadatas['motivation'] + '\n' + metadatas['submit_synopsis'] + '\n' + metadatas[
            'description_of_annotations'] + '\n' + metadatas['source_text']
        book_description = book_description.replace("\n\n", "\n")
        book_description = "test"
        print("created full book description")
        # print(book_description)
    except Exception as e:
        st.error(traceback.format_exc())
        print('couldnae assemble bd')
        # zabook_description = "**DRAFT** \n" + metadatas_df['Book Description'][1] + '\n' + metadatas_df['Book Cover Blurb'][1] + '\n ' + metadatas_df['description_of_annotations'][1]
    return book_description


def process_acrobat_toc(metadatas):
    # print('processing acrobat toc')
    toc_list_of_lists = metadatas['toc']
    # print(toc_list_of_lists)
    toc_list_of_strings = []
    print(f" {len(toc_list_of_lists)} items in PDF ToC")
    # print(toc_list_of_lists[0])
    if len(toc_list_of_lists) >= 2:
        for item in toc_list_of_lists:
            # print(item)
            level = item[0]
            value = item[1]
            # page number = item[2] but we don't need that right now
            if level == 1:
                # print(f"level: {level}, value: {value}")
                toc_list_of_strings.append(value)
            if level == 2:
                # print(f"level: {level}, value: {value}")
                toc_list_of_strings.append(f"    {value}")
        toc_string = '\n'.join(toc_list_of_strings)
        # try using OpenAI to summarize toc
        # try converting to markdown then taking top 2 levels
    if len(toc_list_of_lists) < 2:
        print('no extractable toc')
        toc_string = ''

    return toc_string


def calculate_min_max_age_grade(metadatas):
    if metadatas['Audience'] == 'Young Adult':
        metadatas['Min Age'] = 13
        metadatas['Max Age'] = 18
        metadatas['Min Grade'] = 8
        metadatas['Max Grade'] = 12
    elif metadatas['Audience'] == 'Children/Juvenile':
        metadatas['Min Age'] = 0
        metadatas['Max Age'] = 12
        metadatas['Min Grade'] = 0
        metadatas['Max Grade'] = 7
    else:
        metadatas['Min Age'] = ''
        metadatas['Max Age'] = ''
        metadatas['Min Grade'] = ''
        metadatas['Max Grade'] = ''
    return metadatas


def calculate_pub_date():
    current_month = datetime.now().month
    # get current year
    current_year = datetime.now().year
    # get current day
    current_day = datetime.now().day
    next_month = current_month + 1
    pub_date = find_first_tuesday_of_next_month(current_year, current_month, current_day)
    return pub_date


def prepare_for_KDP_data_entry(metadatas):
    df = metadatas
    KDP_fields = book_metadata_json2distributor_format_targets("KDP")
    # create df columns using KDP_fields
    for field in KDP_fields:
        df[field] = ""
    # fill in df columns using KDP_fields
    df['Title'] = metadatas['title']

    return
