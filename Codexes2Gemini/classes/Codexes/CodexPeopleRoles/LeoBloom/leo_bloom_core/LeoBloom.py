# behind the scenes financial functions

import argparse
import datetime
import glob
import io
import json
import os
# change system path to include app.utilities
import urllib.request
from datetime import date

import chardet
import numpy as np
# from hydralit import HydraHeadApp
import pandas as pd
import streamlit as st
from currency_converter import ECB_URL
from isbnlib import to_isbn13, to_isbn10
from plotly import express as px


# from classes.Masthead.leo_bloom_core.MaxBialystok import FYI


# @st.cache_data
def create_date_variables():
    today = pd.to_datetime("today")
    thisyear = datetime.date.today().year
    thismonth = datetime.date.today().month
    this_year_month = str(thisyear) + '-' + str(thismonth)
    starting_day_of_current_year = datetime.date.today().replace(year=thisyear, month=1, day=1)
    daysYTD = datetime.date.today() - starting_day_of_current_year + datetime.timedelta(days=1)
    annualizer = 365 / daysYTD.days

    return today, thisyear, starting_day_of_current_year, daysYTD, annualizer, this_year_month


def ingest_and_enhance_lsi_ltd_comp(ltd_comp, full_metadata_export_df):
    st.info('arrived at ingest_and_enhance_lsi_ltd_comp')
    # st.write(ltd_comp)
    # flatten the dataframe by grouping all rows by ISBN and aggregating each row with the Net Qty and Net Compensation  columns summeed and lal others = first
    ltd_comp = ltd_comp.groupby('ISBN').agg(
        {"Net Qty": "sum", "Net Compensation": "sum", "Title": "first", "Author": "first"}).reset_index()
    # st.write(ltd_comp)

    ltd_comp['Author'] = ltd_comp['Author'].astype(str)
    # ltd_comp = ltd_comp.sort_values(by=['Net Compensation'], ascending=False)

    fme = full_metadata_export_df

    for col in fme.columns:
        if fme[col].dtype == 'object':
            fme[col] = fme[col].astype('string')
    fme_to_add = fme[['Pub Date', 'ISBN', 'Page Count', 'Booktype', 'Format', 'Status', 'US List']]
    # only include items where status == 'Available'
    fme_to_add = fme_to_add[fme_to_add['Status'] == 'Available for Printing/Download']

    fme_to_add = fme_to_add.rename(columns={'Pub Date': 'Pub Date FME'})
    ltd_comp = fme.merge(ltd_comp, how='inner', on='ISBN')

    # st.write(ltd_comp.columns)
    ltd_comp.to_excel('userdocs/37/leo_bloom_core/lsidata/ltd_compall.xlsx')
    ltd_comp = ltd_comp[
        ['Pub Date', 'Title_x', 'ISBN', 'Contributor 1 Name', 'Net Qty', 'Net Compensation', 'Page Count', 'US List']]
    ltd_comp = ltd_comp.rename(columns={'Title_x': 'Title', 'Contributor 1 Name': 'Author'})
    # identify most recent end of month day before today
    eom = pd.to_datetime('today') - pd.offsets.MonthEnd(1)
    # months in print to one decimal place

    ltd_comp['Pub Date'] = pd.to_datetime(ltd_comp['Pub Date'])
    ltd_comp['Months in Print'] = ((eom - ltd_comp['Pub Date']).dt.days / 30).round(1)
    # st.write(f"days_to_print {(eom - ltd_comp['Pub Date']).dt.days}")

    ltd_comp['Net Comp Per Month'] = (ltd_comp['Net Compensation'] / ltd_comp['Months in Print'])

    lsi_ltd_comp = ltd_comp.groupby('ISBN').agg({
        'Pub Date': 'first',
        'Title': 'first',
        'Author': 'first',
        'Page Count': 'first',
        'Months in Print': 'first',
        'Net Qty': 'sum',
        'Net Compensation': 'sum',
        'Net Comp Per Month': 'first',
        'US List': 'first'
    }).reset_index()
    # print(new_df)
    lsi_ltd_comp['Pub Date'] = pd.to_datetime(lsi_ltd_comp['Pub Date'])
    lsi_ltd_comp['Pub Date'] = lsi_ltd_comp['Pub Date'].dt.strftime('%Y-%m-%d')

    return lsi_ltd_comp


@st.cache_data
def last_day_of_month(any_day):
    # this will never fail
    # get close to the end of the month for any day, and add 4 days 'over'
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)
    # subtract the number of remaining 'overage' days to get last day of current month, or said programattically said, the previous day of the first of next month
    return next_month - datetime.timedelta(days=next_month.day)


def months_so_far_this_year(thisyear):
    # calculate number of full months that have passed so far this year
    thisyear = datetime.datetime.now().year
    thismonth = datetime.datetime.now().month
    months_so_far = thismonth - 1
    return months_so_far


@st.cache_data
def ingest_lsi(userdocs_lsidata_path):
    data = pd.DataFrame()
    hear_this = st.empty()
    lsitarget = userdocs_lsidata_path + '/' + '*.xls'
    # st.write(lsitarget)
    df = pd.DataFrame()
    for i in glob.glob(lsitarget):
        imessage = "ingesting file " + i
        hear_this.info(imessage)
        with open(i, 'rb') as f:
            result = chardet.detect(f.read())['encoding']
            if result:
                result = result.lower()
                print(result)
            else:
                print("couldn't detect encoding of excel file")
                result = 'utf-8'

        try:
            data = pd.read_excel(i)
        except Exception as e:
            # print("couldn't open data using read_excel default")
            try:
                data = pd.read_excel(i, engine="xlrd")
            except Exception as e:
                # print("couldn't open data file using xlrd")
                try:
                    data = pd.read_csv(i, sep='\t', lineterminator='\r', encoding='cp1252')
                except Exception as e:
                    print("couldn't open anything")

        # print(data)
        yearval = os.path.splitext(i)[0]

        lasttwo = yearval[-2:]
        if lasttwo == "UK":
            yearval = yearval[:-2]

        elif lasttwo == "GC":
            yearval = yearval[:-2]

        elif lasttwo == "US":
            yearval = yearval[:-2]

        elif lasttwo == "AU":
            yearval = yearval[:-2]

        else:
            pass
        yearval = yearval[-4:]
        data.insert(1, 'year', yearval)
        data = data[:-1]  # necessary to remove extra lines
        # concatenate the dataframes
        df = pd.concat([df, data], ignore_index=True)
        # df = df.append(data, ignore_index=True)

        df.to_csv('output/lsidf.csv')
    # close the hear_this object
    hear_this.empty()
    return df


# def lsi_row_filler(df, BIPtruth):

#     return padded_df

def set_column_value_formats(df):
    twodecimals = ['lmip', 'PTD_avg_list_price', 'PTD_extended_list', 'PTD_avg_discount_ %', 'PTD_avg_wholesale_price',
                   'PTD_extended_wholesale', 'PTD_avg_print_charge', 'PTD_extended_print_charge', 'PTD_gross_pub_comp',
                   'PTD_extended_adjustments', 'PTD_extended_recovery', 'PTD_pub_comp', 'YTD_avg_list_price',
                   'YTD_extended_list_price', 'YTD_avg_discount_ %', 'YTD_avg_wholesale_price',
                   'YTD_extended_wholesale', 'YTD_avg_print_charge', 'YTD_extended_print_charge', 'YTD_gross_pub_comp']

    for i in twodecimals:
        if i in df.columns:
            df[i] = df[i].apply(lambda x: float("{:.2f}".format(x)))
        else:
            pass
    return df


