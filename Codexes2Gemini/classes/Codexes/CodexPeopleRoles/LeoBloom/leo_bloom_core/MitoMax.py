# Import the necessary modules
import traceback

import pandas as pd
import streamlit as st
from app.utilities.utilities import load_spreadsheet
# from app.utilities.leo_bloom_core.leo_bloom_core import product_line, glueresults
from classes.Masthead.LeoBloom.LeoBloom import CurrencyConverter, add_amazon_buy_links, ingest_direct_sales, \
    argparse_handler, create_userdocs_directories, create_date_variables
from isbnlib import to_isbn10
from mitosheet.streamlit.v1 import spreadsheet

# from app.utilities.make_basename_safe import make_basename_safe


user_id, year, frontlist_window, profiling, make_plotly_plots = argparse_handler()
deep_backlist_window = 60  # months
if 'user_id' in locals():
    user_id = 37  # current_user.id
else:
    user_id = user_id
    print('running from main using cli-specified user id', user_id)
# check if directory a/b/c/ exists, if not create it
userdocs_path = 'userdocs/' + str(user_id) + '/leo_bloom_core'
userdocs_working_docs_path, userdocs_results_path, userdocs_authordata_path, userdocs_lsidata_path, userdocs_kdpdata_path, userdocs_directsales_path, userdocs_royaltyreports_path = create_userdocs_directories(
    user_id, userdocs_path)

# begin calculations

today, thisyear, starting_day_of_current_year, daysYTD, annualizer, this_year_month = create_date_variables()
st.write('today is', today, 'this year is', thisyear, 'starting day of current year is', starting_day_of_current_year)

topbar = st.columns([3, 7])
topbar[0].image('resources/images/Max_Bialystock_-_Edited.png')
topbar[1].write(" **Max Bialystok: Financial Analysis Software for Book Publishers**")
topbar[1].markdown("""
- Ingests royalty data from KDP, Ingram, and publisher direct sales
- Analyzes profitability by frontlist, backlist, product line, style, and more")
- Calculates and reports royalty rates and royalties earned
- Visualizations for all categories and for each title
""")
FYI = st.empty()
st.caption(
    "The inspired lunacy of Zero Mostel as Max Bialystok in the classic movie THE PRODUCERS. (Wikipedia)")

FYI.info(f'Running MaxBialystokfor user {user_id} on {today}.')
##sleep(1)  # Notification area
c = CurrencyConverter()
cgbp = c.convert(1, 'USD', 'GBP')
exchange_message = f"1 USD = {cgbp} GBP"
FYI.info(exchange_message)

tab1, tab2 = st.tabs(["Analysis", "Royalties"])

