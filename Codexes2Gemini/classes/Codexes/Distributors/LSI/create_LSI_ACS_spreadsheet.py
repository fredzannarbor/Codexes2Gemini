#  Copyright (c) 2023. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com
import logging
import math
from textwrap import shorten

import pandas as pd
from currency_converter import CurrencyConverter
from nameparser import HumanName
from Codexes2Gemini.classes.Codexes.Metadata.metadatas2distributor_reqts import initialize_LSI_ACS_variables, \
    get_rendition_string, \
    calculate_pub_date, create_draft_book_description, get_recommended_BISAC_categories, get_LSI_ACS_keywords, \
    calculate_min_max_age_grade, process_acrobat_toc, get_rendition_index, estimate_price
import streamlit as st

def create_LSI_ACS_spreadsheet(metadatas, config=None):
    logging.info("beginning to create ISBN spreadsheet")
    metadatas = metadatas.get_all_attributes()
    isbn = metadatas['ISBN']

    rendition_string, LSI_ACS_publisher, imprint, usd2gbp, jacket_filepath, interior_filepath, cover_filepath = initialize_LSI_ACS_variables(
        metadatas)
    c = CurrencyConverter(fallback_on_missing_rate=True)
    df = pd.DataFrame(index=range(1))
    df["Lightning Source Account #"] = "6024045"
    df["Metadata Contact Dictionary"] = "Fred Zimmerman"
    df['Parent ISBN'] = metadatas['ISBN'].replace('-', '')
    df['ISBN or SKU'] = metadatas['ISBN'].replace('-', '')  # config needed
    # print(df['ISBN or SKU'])
    rendition_string = get_rendition_string(metadatas)
    df['Rendition /Booktype'] = rendition_string
    df['Title'] = metadatas['title']
    df['Publisher'] = "W. Frederick Zimmerman"  # LSI_ACS_publisher  # working
    df['Imprint'] = "Nimble Books LLC"  # working
    df['Cover/Jacket Submission Method'] = 'FTP'  # done
    df['Text Block SubmissionMethod'] = 'FTP'  # done

    df['human_name'] = rearrange_name(metadatas['author'])
    metadatas['human_name'] = df['human_name']
    df['Contributor One'] = metadatas['human_name']

    df['Contributor One Role'] = "A"  # lookup contributor_role_
    # function to decide on rendition costs index
    df['Reserved 1'] = ""  # done
    df['Reserved 2'] = ""  # done
    df['Reserved 3'] = ""  # done
    df['Reserved 4'] = ""  # done
    df['Custom Trim Width (inches)'] = "NA"  # done
    df['Custom Trim Height (inches)'] = "NA"  # done
    df['Weight(Lbs)'] = "NA"  # done

    df['Reserved5'] = ""  # done
    df['Reserved6'] = ""  # done
    df['Reserved7'] = ""  # done
    df['Reserved8'] = ""  # done
    # TODO: write function to extract front cover image from cover PD
    df['Marketing Image'] = ''  # 'resources/images/placeholder-page001.jpeg'
    df['Pages'] = 0  # metadatas['final page count']
    pub_date = calculate_pub_date()
    df['Pub Date'] = pub_date  # metadatas['publication date']
    df['Street Date'] = ''  # metadatas['publication date']
    df['Territorial Rights'] = 'World'  # informational # done
    contributing_editor = None  # default
    editor = "Zimmerman, Fred"
    if contributing_editor is not None:
        df['Contributor Two'] = contributing_editor
        df['Contributor Two Role'] = "E"
    else:
        df['Contributor Two'] = editor
        df['Contributor Two Role'] = "E"
    df['Contributor Three'] = ''
    df['Contributor Three Role'] = ''
    df['Edition Number'] = ''
    international_edition = False
    if international_edition == True:
        edition_name = 'Global Edition'
        df['Edition Description'] = edition_name
    else:
        df['Edition Description'] = ''
    try:
        df['Jacket Path / Filename'] = jacket_filepath
        df['Interior Path / Filename'] = interior_filepath
        df['Cover Path / Filename'] = cover_filepath
    except Exception as e:
        print(f"Exception: {e}")
    try:
        # metadatas['Annotation / Summary'] = create_draft_book_description(metadatas)
        metadatas['Annotation / Summary'] = st.session_state.current_plan["gemini_summary"]
        df['Annotation / Summary'] = metadatas['Annotation / Summary']
    except Exception as e:
        print(e)
        df['Annotation / Summary'] = ''
        print("problem creating book description draft ")
    df['Reserved (Special Instructions)'] = ''  # done
    df['LSI Special Category  (please consult LSI before using'] = ''
    df['Stamped Text LEFT'] = ''
    df['Stamped Text CENTER'] = ''  # done
    df['Stamped Text RIGHT'] = ''  # done
    df['Order Type Eligibility'] = 'POD-Distribution & Short Run'  # done
    df['Returnable'] = True  # done
    recommended_BISAC_categories = get_recommended_BISAC_categories(metadatas)
    print('made it to BISAC')
    if len(recommended_BISAC_categories) > 0:
        df['BISAC Category'] = recommended_BISAC_categories[0]
    else:
        df['BISAC Category'] = 'N/A'
    df['Language Code'] = "English"
    df['LSI FlexField1 (please consult LSI before using)'] = ''  # done
    df['LSI FlexField2 (please consult LSI before using)'] = ''  # done
    df['LSI FlexField3 (please consult LSI before using)'] = ''  # done
    df['LSI FlexField4 (please consult LSI before using)'] = ''  # done
    df['LSI FlexField5 (please consult LSI before using)'] = ''  # done
    df['Reserved11'] = ''  # done
    df['Reserved12'] = ''  # done
    print('made to to BISACs 2 and 3')
    if len(recommended_BISAC_categories) == 1:
        df['BISAC Category 2'] = ''
        df['BISAC Category 3'] = ''
    if len(recommended_BISAC_categories) == 2:
        df['BISAC Category 2'] = recommended_BISAC_categories[1]
        df['BISAC Category 3'] = ''
    if len(recommended_BISAC_categories) > 2:
        df['BISAC Category 2'] = recommended_BISAC_categories[1]
        df['BISAC Category 3'] = recommended_BISAC_categories[2]
    df['Publisher Reference ID'] = ''
    df['Reserved9'] = ''
    df['Reserved10'] = ''
    df['Carton Pack Quantity'] = ''  # never going to need this
    df['Contributor One BIO'] = ' '
    df['Contributor One Affiliations'] = ' '
    df['Contributor One Professional Position'] = ' '
    df['Contributor One Location'] = ' '
    df['Contributor One Location Type Code'] = ' '
    df['Contributor One Prior Work'] = ' '
    # st.write('testing metadatas', metadatas)
    metadatas = get_LSI_ACS_keywords(metadatas, "Bibliographic Keyword Phrases")
    print('exited get keywords')
    # print(metadatas)
    try:
        df['Keywords'] = metadatas['keywords']
        # TODO: write function to recommend THEMA parameters
        df['Thema Subject 1'] = ''
        df['Thema Subject 2'] = ''
        df['Thema Subject 3'] = ''
        df['Regional Subjects'] = ''
        df['Min Age'] = metadatas['min_age']
        df['Max Age'] = metadatas['max_age']
        df['Min Grade'] = metadatas['min_grade']
        df['Max Grade'] = metadatas['max_grade']
        metadatas['Audience'] = 'General/Trade'  # default
        df['Audience'] = 'General/Trade'  # other options include "Young Adult"
        metadatas = calculate_min_max_age_grade(metadatas)
        df['Short Description'] = shorten(metadatas['TLDR'], 250)  # need new preset😂
        print('bisect')
        toc_string = process_acrobat_toc(metadatas)
        df['Table of Contents'] = toc_string  # need new function
        df['Review Quote(s)'] = ''  # need new function
        df['# Illustrations'] = '' \
                                ''  # in future count number of "Figure" captions in text
        df['Illustration Notes'] = ''
        df['Series Name'] = ''
        df['# in Series'] = ''
        df['color_interior'] = metadatas['color_interior']
    except Exception as e:
        print('Exception: ', e)
    print('assigned color interior bool')
    # print('type of metadatas color inteiror')
    # print(type(metadatas['color_interior']))
    metadatas['rendition_string'] = rendition_string
    metadatas['rendition_costs_index'] = get_rendition_index(rendition_string, metadatas['color_interior'])
    rci = 3  # hardcoded for now
    us_list_price = estimate_price(rci, metadatas['pagecount'], metadatas['color_interior'], profit_goal=10)
    us_list_price = math.ceil(us_list_price) - 0.01
    print(f"us_list_price: {us_list_price}")
    df['US Suggested List Price'] = us_list_price  # metadatas['recommended price']
    # round up to nearest 0.01
    min_discount = 40
    df['US Wholesale Discount'] = min_discount
    uk_list_price = round(us_list_price * usd2gbp, 2)
    uk_list_price = math.ceil(uk_list_price) - 0.01
    df['UK Suggested List Price'] = uk_list_price  # calculate in future
    df['UK Wholesale Discount (%)'] = min_discount

    eu_list_price = round(us_list_price * c.convert(1, 'USD', 'EUR'), 2)
    df['EU Suggested List Price (mode 2)'] = eu_list_price
    df['EU Wholesale Discount % (Mode 2)'] = min_discount

    au_list_price = round(us_list_price * c.convert(1, 'USD', 'AUD'), 2)
    df['AU Suggested List Price (mode 2)'] = au_list_price
    df['AU Wholesale Discount % (Mode 2)'] = min_discount

    ca_list_price = round(us_list_price * c.convert(1, 'USD', 'CAD'), 2)
    df['CA Suggested List Price (mode 2)'] = ca_list_price
    df['CA Wholesale Discount % (Mode 2)'] = min_discount

    df['GC Suggested List Price (mode 2)'] = us_list_price
    df['GC Wholesale Discount % (Mode 2)'] = min_discount

    gcdict = {"USBR1 Suggested List Price (mode 2)": us_list_price, "USBR1 Wholesale Discount % (Mode 2)": min_discount,
              "USDE1 Suggested List Price (mode 2)": us_list_price, "USDE1 Wholesale Discount % (Mode 2)": min_discount,
              "USRU1 Suggested List Price (mode 2)": us_list_price, "USRU1 Wholesale Discount % (Mode 2)": min_discount,
              "USPL1 Suggested List Price (mode 2)": us_list_price, "USPL1 Wholesale Discount % (Mode 2)": min_discount,
              "USCN1 Suggested List Price (mode 2)": us_list_price, "USCN1 Wholesale Discount % (Mode 2)": min_discount,
              "USKR1 Suggested List Price (mode 2)": us_list_price, "USKR1 Wholesale Discount % (Mode 2)": min_discount,
              "USIN1 Suggested List Price (mode 2)": us_list_price, "USIN1 Wholesale Discount % (Mode 2)": min_discount,
              "USJP2 Suggested List Price(mode 2)": us_list_price, "USJP2 Wholesale Discount % (Mode 2)": min_discount,
              "UAEUSD Suggested List Price (mode 2)": us_list_price,
              "UAEUSD Wholesale Discount % (Mode 2)": min_discount,
              "US-Ingram-Only* Suggested List Price (mode 2)": '', "US-Ingram-Only* Wholesale Discount % (Mode 2)": '',
              "US - Ingram - GAP * Suggested List Price (mode 2)": '',
              "US - Ingram - GAP * Wholesale Discount % (Mode 2)": '',
              "SIBI - EDUC - US * Suggested List Price(mode 2)": '',
              "SIBI - EDUC - US * Wholesale Discount % (Mode 2)": ''}
    gcdf = pd.DataFrame(gcdict, index=[0])
    # print(gcdf.shape)

    df = pd.concat([df, gcdf], axis=1, sort=False)
    # print(df.shape)
    # print(df.columns)
    print(df.head())
    return df


def rearrange_name(full_name):
    name = HumanName(full_name)
    # Reconstruct the name in the format "Last, First"
    rearranged_name = f"{name.last}, {name.first}"
    return rearranged_name.strip()

    # Example usage
    full_name = "John Doe"
    rearranged_name = rearrange_name(full_name)
    print(rearranged_name)