@st.cache_data
def ingest_kdp_lifetime_data(filepath):
    kdpdata = pd.read_excel(filepath, 'Combined Sales')
    FYI = st.empty()
    FYI.info('getting foreign exchange rates')
    filename = f"ecb_{date.today():%Y%m%d}.zip"
    print(filename)
    if not os.path.isfile(filename):
        print('retrieving', ECB_URL)
        urllib.request.urlretrieve(ECB_URL, filename)
    else:
        print('file already exists')
    c = CurrencyConverter(filename, fallback_on_wrong_date=True, fallback_on_missing_rate=True)
    print('loaded', filename)

    #  ingest_kdp initially supports only post-2015 format KDP data

    # for each row, get the year from Royalty Date by doing a split
    # then get the month from Royalty Date by doing a split
    kdpdata['year'] = kdpdata['Royalty Date'].apply(lambda x: x.split('-')[0])
    kdpdata['month'] = kdpdata['Royalty Date'].apply(lambda x: x.split('-')[1])

    # kdpdata['month'] = kdpdata['Royalty Date'].split()[1]
    # kdpdata['year'] = kdpdata['Royalty Date'].split()[0]
    # long_month_name = kdpdate.split()[0]
    # year_name = kdpdate.split()[1]
    # month_number = datetime.datetime.strptime(long_month_name, "%B").month
    # year_number = datetime.datetime.strptime(year_name, "%Y").year
    # st.write(kdpdata['month'])

    # get last day of month for year_number, month_number
    thisyear = int(kdpdata['year'].iloc[0])
    month_number = int(kdpdata['month'].iloc[0])
    last_day_of_royalty_incurring_month = last_day_of_month(datetime.date(thisyear, month_number, 1))
    first_date, last_date = c.bounds['USD']
    first_date, last_date = c.bounds['GBP']
    kdpdata['exchangedate']: object = kdpdata['Royalty Date'].apply(lambda x: datetime.datetime.strptime(x, '%Y-%M'))
    # st.write(kdpdata['Currency'])
    # add column to kdpdata that calculates the last day of the month of "Royalty Date"
    kdpdata['lookuproyaltyratedate'] = kdpdata['Royalty Date'].apply(
        lambda x: last_day_of_month(datetime.datetime.strptime(x, '%Y-%m')))
    # calculate conversion to usd for each currency/lookuproyaltyratedate pair
    kdpdata['exchangerate_on_lookupdate'] = kdpdata.apply(
        lambda x: c.convert(1, x['Currency'], 'USD', x['lookuproyaltyratedate']), axis=1)
    # create column USDeq_Royalty for each exchangerate_on_lookupdate * Royalty
    kdpdata['USDeq_Royalty'] = kdpdata.apply(lambda x: x['exchangerate_on_lookupdate'] * x['Royalty'], axis=1)
    # calculate Net Units Sold
    kdpdata['Net_Units_Sold'] = kdpdata.apply(lambda x: x['Units Sold'] - x['Units Refunded'], axis=1)
    return kdpdata


@st.cache_data
def ingest_kdp_by_month(userdocs_kdpdata_path):
    FYI = st.empty()
    FYI.info('getting foreign exchange rates')
    filename = f"ecb_{date.today():%Y%m%d}.zip"
    print(filename)
    if not os.path.isfile(filename):
        print('retrieving', ECB_URL)
        urllib.request.urlretrieve(ECB_URL, filename)
    else:
        print('file already exists')
    c = CurrencyConverter(filename, fallback_on_wrong_date=True, fallback_on_missing_rate=True)
    print('loaded', filename)

    #  ingest_kdp initially supports only post-2015 format KDP data
    dkdp = pd.DataFrame()
    kdpdatatarget = userdocs_kdpdata_path + '/' + 'K*.xlsx'
    print('just before i loop')
    for i in glob.glob(kdpdatatarget):
        imessage = "ingesting KDP data file " + str(i)
        FYI.info(imessage)

        getdate = pd.read_excel(i, header=0, sheet_name='Total Royalty')
        # print(getdate)
        kdpdate = getdate.columns[1]
        # get month & date from file
        kdpdata = pd.read_excel(i, header=1, sheet_name='Total Royalty')

        kdpdata['month'] = kdpdate.split()[0]
        kdpdata['year'] = kdpdate.split()[1]
        long_month_name = kdpdate.split()[0]
        year_name = kdpdate.split()[1]
        month_number = datetime.datetime.strptime(long_month_name, "%B").month
        year_number = datetime.datetime.strptime(year_name, "%Y").year

        # get last day of month for year_number, month_number
        last_day_of_this_month = last_day_of_month(datetime.date(year_number, month_number, 1))

        first_date, last_date = c.bounds['USD']
        print('first_date', first_date, 'last_date', last_date)
        first_date, last_date = c.bounds['GBP']
        print('GBP first_date', first_date, 'last_date', last_date)
        exchangedate = datetime.datetime(year_number, month_number, last_day_of_this_month.day)
        kdpdata.insert(0, "Report Date", exchangedate)
        lookupdate = exchangedate.strftime('%F')

        print(lookupdate)
        cusd = 1.0
        try:
            cgbp = c.convert(1, 'GBP', 'USD', date=exchangedate)
        except Exception as e:
            st.error('error converting GBP to USD')
        cgbp = c.convert(1, 'GBP', 'USD', date=exchangedate)
        ceur = c.convert(1, 'EUR', 'USD', date=exchangedate)
        cjpy = c.convert(1, 'JPY', 'USD', date=exchangedate)
        caud = c.convert(1, 'AUD', 'USD', date=exchangedate)
        ccad = c.convert(1, 'CAD', 'USD', date=exchangedate)
        cbrl = c.convert(1, 'BRL', 'USD', date=exchangedate)
        cmxn = c.convert(1, 'MXN', 'USD', date=exchangedate)
        cinr = c.convert(1, 'INR', 'USD', date=exchangedate)

        conditions = [
            kdpdata['Currency'] == 'USD',
            kdpdata['Currency'] == 'GBP',
            kdpdata['Currency'] == 'EUR',
            kdpdata['Currency'] == 'JPY',
            kdpdata['Currency'] == 'AUD',
            kdpdata['Currency'] == 'CAD',
            kdpdata['Currency'] == 'BRL',
            kdpdata['Currency'] == 'MXN',
            kdpdata['Currency'] == 'INR']

        choices = [
            kdpdata['Royalty'] * cusd,
            kdpdata['Royalty'] * cgbp,
            kdpdata['Royalty'] * ceur,
            kdpdata['Royalty'] * cjpy,
            kdpdata['Royalty'] * caud,
            kdpdata['Royalty'] * ccad,
            kdpdata['Royalty'] * cbrl,
            kdpdata['Royalty'] * cmxn,
            kdpdata['Royalty'] * cinr
        ]

        kdpdata['USDeq_Royalty'] = np.select(conditions, choices, default=0)
        kdpdata['USDeq_Royalty'] = kdpdata['USDeq_Royalty'].round(2)

        kdpdata['Net Units Sold'] = kdpdata['Units Sold'] - kdpdata['Units Refunded']
        print(kdpdata['Net Units Sold'])

        dkdp = dkdp.append(kdpdata, ignore_index=True)

    dkdp.to_csv(userdocs_kdpdata_path + '/dkdp.csv')
    return dkdp