with tab1:
    with st.expander("LSI compensation", expanded=True):
        try:
            ltd = pd.read_excel('resources/data_tables/LSI/ltd.xlsx', dtype={'Title': str, 'ISBN': str})
            # st.write(ltd)
            FYI.info('loaded LSI LTD')
        except Exception as e:
            st.error(e)
            st.stop()

        ltdraw = ltd
        try:
            Accrued = pd.read_excel('resources/data_tables/LSI/unpaid_comp.xlsx', dtype={'Title': str, 'ISBN': str})
            FYI.info('loaded unpaid comp for most recent 90+ days')
            # st.write(unpaid_comp)

        except Exception as e:
            st.error(f"Could not load unpaid compensation file: {e}")
            st.stop()

        try:
            this_month_sales = pd.read_excel('resources/data_tables/LSI/this_month_sales.xlsx')
            FYI.info("loaded this month's unit sales")
        except Exception as e:
            st.error("could not load unit sales")
            st.stop()

        try:
            fme = load_spreadsheet("resources/data_tables/LSI/fme.csv")
            # st.write(fme.head())

            fme['isbn_10_bak'] = fme['ISBN'].apply(lambda x: to_isbn10(x) if len(str(x)) == 13 else x)
            fme['Ean'].fillna(0, inplace=True)
            fme['Ean'] = fme['Ean'].astype(int)
            fme['Ean'] = fme['Ean'].astype(str).replace(',', '')
            # st.write(fme.head())
            fme["Pub Date"] = pd.to_datetime(fme["Pub Date"])

            fme_with_buy_links = add_amazon_buy_links(fme)
            fme_with_buy_links.to_excel("resources/data_tables/LSI/Nimble_Books_Catalog.xlsx")
            # fme_with_buy_links.to_excel('resources/data_tables/LSI/Nimble_Books_Catalog.xlsx')

        except Exception as e:
            st.error(e)
            # st.stop()

        try:
            add2fme = pd.read_excel('resources/sources_of_truth/add2fme.xlsx')
        except Exception as e:
            errormsg = traceback.print_exc()
            st.error(errormsg)
            st.stop()

        # add column 'royaltied' to fme from add2fme by matching on ISBN
        fme = fme.merge(add2fme[['ISBN', 'royaltied']], on='ISBN', how='left')
        fme['royaltied'] = fme['royaltied'].fillna(False).astype('bool')

        LTD_raw = ltdraw

        # combine all rows by isbn
        LTD_raw = LTD_raw.groupby('ISBN').agg({
            'Title': 'first',
            'Author': 'first',
            'Format': 'first',
            'Gross Qty': 'sum',
            'Returned Qty': 'sum',
            'Net Qty': 'sum',
            'Net Compensation': 'sum',
            'Sales Market': 'first'
        }).reset_index()

        # Sorted Net Compensation in descending order
        LTD_raw = LTD_raw.sort_values(by='Net Compensation', ascending=False, na_position='last')

        # Duplicated LTD_raw
        LTD_combined_ISBN = LTD_raw.copy(deep=True)

        # add Pub Date column from FME by matching on ISBN
        LTD_combined_ISBN = LTD_combined_ISBN.merge(fme[['ISBN', 'Pub Date', 'royaltied']], on='ISBN', how='left')

        # Changed Pub Date to dtype datetime
        LTD_combined_ISBN['Pub Date'] = pd.to_datetime(LTD_combined_ISBN['Pub Date'], format='mixed', errors='coerce')

        # Sorted Pub Date in descending order
        LTD_combined_ISBN = LTD_combined_ISBN.sort_values(by='Pub Date', ascending=False, na_position='last')

        LTD_combined_ISBN['avg_net_comp'] = LTD_combined_ISBN['Net Compensation'] / LTD_combined_ISBN['Net Qty']

        # in Accrued, combine ISBNs and sum Net Compensation column only
        series = Accrued.groupby('ISBN')['Net Compensation'].sum()
        df5 = pd.DataFrame(series, index=series.index)

        # In Accrued, combine rows into unique ISBNs. concatenate strings separated by "; ".  sum integer columns.
        Accrued = Accrued.groupby('ISBN').agg(
            {'Title': '; '.join, 'Author': '; '.join, 'Format': '; '.join, 'Gross Qty': 'sum', 'Returned Qty': 'sum',
             'Net Qty': 'sum', 'Net Compensation': 'sum', 'Sales Market': '; '.join}).reset_index()
        #
        # Sorted Net Compensation in descending order
        Accrued = Accrued.sort_values(by='Net Compensation', ascending=False, na_position='last')
        #
        # In Title, Author, and Format fields, convert strings separated by ";" into list.
        Accrued['Title'] = Accrued['Title'].apply(lambda x: x.split('; '))
        Accrued['Author'] = Accrued['Author'].apply(lambda x: x.split('; '))
        Accrued['Format'] = Accrued['Format'].apply(lambda x: x.split('; '))
        #
        # In the Title, Author, and Format fields in Accrued, delete duplicate items in lists.
        Accrued['Title'] = Accrued['Title'].apply(lambda x: list(set(x)))
        Accrued['Author'] = Accrued['Author'].apply(lambda x: list(set(x)))
        Accrued['Format'] = Accrued['Format'].apply(lambda x: list(set(x)))
        #
        # In Accrued, add a column with Pub Date by matching on ISBN from FME.
        Accrued = Accrued.merge(fme[['ISBN', 'Pub Date', 'royaltied']], on='ISBN', how='left')
        #
        # # Sorted Pub Date in descending order
        # Accrued = Accrued.sort_values(by='Pub Date', ascending=False, na_position='last')

        # merge LTD combined ISBN and this_month_sales on matching ISBNs
        # just merge one column, "avg_net_comp"
        this_month_sales = this_month_sales.astype(str)
        LTD_combined_ISBN = LTD_combined_ISBN.astype(str)

        this_month_sales = this_month_sales.merge(LTD_combined_ISBN[['ISBN', 'avg_net_comp']], on='ISBN', how='left')

        # for rows with NaN, make avg_net_comp = 7.00.
        this_month_sales['avg_net_comp'].fillna(7.00, inplace=True)

        # # Deleted columns Title_y, Author_y, Format_y, Gross Qty, Returned Qty, Pub Date_y, Net Qty, Net Compensation, Sales Market
        # this_month_sales.drop(['Title_y', 'Author_y', 'Format_y', 'Gross Qty', 'Returned Qty', 'Pub Date_y', 'Net Qty',
        #                        'Net Compensation', 'Sales Market'], axis=1, inplace=True)

        # calculate "estimated_comp" by multiplying "Units Sold" by "avg_net_comp"
        this_month_sales['estimated_comp'] = this_month_sales['Units Sold'].astype(int) * this_month_sales[
            'avg_net_comp']

        thru_most_recent_end_of_month = pd.concat([LTD_combined_ISBN, Accrued], join='inner', ignore_index=True)

        LSI2022 = pd.read_excel("resources/data_tables/LSI/2022LSIcomp.xlsx")
        LSI2023 = pd.read_excel("resources/data_tables/LSI/2023LSIComp.xlsx")
        LSI2022["ISBN"] = LSI2022["ISBN"].astype(str)
        LSI2023["ISBN"] = LSI2023["ISBN"].astype(str)

        LSI2022enhanced = LSI2022.copy(deep=True)

        # add Pub Date column from FME by matching on ISBN
        LSI2022enhanced = LSI2022enhanced.merge(fme[['ISBN', 'Pub Date', 'royaltied']], on='ISBN', how='left')

        # Changed Pub Date to dtype datetime
        LSI2022enhanced['Pub Date'] = pd.to_datetime(LSI2022enhanced['Pub Date'], format='mixed', errors='coerce')

        LSI2023enhanced = LSI2023.copy(deep=True)

        # add Pub Date column from FME by matching on ISBN
        LSI2023enhanced = LSI2023enhanced.merge(fme[['ISBN', 'Pub Date', 'royaltied']], on='ISBN', how='left')

        # Changed Pub Date to dtype datetime
        LSI2023enhanced['Pub Date'] = pd.to_datetime(LSI2023enhanced['Pub Date'], format='mixed', errors='coerce')

        # add royaltied flag from add2fme

        LSIroyalties2023 = LSI2023enhanced[LSI2023enhanced['royaltied'] == True]
        LSIroyalties2023["due2author"] = LSIroyalties2023['Net Compensation'] * 0.3

        LSI_due2authors = LSIroyalties2023.groupby('Author')['due2author'].sum()
        LSI_due2authors_df = pd.DataFrame(LSI_due2authors, index=series.index)

        # Sorted due2author in descending order
        LSI_due2authors_df.sort_values(by='due2author', ascending=False, na_position='last')
        # add blank columns
        # LSI_due2authors_df[['paid_amt', 'paid_date', 'paid_mode', 'paid_notes']] = None

        dfs, code = spreadsheet(LTD_combined_ISBN, ltdraw, fme, Accrued, this_month_sales,
                                thru_most_recent_end_of_month, LSI2022enhanced, LSI2023enhanced, LSIroyalties2023,
                                LSI_due2authors_df,
                                df_names=['LTD by Pub Date', 'LTD_raw', 'fme', 'Accrued', 'this_month_sales',
                                          'thru_most_recent_end_of_month', 'LSI2022', 'LSI2023', 'LSIroyalties2023',
                                          'LSI_due2authors'],
                                key='ltd_lsi_expander', import_folder="resources/data_tables/LSI")
        st.code(code)

    try:
        copy_directdf = ingest_direct_sales(userdocs_directsales_path)
        FYI.info("read direct sales data files")
    except Exception as e:
        st.error('error while ingesting direct sales data files')
        st.error(e)

        with st.expander("Upload LSI data files", expanded=False):
            with st.form(key='LSIupload'):
                st.info(
                    "Upload LSI files")
                destination = st.selectbox("Destination", ["YTD", "LYTD", "LTD", "ThisMonth"])
                uploaded_file = st.file_uploader("Upload a file ",
                                                 type=['xlsx', 'csv', 'xls'])
                st.form_submit_button(label='Upload')
                if uploaded_file is None:
                    st.warning(
                        "If you do not upload a file, Max will use the hard-coded system defaults and local data tables.")
                else:
                    # move uploaded file to working directory
                    file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type,
                                    "FileSize": uploaded_file.size}
                    st.info(file_details)
                    destination_name_file = {destination: file_details}

    with st.expander("Kindle Direct Publishing", expanded=False):
        kdp_ltd_df = pd.read_excel("resources/data_tables/KDP/KDPltd.xlsx", sheet_name="Combined Sales")
        kdp2023_df = pd.read_excel("resources/data_tables/KDP/kdp2023.xlsx", sheet_name="Combined Sales")
        kdp_titles_with_sales = pd.read_excel("resources/data_tables/KDP/KDP_titles_with_sales.xlsx",
                                              sheet_name="Combined Sales")
        # get all rows with unique ASIN/ISBNs
        unique_df = kdp_titles_with_sales.drop_duplicates(subset=['ASIN/ISBN'], keep='last')
        kdp_royalties = pd.read_excel("resources/data_tables/KDP/KDP_2023_royalty_calculations.xlsx")

        dfs, code = spreadsheet(kdp_ltd_df, kdp2023_df, unique_df, kdp_royalties,
                                df_names=["KDP LTD", "KDP 2023", "KDP titles", "KDP royalties"])
        st.code(code)

    with st.expander("Substack", expanded=False):
        col4, col5 = st.columns(2)
        substack_df = pd.read_csv('resources/data_tables/substack_revenues.csv')
        substack_df['Year'] = pd.to_datetime(substack_df['Year'], format='%Y')
        # display df['Year'] as year only
        substack_df['Year'] = substack_df['Year'].dt.strftime('%Y')
        substack_monthly_gross_revenue = (substack_df['Annualized Gross Revenue'].sum() / 12).round(2)
        substack_df = col4.data_editor(substack_df, num_rows="dynamic")
        col5.caption(f'Monthly Gross Revenue: {substack_monthly_gross_revenue}')
        submit = st.button("Save Substack Data")
        if submit:
            substack_df.to_csv('resources/data/substack_revenues.csv', index=False)
            FYI.info('Substack data saved')