# def ingest_royaltied_author_info(lsi_export_df, filename):
#     royaltied_titles_df = pd.read_excel(filename)
#     rtdf = royaltied_titles_df
#     st.write('rtdf is', rtdf.shape) # 94, 77
#     st.write(rtdf)
#     df = lsi_export_df.copy()
#     for index, row in df.iterrows():
#
#         # get the isbn_13 of the current sales row
#         isbn_13 = row['isbn_13']
#         # get the metadata row matching isbn_13 of the current sales row
#         st.write('row', index, 'contains', row['isbn_13'])
#         st.write('rtdf row is', rtdf[rtdf['isbn_13'] == isbn_13])
#
#
#         try:
#             df.loc[index, 'royaltied_author_id'] = a.iat[0, 1]
#
#         except Exception as e:
#             b = 'no royaltied athor id in testdf for ' + isbn_13
#             df.loc[index, 'royaltied_author_id'] = 0
#             print('exception', e)
#     # returning sales row db with royalty author ids addedd
#     #st.write(df.head(10))
#     lsi_export_df = df.copy()
#     return lsi_export_df


# @st.cache_data

def clean_fme(fme):
    try:
        fme['isbn_10_bak'] = fme['ISBN'].apply(lambda x: to_isbn10(x) if len(str(x)) == 13 else x)
        fme['isbn_13'] = fme['ISBN'].apply(lambda x: to_isbn13(x) if len(str(x)) == 10 else x)
        # make ISBN13 into string
        fme['isbn_13'] = fme['isbn_13'].astype(str)
        fme['Ean'].astype(str).fillna('', inplace=True)
        fme["Pub Date"] = pd.to_datetime(fme["Pub Date"], format='%Y%d%m')
        fme["Pub Date"].astype(datetime, inplace=True)
    except Exception as e:
        errormessage = "could not convert ISBN10s to ISBN13" + str(e)
        st.error(errormessage)
        return
    return fme


@st.cache_data
def ingest_complementary_publisher_data(lsi_export_df, filename):
    try:
        complementary_df = pd.read_excel(filename, header=0)
    except Exception as e:
        st.error('could not open complementary metadata from Nimble')
        st.error(e)
        return
    for index, row in lsi_export_df.iterrows():
        isbn_13 = row['isbn_13']
        complementary_df['isbn_13'] = complementary_df['isbn_13'].astype(str)
        # add complementary values to lsi_export_df
        c1 = complementary_df.loc[complementary_df['isbn_13'] == isbn_13]

        if c1.empty:

            lsi_export_df.loc[index, 'product_line'] = 'unknown'
            lsi_export_df.loc[index, 'royaltied'] = 'unknown'
            lsi_export_df.loc[index, 'public_domain_work'] = 'unknown'
            lsi_export_df.loc[index, 'royaltied_author_id'] = 0
        else:
            # st.write('match for isbn_13', isbn_13)
            lsi_export_df.loc[index, 'product_line'] = c1['product_line'].values[0]
            lsi_export_df.loc[index, 'royaltied'] = c1['royaltied'].values[0]
            lsi_export_df.loc[index, 'public_domain_work'] = c1['public_domain_work'].values[0]
            lsi_export_df.loc[index, 'royaltied_author_id'] = c1['royaltied_author_id'].values[0]

    return lsi_export_df


def add_amazon_buy_links(df):
    df['amazon_buy_link'] = 'https://www.amazon.com/dp/' + df['isbn_10_bak'].astype(str) + '?tag=ai4bookloversgpt-20'
    return df


@st.cache_data
def ingest_direct_sales(userdocs_directsales_path):
    # print(userdocs_directsales_path)
    directtarget = userdocs_directsales_path + '/' + '2*.xls*'
    print(directtarget)
    directdf = pd.DataFrame()
    directdata = None
    for i in glob.glob(directtarget):
        print("trying to ingest direct sales file", i)
        try:
            directdata = pd.read_excel(i)
            print(directdata)
        except Exception as e:
            print('could not read direct sales file', i, e)
        directdf = pd.concat([directdf, directdata], ignore_index=True)

    directdf.to_excel(userdocs_directsales_path + '/alldirectsales.xlsx')
    return directdf


@st.cache_data
def ingest_gumroad(userdocs_path):
    gumroad = pd.DataFrame()
    gumroadtarget = userdocs_path + '/gumroad/Sales*.csv'
    for i in glob.glob(gumroadtarget):
        print(i)
        data = pd.read_csv(i)
        gumroad = gumroad.append(data, ignore_index=True)
    return gumroad


def convert_to_list_of_lists(df):
    df_list = df.values.tolist()
    df_list_of_lists = []
    for i in range(len(df_list)):
        if i == 0:
            df_list_of_lists.append([df_list[i][0], [df_list[i][1]]])
        elif df_list[i][0] == df_list[i - 1][0]:
            df_list_of_lists[-1][1].append(df_list[i][1])
        else:
            df_list_of_lists.append([df_list[i][0], [df_list[i][1]]])
    return df_list_of_lists


@st.cache_data
def create_royaltied_author_list_of_titles(filename='userdocs/37/leo_bloom_core/kdp_author_ids.xlsx'):
    userdocs_kdp_path = 'userdocs/37/leo_bloom_core/kdpdata/'
    df = pd.read_excel(filename, sheet_name='kdp_author_ids', dtype=str)
    royaltied_author_list_of_titles = convert_to_list_of_lists(df)
    with open(userdocs_kdp_path + 'authors.json', 'w') as f:
        json.dump(royaltied_author_list_of_titles, f)

    return royaltied_author_list_of_titles


@st.cache_data
def enhance_LSI_dataframe(df, lsi_full_export, cgbp):
    df['USDeq_pub_comp'] = np.where(df['reporting_currency_code'] == 'GBP', (df['YTD_pub_comp'] * cgbp).round(2),
                                    df['YTD_pub_comp'])

    # fills NA values with 0, but does not add missing rows

    df['YTD_net_quantity'] = df['YTD_net_quantity'].fillna(0.0).astype(int)
    df['isbn_13'] = df['isbn_13'].fillna(0).astype(int)
    df['YTD_net_quantity'].fillna(0.0).astype(int)
    df['YTD_pub_comp'].fillna(0.0).astype(int)
    df['USDeq_pub_comp'].fillna(0.0).astype(int)

    # rename lsi_full_export "ISBN" to isbn_13
    # lsi_full_export.rename(columns={'ISBN': 'isbn_13'}, inplace=True)
    df['title_x'] = df['title'].fillna('no title')
    # make isbn_13 column into string
    lsi_full_export['ISBN'] = lsi_full_export['ISBN'].astype(str)
    df[['isbn_13']] = df[['isbn_13']].astype(str)
    testdf = lsi_full_export[
        ['Title', 'ISBN', 'Pub Date', 'pub_age', 'lmip', 'product_line', 'royaltied', 'public_domain_work',
         'royaltied_author_id']].copy()

    # loop through the sales rows:
    for index, row in df.iterrows():
        # get the isbn_13 o the current sales row
        isbn_13 = row['isbn_13']
        # get the metadata row matching isbn_13 of the current sales row
        a = testdf.loc[testdf['ISBN'] == isbn_13]
        try:
            df.loc[index, 'Pub Date'] = a.iat[0, 2]
            df.loc[index, 'pub_age'] = a.iat[0, 3]
            df.loc[index, 'lmip'] = a.iat[0, 4]
            df.loc[index, 'product_line'] = a.iat[0, 5]
            df.loc[index, 'royaltied'] = a.iat[0, 6]
            df.loc[index, 'public_domain_work'] = a.iat[0, 7]
            df.loc[index, 'royaltied_author_id'] = a.iat[0, 8]
        except Exception as e:
            b = 'no pub date in testdf for ' + isbn_13
            df.loc[index, 'Pub Date'] = b
            print('exception', e)
    df['Pub Date'] = df['Pub Date'].astype(str)
    df['Pub Date'] = df['Pub Date'].str.split('T').str[0]  # truncates

    # move pub date, pub age, and lmip to the front of the dataframe
    # cols = df.columns.tolist()
    # cols = cols[-3:] + cols[:-3]
    # df = df[cols]

    pd.set_option('max_colwidth', 25)
    # df = set_column_value_formats(df)
    enhanced_df = df.copy()
    enhanced_df.to_csv(userdocs_lsidata_path + '/enhanced_df_from_enhance_lsi.csv')
    return enhanced_df


@st.cache_data
def enhance_KDP_dataframe(dkdp, BIPtruth_subset):
    netunits = dkdp.groupby(['Title'], as_index=False)[['Title', 'Net Units Sold']].sum().sort_values(
        by='Net Units Sold', ascending=False)

    #
    # add royaltied author ids to dkdp rows

    royaltied_titles_list = create_royaltied_author_list_of_titles()

    # loop over dkdp rows and add author id to row if isbn is in royaltied_titles_list
    for index, row in dkdp.iterrows():
        for author_id, isbn_list in royaltied_titles_list:
            # print(author_id, isbn_list)

            # print(row['ASIN/ISBN'])

            if row['ASIN/ISBN'] in isbn_list:
                dkdp.at[index, 'royaltied_author_id'] = author_id

    dkdp.to_csv(userdocs_path + '/results/dkdptest.csv')
    enhanced_dkdp = dkdp

    print(' ')
    print('KDP Report')
    print('most profitable KDP titles')

    print(dkdp.groupby('Title').sum().sort_values(by='USDeq_Royalty', ascending=False).head(10))
    topkdptitles = dkdp.groupby('Title').sum().sort_values(by='USDeq_Royalty', ascending=False).head(10)
    enhanced_dkdp.to_csv(userdocs_path + '/results/enhanced_dkdp.csv')
    return enhanced_dkdp, topkdptitles, netunits


@st.cache_data
def create_LTD_LSI_sales_dataframe(enhanced):
    LTD = enhanced.groupby(
        ['title_x', 'year', 'market', 'lmip', 'author', 'isbn_13', 'product_line', 'royaltied', 'public_domain_work',
         'royaltied_author_id', 'page_count', 'list_price'], as_index=False)[
        ['title_x', 'YTD_net_quantity', 'USDeq_pub_comp']].sum()
    LTD['monthly_avg_$'] = (LTD['USDeq_pub_comp'] / LTD['lmip']).round(2)
    LTD.to_excel(userdocs_path + '/results/LTD.xlsx')
    return LTD


@st.cache_data
def create_frontlist_dataframes(LTD, frontlist_window):
    frontlist = LTD[LTD['Months In Print'] < frontlist_window].sort_values(by='monthly_avg_$', ascending=False)
    frontlist.pop('monthly_avg_$')
    frontlist.insert(2, 'monthly_avg_$', frontlist['USDeq_pub_comp'] / frontlist['lmip'])

    frontlist['monthly_avg_$'] = frontlist['monthly_avg_$'].round(2)  #
    cols = frontlist.columns.tolist()
    # combine rows where isbn and market are equal and sum the net quantity and pub comp
    frontlist = frontlist.groupby(
        ['title_x', 'year', 'market', 'lmip', 'monthly_avg_$', 'author', 'isbn_13', 'product_line', 'royaltied',
         'public_domain_work', 'royaltied_author_id', 'page_count', 'list_price'], as_index=False)[
        ['title_x', 'YTD_net_quantity', 'USDeq_pub_comp']].sum()
    # for each row if isbn and market are equal,
    # create new rows for combined market & year
    # and delete the original rows
    for index, row in frontlist.iterrows():
        for index2, row2 in frontlist.iterrows():
            if row['isbn_13'] == row2['isbn_13'] and row['market'] == row2['market'] and row['year'] != row2['year']:
                frontlist.loc[index, 'YTD_net_quantity'] = row['YTD_net_quantity'] + row2['YTD_net_quantity']
                frontlist.loc[index, 'USDeq_pub_comp'] = row['USDeq_pub_comp'] + row2['USDeq_pub_comp']
                frontlist.loc[index, 'USDeq_pub_comp'] = frontlist.loc[index, 'USDeq_pub_comp'].round(2)
                frontlist.loc[index, 'market'] = row['market']
                frontlist.loc[index, 'title_x'] = row['title_x']
                frontlist.loc[index, 'lmip'] = row['lmip']
                frontlist.loc[index, 'monthly_avg_$'] = round(
                    (row['USDeq_pub_comp'] + row2['USDeq_pub_comp']) / row['lmip'], 2)
                frontlist.loc[index, 'monthly_avg_$'] = frontlist.loc[index, 'monthly_avg_$'].round(2)
                frontlist.loc[index, 'author'] = row['author']
                frontlist.loc[index, 'isbn_13'] = row['isbn_13']
                frontlist.loc[index, 'product_line'] = row['product_line']
                frontlist.loc[index, 'royaltied'] = row['royaltied']
                frontlist.loc[index, 'public_domain_work'] = row['public_domain_work']
                frontlist.loc[index, 'royaltied_author_id'] = row['royaltied_author_id']
                frontlist.loc[index, 'page_count'] = round(row['page_count'], 0)
                frontlist.loc[index, 'list_price'] = round(row['list_price'], 2)
                # list price with 2 deciimal places

                frontlist.drop(index2, inplace=True)
        # delete "year" column
    frontlist.pop('year')
    # move USDeq_pub_comp to after montnly average $
    cols = frontlist.columns.tolist()
    cols.insert(4, cols.pop(cols.index('USDeq_pub_comp')))
    frontlist = frontlist.reindex(columns=cols)

    # for each row if isbn is equal
    # create new row summing net quantity and pub comp
    # and delete the original rows
    frontlist_all_markets = frontlist.copy()
    #  move column 'lmip' to first position
    cols = frontlist_all_markets.columns.tolist()
    cols.insert(0, cols.pop(cols.index('lmip')))
    # st.write(cols)

    frontlist_all_markets = frontlist_all_markets.reindex(columns=cols)
    grouped = frontlist_all_markets.groupby(['isbn_13'], as_index=False).agg(
        {'lmip': 'first', 'YTD_net_quantity': 'sum', 'USDeq_pub_comp': 'sum', 'title_x': 'first',
         'monthly_avg_$': 'first', 'author': 'first', 'product_line': 'first', 'royaltied': 'first',
         'public_domain_work': 'first', 'royaltied_author_id': 'first', 'page_count': 'first', 'list_price': 'first'})

    grouped['market'] = 'All Markets'
    grouped['monthly_avg_$'] = grouped['USDeq_pub_comp'] / grouped['lmip']
    # st.write(grouped)
    frontlist_all_markets = grouped
    fam = frontlist_all_markets.copy()

    frontlist_number = len(frontlist_all_markets)
    winsorized = (fam['USDeq_pub_comp'] > fam['USDeq_pub_comp'].quantile(0.05)) & (
            fam['USDeq_pub_comp'] < fam['USDeq_pub_comp'].quantile(0.95))
    fam.to_excel(userdocs_path + '/results/frontlist.xlsx')
    frontlist_winsorized_mean = fam[winsorized]['monthly_avg_$'].mean()
    frontlist_median = fam['monthly_avg_$'].median()

    fwmean = fam[winsorized]['monthly_avg_$'].mean()
    fam.to_excel(userdocs_path + '/results/frontlist.xlsx')

    return frontlist, frontlist_number, winsorized, frontlist_winsorized_mean, fwmean, frontlist_median, frontlist_all_markets