with tab2:
    with st.expander("Integrated Payments Due to Authors"):
        LSIroyalties2023.to_csv("resources/royalties/LSI/LSIroyalties2023.csv")
        kdp_royalties.to_csv("resources/royalties/KDP/KDProyalties2023.csv")
        author_info = pd.read_excel("resources/sources_of_truth/ActiveNimbleAuthors.xlsx")
        adjusted_author_info = pd.read_csv("resources/royalties/Combined/adjusted_due2authors.csv")

        # Group the data by ASIN/ISBN, Marketplace, Title, and Author Name, then aggregate relevant metrics
        detailed_summary_df = kdp_royalties.groupby(['ASIN/ISBN', 'Marketplace', 'Title', 'Author Name']).agg(
            Total_Units_Sold=pd.NamedAgg(column='Units Sold', aggfunc='sum'),
            Total_Units_Refunded=pd.NamedAgg(column='Units Refunded', aggfunc='sum'),
            Total_Net_Units_Sold=pd.NamedAgg(column='Net Units Sold', aggfunc='sum'),
            Total_Royalty=pd.NamedAgg(column='Royalty', aggfunc='sum')
        ).reset_index()

        dkdf = detailed_summary_df
        dkdf.to_csv('resources/royalties/Combined/ddf.csv')

        dfs, code = spreadsheet(LSIroyalties2023, kdp_royalties, author_info, adjusted_author_info, dkdf,
                                df_names=["LSI_due2authors", "KDP_due2authors", "Author Info", "Due to Authors",
                                          "Detailed Summary"])

    with st.expander("Payments Data and Reporting"):
        st.markdown("**History**")