@st.cache_data
def create_backlist_dataframes(LTD, deep_backlist_window):
    backlist = LTD[LTD['lmip'] > deep_backlist_window].sort_values(by='monthly_avg_$', ascending=False)
    backlist_number = (LTD[LTD['lmip'] > deep_backlist_window]).isbn_13.size
    backlist_winsorized = (backlist['USDeq_pub_comp'] > backlist['USDeq_pub_comp'].quantile(0.05)) & (
            backlist['USDeq_pub_comp'] < backlist['USDeq_pub_comp'].quantile(0.95))

    backlist_winsorized_mean = backlist[winsorized]['monthly_avg_$'].mean()

    print(backlist.describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95]))

    bwmean = backlist[winsorized]['monthly_avg_$'].mean()
    backlist.to_excel(userdocs_path + '/results/backlist.xlsx')
    return backlist, backlist_number, backlist_winsorized, backlist_winsorized_mean, bwmean


@st.cache_data
def create_product_lines_dataframe(LTD):
    productlines = LTD.groupby('product_line').sum().sort_values(by='monthly_avg_$', ascending=False)
    productlines.to_excel(userdocs_path + '/results/productlines.xlsx')
    return productlines


@st.cache_data
def create_by_years_dataframe(enhanced):
    pd.set_option('display.max_rows', 1000)
    pivotall = enhanced.pivot_table(index='title_x', columns='year', values='USDeq_pub_comp', aggfunc='sum',
                                    margins=True).sort_values(by='All', ascending=False).iloc[:, :-1]
    pivotall = pivotall.fillna(0.0)
    pivotall.to_excel(userdocs_path + '/results/pivotall.xlsx')
    # by years is inaccurate -- drops out nulls from series -- should b ecome 0s
    by_years = pivotall.apply(lambda x: pd.Series([e for e in x if pd.notnull(e)]), axis=1)
    by_years = by_years.drop(by_years.index[0])
    by_years.to_excel(userdocs_path + '/results/by_years.xlsx')
    by_years = pd.read_excel(userdocs_path + '/results/by_years.xlsx')
    pivotall.to_excel(userdocs_path + '/results/pivotall.xlsx')
    return by_years, pivotall


@st.cache_data
def remove_leap_days(datetime):
    df = pd.DataFrame({'Date': datetime})
    df['Date'] = df['Date'].apply(
        lambda x:
        x if x.month != 2 and x.date != 29
        else pd.datetime(x.year, x.month, 28)
    )
    return df['Date']


@st.cache_data
def create_public_domain_dataframe(enhanced, BIPtruth_subset):
    publicdomain = enhanced.pivot_table(index='product_id', columns='year', values='USDeq_pub_comp', aggfunc='sum',
                                        margins=True).sort_values(by='All', ascending=False)

    publicdomain = pd.merge(publicdomain, BIPtruth_subset, on='product_id', how='left')
    # filter rows with publicdomain = 0
    publicdomain = publicdomain[publicdomain['public_domain_work'] == 1]

    publicdomain['monthly_avg_$'] = (publicdomain['All'] / publicdomain['lmip']).round(2)
    publicdomain['annualized_avg_$'] = (publicdomain['All'] / publicdomain['lmip'] * 12).round(2)
    colz = ['title', 'All', 'lmip', 'public_domain_work', 'monthly_avg_$', 'annualized_avg_$']
    publicdomain[colz].sort_values(by='monthly_avg_$', ascending=False).to_excel(
        userdocs_path + '/results/publicdomain.xlsx')
    public_domain_analysis = publicdomain[colz].sort_values(by='monthly_avg_$', ascending=False)
    pdbyproductline = publicdomain.groupby('product_line').sum()

    return public_domain_analysis, pdbyproductline


@st.cache_data
def create_royaltied_title_analysis(enhanced, BIPtruth_subset):
    royaltied = enhanced.pivot_table(index='product_id', columns='year', values='USDeq_pub_comp', aggfunc='sum',
                                     margins=True).sort_values(by='All', ascending=False)
    royaltied = pd.merge(royaltied, BIPtruth_subset, on='product_id', how='left')
    # royaltied = royaltied[royaltied['royaltied'].fillna(False)]
    royaltied['monthly_avg_$'] = (royaltied['All'] / royaltied['lmip']).round(2)
    colz = ['title', 'All', 'lmip', 'royaltied', 'monthly_avg_$']
    royaltied[colz].sort_values(by='monthly_avg_$', ascending=False).to_excel(userdocs_path + '/results/royaltied.xlsx')
    royaltied.to_excel(userdocs_path + '/results/royaltied.xlsx')
    return royaltied


@st.cache_data
def calculate_and_report_royalties(year, enhanced, enhanced_dkdp, directdf=None):
    authordata = pd.read_excel(userdocs_path + '/authordata/royaltied_authors.xlsx')

    # get this year's sale data for each distributor
    yearLSIsales = enhanced[enhanced['year'].str.contains(year).fillna(False)]
    yearKDPsales = enhanced_dkdp[enhanced_dkdp['year'].str.contains(year).fillna(False)]  # has 61 records
    yearDirectsales = pd.DataFrame()
    if directdf is not None:
        directdf['year'] = directdf['year'].astype(str)
        yearDirectsales = pd.DataFrame(directdf[directdf['year'].str.contains(year).fillna(False)])
    yearLSIsales.to_csv(userdocs_path + '/results/' + year + '_LSI_sales.csv')
    yearKDPsales.to_csv(userdocs_path + '/results/' + year + '_KDP_sales.csv')
    yearDirectsales.to_csv(userdocs_path + '/results/' + year + '_direct_sales.csv')
    report_table = {}

    yearLSIcols = []
    yearKDPcols = []
    yearDirectcols = []
    directprofit = 0
    directdf_sales_rows = pd.DataFrame()

    # define columns for each distributor df

    yearLSIcols = ['year', 'YTD_net_quantity', 'USDeq_pub_comp', 'title_x', 'reporting_currency_code']  # product_id
    yearKDPcols = ['year', 'Net Units Sold', 'USDeq_Royalty', 'Title', 'ASIN/ISBN']
    yearDirectcols = ['year', 'YTD_net_quantity', 'USDeq_pub_comp', 'Title']

    for index, row in authordata.iterrows():  # looping over authors by id number
        # st.write('author id: ', row['royaltied_author_id'])
        # get rows by distributor that match author id
        a = row['royaltied_author_id']
        LSI_editions_sales = yearLSIsales[yearLSIsales['royaltied_author_id'] == a]
        # LSI_editions_sales.to_csv(userdocs_path + '/results/' + year + '_LSI_sales_' + str(row['royaltied_author_id']) + '.csv')

        LSIprofit = yearLSIsales[yearLSIsales['royaltied_author_id'] == row['royaltied_author_id']][yearLSIcols][
            'USDeq_pub_comp'].sum().round(2)

        # get all rows in yearKDPsales that contain the author's id number

        # KDP_sales_by_product_id = yearKDPsales[yearKDPsales['royaltied_author_id'] == str(row['royaltied_author_id'])][
        #     yearKDPcols]
        if directdf is not None:
            directdf_sales_rows = yearDirectsales[yearDirectsales['royaltied_author_id'] == row['royaltied_author_id']][
                yearDirectcols]
        print(directdf_sales_rows)
        # calculatenet revenue by distributor
        LSIprofit = yearLSIsales[yearLSIsales['royaltied_author_id'] == row['royaltied_author_id']][
            'USDeq_pub_comp'].sum().round(2)
        # KDPprofit = yearKDPsales[yearKDPsales['royaltied_author_id'] == str(row['royaltied_author_id'])][yearKDPcols][
        #     'USDeq_Royalty'].sum().round(2)
        KDPprofit = 10000
        if directdf is not None:
            directdf['net_revenue'] = directdf['USDeq_pub_comp'].sum().round(2)
            totalnetrevenue = (LSIprofit + KDPprofit + directdf['net_revenue']).round(2)
        else:
            totalnetrevenue = (LSIprofit + KDPprofit).round(2)

        royaltydue = (totalnetrevenue * .30).round(2)
        # address escalators in future

        totalnetrevenue = (LSIprofit + KDPprofit).round(2)
        royaltydue = (totalnetrevenue * .30).round(2)  # address escalators in future

        # append row to report_table

        if directdf is not None:

            report_table.update({'author_id': row['royaltied_author_id'], 'author_name': row['Real author full name'],
                                 'LSI_sales': LSIprofit, 'KDP_sales': KDPprofit,
                                 'direct_sales': directdf_sales_rows['YTD_net_quantity'], 'LSI_profit': LSIprofit,
                                 'KDP_profit': KDPprofit, 'direct sales profit': directprofit,
                                 'total_net_revenue': totalnetrevenue, 'royalty_due': royaltydue}, ignore_index=True)

        else:
            report_table.update({'author_id': row['royaltied_author_id'], 'author_name': row['Real author full name'],
                                 'LSI_sales': LSIprofit, 'KDP_sales': KDPprofit, 'LSI_profit': LSIprofit,
                                 'KDP_profit': KDPprofit, 'total_net_revenue': totalnetrevenue,
                                 'royalty_due': royaltydue}, ignore_index=True)

        # now prepare content for printing to file
        pd.options.display.width = 8
        pd.options.display.max_colwidth = 13

        if LSI_editions_sales.empty:
            LSI_message = 'No LSI sales for this author in ' + year + '.'
        else:
            LSI_message = (f"LSI sales in {year}:\n\n"
                           f"{LSI_editions_sales.to_string(index=False, max_colwidth=20, line_width=72)}\n\n")
            KDP_message = 'test '
        # if KDP_sales_by_product_id.empty:
        #     KDP_message = 'No KDP sales for this author in ' + year + '.'
        # else:
        #     KDP_message = (f"KDP sales in {year}: \n\n"
        #                    f" {KDP_sales_by_product_id.to_string(index=False, max_colwidth=20)}")
        if directdf is not None:
            direct_message = (f"Direct sales in {year}: \n\n"
                              f"{directdf_sales_rows.to_string(index=False, max_colwidth=20)}")
        else:
            direct_message = 'No direct sales for this author in ' + year + '.'

        multiline_string = (f"# Royalty Report - Nimble Books LLC\n"
                            f"{row['Real author full name']}\n\n"
                            f"{LSI_message}\n\n"
                            f"LSI net revenue in {year} to date: {LSIprofit}\n\n"
                            f"{KDP_message}\n\n"
                            f"KDP net revenue in {year}: {KDPprofit}\n\n"
                            f"{direct_message}\n\n"
                            f"Direct sales net revenue in {year}: {directprofit}\n\n"
                            f"Total net revenue in {year}: ${totalnetrevenue}\n\n"
                            f"Royalty due in {year}: ${royaltydue}\n\n"
                            f"\n\n\n\n")

        # printing report for this author

        with open(userdocs_path + '/royaltyreports/' + str(row['royaltied_author_id']) + str(row['Last name']) + '.md',
                  'w') as outfile:
            outfile.write(multiline_string)
    report_table_df = pd.DataFrame(report_table)

    report_table_df.to_csv(userdocs_path + '/results/' + 'all_royaltied_authors_for_' + year + '_royalty_report.csv')
    return yearKDPsales, yearLSIsales, authordata


@st.cache_data
def simplified_royalties_LSI(year, df):
    year = str(year)
    # st.write(year)
    # st.write(df.columns)
    dftargetfilepath = "resources/royalties/LSI/LSI_sales_" + year + ".csv"
    df['due2author'] = df['Net Compensation'] * 0.3

    simpleLSIsales = df[df['year'] == year]
    simpleLSIsales.to_csv("resources/royalties/LSI/LSI_sales_" + year + ".csv")
    # TODO merge with source of truth list of royaltied titles
    # TODO sort by Author
    # TODO prepare reports by Author
    return df


def read_LSI_comp_report_for_year(year):
    year = str(year)
    # Use StringIO to simulate a file-like object
    filepath = f"resources/royalties/LSI/compensation_reports/{year}.csv"
    st.write(filepath)
    # clean up =ISBN

    try:
        df = pd.read_csv(filepath, encoding='utf-16')
    except UnicodeDecodeError as e:
        # If UTF-16 also fails, we can try another common encoding like Latin-1
        try:
            df = pd.read_csv(filepath, encoding='latin1')
        except Exception as e:
            error_message = str(e)
        try:
            df = pd.read_csv(filepath, encoding='utf-8')
        except Exception as e:
            error_message = str(e)
    try:  # cleanup LSI peculiarities
        # for ISBN: strip = sign
        df['ISBN'] = df['ISBN'].str.strip('=')
        # remove quotes
        df['ISBN'] = df['ISBN'].str.replace('"', '')
    except Exception as e:
        error_message = str(e)
    df['year'] = year
    df.dropna(subset=['Net Compensation'], inplace=True)
    # drop index
    df.reset_index(drop=True, inplace=True)
    return df


@st.cache_data
def simplified_royalties_KDP(year, dkdp):
    dkdp['due2author'] = dkdp['USDeq_Royalty'] * 0.3
    dkdp['Report Date'] = pd.to_datetime(dkdp['Report Date'])
    simpleKDPsales = dkdp[dkdp['Report Date'].dt.year == year]
    simpleKDPsales.to_csv(userdocs_path + '/results/simpleKDPsales.csv')
    dkdp.to_csv(userdocs_path + '/results/dkdp_due2author.csv')
    return dkdp


@st.cache_data
def jumbo(page_limit, LTD):
    # if page count is string, convert to integer
    # Convert to pandas nullable integer type
    st.write(LTD['Page Count'].dtype)
    LTD['Page Count'] = pd.to_numeric(LTD['Page Count'], errors='coerce').astype('Int64')
    # st.stop()
    LTD['US List'] = pd.to_numeric(LTD['US List'], errors='coerce').astype(float)
    jumbodf = LTD[(LTD['Page Count'] >= page_limit) | (LTD['US List'] >= 99.00)]
    jumbotitles = jumbodf.groupby('Title').agg({
        'Net Compensation': 'sum',
        'Net Qty': 'sum',
        'Page Count': 'first'
    }).sort_values(by='Net Compensation', ascending=False)
    jumbotitles['superjumbo'] = np.where(jumbotitles['Page Count'] >= page_limit, 'yes', 'no')
    pd.options.display.max_colwidth = 32
    # jumbodf.to_excel(userdocs_path + '/results/jumbo.xlsx')
    return jumbodf


@st.cache_data
def slowhorses_from_last_three_years(LTD, thisyear, slowyearswindow, slowsalesthreshold):
    slowyearsstart = thisyear - slowyearswindow
    slowyearsend = thisyear
    # st.write(slowyearsstart, slowyearsend)
    slowyearslist = list(range(slowyearsstart, slowyearsend))
    strings = [str(x) for x in slowyearslist]

    # sloughhousedf = LTD.loc[ & (LTD['year'] == '2021')]
    sloughhousedf = LTD.loc[(LTD['Net Compensation'] <= slowsalesthreshold) & (LTD['year'].isin(strings))]  #
    # write sloughhousedf to csv
    # sloughhousedf.to_excel(userdocs_path + '/results/sloughhousedf.xlsx')

    # print(sloughhousedf.describe())
    return sloughhousedf, slowyearslist, slowsalesthreshold


def slowhorses_by_monthly_net_comp(LTD, slowsalesthreshold):
    sloughhousedf = LTD.loc[(LTD['Net Comp Per Month'] < slowsalesthreshold)]
    return sloughhousedf


@st.cache_data
def glue_factory(lsi_export_df, today, gluesalesthreshold=24, df=None):
    lsidf = lsi_export_df

    # select all transactions with year = 2020, 2021, and 2022 from df
    glueyearstransactions = df[df['year'].isin(['2021', '2022', '2023'])]
    # st.dataframe(glueyearstransactions)

    candidate_list = []
    renewal_list = []
    # create list of books renewing in next 60 days

    for index, row in lsidf.iterrows():

        pubdate = pd.to_datetime(row['Pub Date'], format='dayfirst')
        if pubdate.day == 29 and pubdate.month == 2:
            pubdate = pubdate.replace(day=28)
        # calculate next anniversary date from today
        next_anniversary = pubdate.replace(year=today.year)
        if next_anniversary < today:
            next_anniversary = next_anniversary.replace(year=today.year + 1)
        # calculate days until next anniversary
        days_until_next_anniversary = (next_anniversary - today).days

        if days_until_next_anniversary > 0 and days_until_next_anniversary < 60:
            if row['Status'] == 'Available for Printing/Download':
                if df is not None:

                    # glueyear sales for this title in USDEQ
                    glueyearsales = glueyearstransactions[glueyearstransactions['title_x'] == row['Title']]
                    totalglueyearsales = glueyearsales['USDeq_pub_comp'].sum()
                    if totalglueyearsales < gluesalesthreshold:
                        candidate = [row['Title'], row['isbn_13'], next_anniversary, totalglueyearsales]
                        candidate_list.append(candidate)
                    else:
                        renewme = [row['Title'], row['isbn_13'], next_anniversary, totalglueyearsales]
                        renewal_list.append(renewme)
        else:
            # candidate is safe
            pass

    # st.write(candidate_list)
    return candidate_list, renewal_list


@st.cache_data
def slowhorses_zero_sales(pivotall, thisyear, howfarback=3):
    zero_sales_df = pd.DataFrame()
    for year in range(thisyear - howfarback, thisyear):
        year = str(year)
        year_df = pivotall[(pivotall[year] == year) & (pivotall[year] == 0)]
        zero_sales_df = zero_sales_df.append(year_df)
    zero_sales_df.to_csv(userdocs_path + '/results/zero_sales_df.csv')

    return zero_sales_df


@st.cache_data
def create_payments_df(filename):
    payments_df = pd.read_excel(filename, sheet_name='Payments')
    return payments_df


@st.cache_data
def record_payments(filename, payments_df):
    # add inbound payments record to payments_df
    new_rows = pd.read_csv(filename)
    payments_df = pd.concat([payments_df, new_rows])
    payments_df.to_csv(userdocs_path + '/results/' + filename + '.csv')
    return payments_df


@st.cache_data
def dashboard(pivotall, dkdp, directdf, thisyear, annualizer, goal, mrr, winsorized_mean, frontlist):
    # st.write(pivotall, dkdp, directdf, thisyear, annualizer, goal, mrr, winsorized_mean, frontlist)

    LSI_YTD_rev = pivotall.iloc[0, -1].round()
    st.write("This year is ", thisyear)
    # KDP_YTD_rev = dkdp[dkdp['year'] == str(thisyear)]['USDeq_Royalty'].sum().round()
    include = directdf[directdf['Sale date'].dt.year == thisyear]
    direct_YTD_rev = include['USDeq_pub_comp'].sum().round()
    # KD#P_YTD_rev = simplified_royalties_KDP(thisyear, dkdp)
    # YTD_total_rev = (LSI_YTD_rev + KDP_YTD_rev + direct_YTD_rev).round()
    # annualized_rev = (YTD_total_rev * annualizer).round()
    # mrr = annualized_rev / 12
    # goal = goal
    # gap = goal - mrr
    # rint(gap, goal, mrr, winsorized_mean)
    # ap_titles_to_do = int(gap / winsorized_mean)
    # kdpdate = dkdp['Report Date'].max()
    # dict = {'LSI YTD revenue': LSI_YTD_rev, 'KDP YTD revenue': KDP_YTD_rev, 'direct YTD revenue': direct_YTD_rev,
    # 'YTD total revenue': YTD_total_rev, 'annualized revenue': annualized_rev}
    # dashboard_df = pd.DataFrame(dict, index=[0])

    # format columns in dashboard_df as integers with commas separating thousands
    # all_cols = list(dashboard_df)
    # dashboard_df[all_cols] = dashboard_df[all_cols].astype(float)
    # dashboard_df['kdpdate'] = kdpdate
    # # dashboard_df['LSI YTD revenue'] = dashboard_df['LSI YTD revenue'].map('${:,.0f}'.format)
    #
    # dashboard_df.to_excel(userdocs_path + '/results/dashboard_df.xlsx')

    wmean = frontlist_all_markets[winsorized]['monthly_avg_$'].mean()

    # st.write("Current MRR: ", f"${mrr:,.0f}")
    # st.write("Gap: ", f"${gap:,.0f}")
    st.write("YTD LSI DEq revenue: ", f"${LSI_YTD_rev:,.0f}")
    st.write("LSI projected revenue {year}: ", f"${LSI_YTD_rev * annualizer:,.0f}")

    # st.write("KDP projected revenue {year}: ", f"${thisyearKDPsales * annualizer:,.0f}")
    # st.write("YTD simple KDP revenue: ", f"${simpleKDPsales:,.0f}")
    st.write("YTD direct revenue: ", f"${direct_YTD_rev:,.0f}")
    # st.write("YTD total revenue:", f"${YTD_total_rev:,.0f}")
    # st.write("annualized revenue:", f"${annualized_rev:,.0f}")

    # st.write("unique ASINs with sales ever: ", dkdp['ASIN/ISBN'].nunique() + dkdp['ASIN/ISBN'].nunique())
    # st.write("Net KDP unit sales ever: ", dkdp['Net Units Sold'].sum().astype(int))

    st.write("new LSI titles in last twelve months: ", frontlist_number)
    st.write("total monthly contribution of all new LSI titles: ", frontlist['monthly_avg_$'].sum().round(2))

    # st.write('New mean revenue public domain titles needed until goal: ', gap_titles_to_do)
    # st.write("Winsorized mean revenue per public domain title")
    # st.write()
    return


# @st.cache_data
def cacheaware_file_upload_only(user_id, types=['csv']):
    uploaded_file = None
    try:
        uploaded_file = st.file_uploader(
            "Upload your document", type=types)

    except Exception as ex:
        st.write('## Trapped exception')
        st.error(str(ex))  # display error message
    return uploaded_file


def argparse_handler():
    parser = argparse.ArgumentParser()

    parser.add_argument("--user_id", help="user_id for command line runs", default='37')
    parser.add_argument("--year", help="single year scope for report", default="2023")
    parser.add_argument("--frontlist_window", help="number of months to look back for frontlist", default=18.0)
    parser.add_argument("--profiling", help="create Pandas profiles (time-consuming)", default=False)
    parser.add_argument("--make-plotly-plots", help="create plotly plots (time-consuming)", default=False)
    args = parser.parse_args()
    user_id = args.user_id
    year = args.year
    frontlist_window = args.frontlist_window
    profiling = args.profiling
    make_plotly_plots = args.make_plotly_plots
    # return all args
    return user_id, year, frontlist_window, profiling, make_plotly_plots


def create_userdocs_directories(user_id, userdocs_path):
    userdocs_working_docs_path = userdocs_path + '/' + 'working_docs'
    userdocs_results_path = userdocs_path + '/' + 'results'
    userdocs_authordata_path = userdocs_path + '/' + 'authordata'
    userdocs_lsidata_path = userdocs_path + '/' + 'lsidata'
    userdocs_kdpdata_path = userdocs_path + '/' + 'kdpdata'
    userdocs_directsales_path = userdocs_path + '/' + 'directsales'
    userdocs_royaltyreports_path = userdocs_path + '/' + 'royaltyreports'
    userdocs_resources_path = userdocs_path + '/' + 'resources'

    # check if directory path exists, if not create it
    if not os.path.exists(userdocs_path):
        os.makedirs(userdocs_path)
    if not os.path.exists(userdocs_working_docs_path):
        os.makedirs(userdocs_working_docs_path)
    if not os.path.exists(userdocs_results_path):
        os.makedirs(userdocs_results_path)
    if not os.path.exists(userdocs_authordata_path):
        os.makedirs(userdocs_authordata_path)
    if not os.path.exists(userdocs_lsidata_path):
        os.makedirs(userdocs_lsidata_path)
    if not os.path.exists(userdocs_kdpdata_path):
        os.makedirs(userdocs_kdpdata_path)
    if not os.path.exists(userdocs_directsales_path):
        os.makedirs(userdocs_directsales_path)
    if not os.path.exists(userdocs_royaltyreports_path):
        os.makedirs(userdocs_royaltyreports_path)
    if not os.path.exists(userdocs_resources_path):
        os.makedirs(userdocs_resources_path)

    return userdocs_working_docs_path, userdocs_results_path, userdocs_authordata_path, userdocs_lsidata_path, userdocs_kdpdata_path, userdocs_directsales_path, userdocs_royaltyreports_path


@st.cache
def presentation(publicdomain, sloughhousedf, howfarback=3):
    #
    # , zero_sales_df=None, howfarback=3):
    st.subheader("Public Domain Titles")
    st.dataframe(publicdomain)
    # st.dataframe(slowhorsesdf)

    buffer = io.StringIO()
    sloughhousedf.info(verbose=True, show_counts=True, buf=buffer)
    s = buffer.getvalue()
    st.text(s)
    # st.dataframe(slowhorsesdf)
    slowhorses_explo = "Titles earning less than " + str(slowsalesthreshold) + " USDeq in the years " + str(
        slowyearslist) + "."
    st.subheader("Slow Horses")
    st.write(slowhorses_explo)
    st.write(sloughhousedf.title_x.unique())
    zero_sales = f"Titles with zero sales in the previous {howfarback} years:"
    # st.write(zero_sales, (zero_sales_df.title_x.unique()))

    # zero_sales = f"Titles with zero sales in the previous {howfarback} years:"
    # st.write(zero_sales, (zero_sales_df.title_x.unique()))
    return


@st.cache
def make_plots(by_years):
    fig = px.violin(by_years, box=True, points='all')
    st.plotly_chart(fig)
    df = by_years
    # fig = subplots.make_subplots(rows=30, cols=10, subplot_titles='test')
    st.write(df.head(5))
    # df = by_years.head(5)
    titles = df.index.to_list()
    st.write(titles)
    columns = df.columns.to_list()
    # create violin plot for each title in df
    for title in titles:
        fig = px.bar(df.loc[title], x=columns, y=title, title=df.loc[title].index[0])
        target_save_file_name = 'output/plotly/' + make_basename_safe(str(title)) + '.png'
        FYI.info(f'{target_save_file_name}')
        fig.write_image(f'{target_save_file_name}', format='png', width=800, height=600)

        fig2 = px.violin(df.loc[title], x=columns, y=title, title=df.loc[title].index[0])
        target_save_file_name = 'output/plotly/' + make_basename_safe(str(title)) + '_violin.png'
        fig2.write_image(f'{target_save_file_name}', format='png', width=800, height=600)

        data = df.loc[title]
        fig3 = px.funnel(data, x=columns, y=title, title=df.loc[title].index[0])
        target_save_file_name = 'output/plotly/' + make_basename_safe(str(title)) + '_funnel.png'
        fig3.write_image(f'{target_save_file_name}', format='png', width=800, height=600)


def simple_royalties_LSI(years_requested=[2022]):
    biptruth_df = read_and_clean_biptruth_df()
    sr_by_year = []
    for y in years_requested:
        print(f"Processing {y} sales for royalties")
        df = read_LSI_comp_report_for_year(y)
        # st.write(df)
        sr = simplified_royalties_LSI(y, df=df)
        for index, row in biptruth_df.iterrows():
            if row['ISBN'] in sr['ISBN'].values:
                sr.loc[sr['ISBN'] == row['ISBN'], 'public_domain_work'] = row['public_domain_work']
                sr.loc[sr['ISBN'] == row['ISBN'], 'product_line'] = row['product_line']
            else:
                # add row
                row_df = row.to_frame().transpose()
                sr = pd.concat([sr, row_df])

            # st.write(sr.columns)
        # fill rows where Gross Qty is NaN as 0
        sr['Gross Qty'].fillna(0, inplace=True)
        sr['public_domain_work'].fillna(True, inplace=True)
        sr = sr[sr['public_domain_work'].astype(bool) == False]

        sr['royaltied'].fillna(True, inplace=True)
        sr = sr[sr['royaltied'].astype(bool) == True]
        sr_by_year.append(sr)
    return sr_by_year


def read_and_clean_biptruth_df():
    global biptruth_df
    biptruth_df = pd.read_csv('resources/sources_of_truth/BIPtruth.csv', dtype={'ISBN': str})
    biptruth_df['ISBN'] = biptruth_df['ISBN'].astype(str)
    biptruth_df['public_domain_work'] = biptruth_df['public_domain_work'].astype(bool)
    return biptruth_df
