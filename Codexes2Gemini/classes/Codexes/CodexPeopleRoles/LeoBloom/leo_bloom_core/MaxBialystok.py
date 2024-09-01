# Import the necessary modules
import pandas as pd
import streamlit as st
# from app.utilities.leo_bloom_core.leo_bloom_core import product_line, glueresults
from classes.Masthead.LeoBloom import LeoBloom as Leo
from dateutil.relativedelta import relativedelta
from mitosheet.streamlit.v1 import spreadsheet

# from app.utilities.make_basename_safe import make_basename_safe
st.set_page_config(layout="wide")

user_id, year, frontlist_window, profiling, make_plotly_plots = Leo.argparse_handler()
deep_backlist_window = 60  # months
if 'user_id' in locals():
    user_id = 37  # current_user.id
else:
    user_id = user_id
    print('running from main using cli-specified user id', user_id)
# check if directory a/b/c/ exists, if not create it
userdocs_path = 'userdocs/' + str(user_id) + '/leo_bloom_core'
userdocs_working_docs_path, userdocs_results_path, userdocs_authordata_path, userdocs_lsidata_path, userdocs_kdpdata_path, userdocs_directsales_path, userdocs_royaltyreports_path = Leo.create_userdocs_directories(
    user_id, userdocs_path)

# begin calculations

today, thisyear, starting_day_of_current_year, daysYTD, annualizer, this_year_month = Leo.create_date_variables()
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
c = Leo.CurrencyConverter()
cgbp = c.convert(1, 'USD', 'GBP')
exchange_message = f"1 USD = {cgbp} GBP"
FYI.info(exchange_message)

tab1, tab2 = st.tabs(["Analysis", "Royalties"])

with tab1:
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
            fme = Leo.load_and_clean_fme('resources/data_tables/LSI/Full_Metadata_Export.xlsx')
            fme_cleaned = fme
            fme_with_buy_links = Leo.add_amazon_buy_links(fme)
            fme_labs = fme_with_buy_links[fme_with_buy_links['Series Name'] == 'AI Lab for Book-Lovers']
            fme_with_buy_links.to_csv('resources/data_tables/LSI/Full_Metadata_Export_with_buy_links.csv', index=False)
            fme_labs = fme_with_buy_links[fme_with_buy_links['Series Name'] == 'AI Lab for Book-Lovers']
            fme_labs.to_csv('resources/data_tables/LSI/fme_labs.csv', index=False)
        except Exception as e:
            st.error('error while loading and cleaning FME')
            st.stop()
        FYI.info('saved FME with amazon buy links to resources/data_tables/LSI/Full_Metadata_Export_with_buy_links.csv')
        LTD = Leo.ingest_and_enhance_lsi_ltd_comp(ltd, fme)

        LTD['Pub Date'] = pd.to_datetime(LTD['Pub Date'], format='%Y-%m-%d', errors='coerce')
        LTD = LTD.sort_values(by='Pub Date', ascending=False)
        LTD_columns = [col for col in LTD.columns if col != 'Net Compensation']
        LTD_columns.insert(5, 'Net Compensation')
        LTD = LTD[LTD_columns]

        # Reordered column Net Qty
        LTD_columns = [col for col in LTD.columns if col != 'Net Qty']
        LTD_columns.insert(4, 'Net Qty')
        LTD = LTD[LTD_columns]

        # Reordered column US List
        LTD_columns = [col for col in LTD.columns if col != 'US List']
        LTD_columns.insert(3, 'US List')
        LTD = LTD[LTD_columns]
        ltd_median_net_comp_per_month = LTD['Net Comp Per Month'].median().round(2)
        ltd_average_net_comp_per_month = LTD['Net Comp Per Month'].mean().round(2)
        median_earnings_over_a_decade = ltd_median_net_comp_per_month * 120

        LSI2022 = pd.read_excel("resources/data_tables/LSI/2022LSIcomp.xlsx")
        LSI2023 = pd.read_excel("resources/data_tables/LSI/2023LSIComp.xlsx")
        # enhance with public domain, product line columns
        biptruth_df = Leo.read_and_clean_biptruth_df()
        for index, row in biptruth_df.iterrows():
            if row['ISBN'] in LTD['ISBN'].values:
                LTD.loc[LTD['ISBN'] == row['ISBN'], 'public_domain_work'] = row['public_domain_work']
                LTD.loc[LTD['ISBN'] == row['ISBN'], 'product_line'] = row['product_line']
            else:
                # add row
                row_df = row.to_frame().transpose()
                LTD = pd.concat([LTD, row_df])
        # Sorted Pub Date in descending order
        LTD = LTD.sort_values(by='Pub Date', ascending=False, na_position='last')
        LTD['public_domain_work'] = LTD['public_domain_work'].astype(bool)
        LTD_with_public_domain = LTD
        frontlist_window = 18
        frontlist_origin = today - relativedelta(months=frontlist_window)
        frontlist = LTD[LTD['Pub Date'] > frontlist_origin]
        frontlist_median_net_compenstation_per_month = frontlist['Net Comp Per Month'].median().round(2)
        frontlist_average_net_compenstation_per_month = frontlist['Net Comp Per Month'].mean().round(2)
        deep_frontlist_window = 60
        deep_frontlist_origin = today - relativedelta(months=deep_frontlist_window)
        deep_frontlist = LTD[LTD['Pub Date'] > deep_frontlist_origin]
        deep_backlist = LTD[LTD['Pub Date'] < deep_frontlist_origin]
        public_domain = LTD[LTD['public_domain_work'] == True]
        public_domain_median_net_comp_per_month = public_domain['Net Comp Per Month'].median().round(2)
        public_domain_median_net_comp_per_month = public_domain['Net Comp Per Month'].median().round(2)
        public_domain_average_net_comp_per_month = public_domain['Net Comp Per Month'].mean().round(2)
        public_domain_frontlist = public_domain[public_domain['Pub Date'] > frontlist_origin]
        public_domain_deep_frontlist = public_domain[public_domain['Pub Date'] > deep_frontlist_origin]
        public_domain_deep_backlist = public_domain[public_domain['Pub Date'] < deep_frontlist_origin]
        public_domain_frontlist_median_net_comp_per_month = public_domain_frontlist[
            'Net Comp Per Month'].median().round(2)
        public_domain_frontlist_average_net_comp_per_month = public_domain_frontlist['Net Comp Per Month'].mean().round(
            2)
        public_domain_deep_frontlist_median_net_comp_per_month = public_domain_deep_frontlist[
            'Net Comp Per Month'].median().round(2)
        public_domain_deep_frontlist_average_net_comp_per_month = public_domain_deep_frontlist[
            'Net Comp Per Month'].mean().round(2)
        public_domain_deep_backlist_median_net_comp_per_month = public_domain_deep_backlist[
            'Net Comp Per Month'].median().round(2)
        public_domain_deep_backlist_average_net_comp_per_month = public_domain_deep_backlist[
            'Net Comp Per Month'].mean().round(2)
        public_domain_frontlist_net_comp = public_domain_frontlist['Net Compensation'].mean().round(2)
        public_domain_LTD_mean = public_domain['Net Compensation'].mean().round(2)
        public_domain_LTD_median = public_domain['Net Compensation'].median().round(2)

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric(label="Frontlist PD median net comp per month",
                    value=public_domain_frontlist_median_net_comp_per_month)
        col2.metric(label="Frontlist PD mean net comp per month",
                    value=public_domain_frontlist_average_net_comp_per_month)
        col3.metric(label="Frontlist PD net comp to date", value=public_domain_frontlist_net_comp)
        col5.metric(label="PD LTD mean net comp", value=public_domain_LTD_mean)
        col4.metric(label="PD LTD median net comp", value=public_domain_LTD_median)
        LSI_royalties = Leo.simple_royalties_LSI(years_requested=[2022])
        roy1 = LSI_royalties[0]

        # Enhance Accrued in the same way as LTD
        biptruth_df = Leo.read_and_clean_biptruth_df()
        for index, row in biptruth_df.iterrows():
            if row['ISBN'] in Accrued['ISBN'].values:
                Accrued.loc[Accrued['ISBN'] == row['ISBN'], 'public_domain_work'] = row['public_domain_work']
                Accrued.loc[Accrued['ISBN'] == row['ISBN'], 'product_line'] = row['product_line']

            else:
                row_df = row.to_frame().transpose()
                Accrued = pd.concat([Accrued, row_df])
        Accrued['Net Qty'] = Accrued['Net Qty'].fillna(0).astype('int')
        Accrued['public_domain_work'] = Accrued['public_domain_work'].astype(bool)
        Accrued = Accrued.merge(LTD[['ISBN', 'Pub Date', 'Months in Print']], on='ISBN', how='left')

        Accrued_columns = [col for col in Accrued.columns if col != 'Pub Date']
        Accrued_columns.insert(3, 'Pub Date')
        Accrued = Accrued[Accrued_columns]

        # Reordered column Months in Print
        Accrued_columns = [col for col in Accrued.columns if col != 'Months in Print']
        Accrued_columns.insert(4, 'Months in Print')

        Accrued = Accrued.groupby('ISBN').agg({
            'Title': 'first',
            'Net Qty': 'sum',
            'Net Compensation': 'sum',
            'Pub Date': 'first',
            'Months in Print': 'first',
            'public_domain_work': 'first',
            'product_line': 'first',
            # Add other columns as needed
        }).reset_index()

        if 'Months in Print' in Accrued.columns:
            merged_df = pd.merge(fme[['ISBN', 'Pub Date']],
                                 Accrued[['ISBN', 'Net Qty', 'Net Compensation', 'Months in Print']],
                                 on='ISBN', how='left')
        else:
            print("Column 'Months in Print' not found in the Accrued DataFrame")

        # add column "Title" from Full ... to merged df matching on ISBN
        merged_df = pd.merge(merged_df, fme[['ISBN', 'Title']], on='ISBN', how='left')

        # Filtered Net Compensation
        merged_df = merged_df[merged_df['Net Compensation'].notnull()]

        # Changed Pub Date to dtype datetime
        merged_df['Pub Date'] = pd.to_datetime(merged_df['Pub Date'], format='mixed', errors='coerce')

        merged_df['Months in Print'] = ((pd.to_datetime('today') - merged_df['Pub Date']).dt.days / 30).round(2)
        # st.write(f"days_to_print {(eom - ltd_comp['Pub Date']).dt.days}")

        merged_df['Net Comp Per Month'] = (merged_df['Net Compensation'] / merged_df['Months in Print'])

        # Sorted Pub Date in descending order
        merged_df = merged_df.sort_values(by='Pub Date', ascending=False, na_position='last')

        merged_df['Net Qty'] = merged_df['Net Qty'].fillna(0).astype('int')
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
        LTD_combined_ISBN = LTD_combined_ISBN.merge(fme[['ISBN', 'Pub Date']], on='ISBN', how='left')

        # Changed Pub Date to dtype datetime
        LTD_combined_ISBN['Pub Date'] = pd.to_datetime(LTD_combined_ISBN['Pub Date'], format='mixed', errors='coerce')

        # Sorted Pub Date in descending order
        LTD_combined_ISBN = LTD_combined_ISBN.sort_values(by='Pub Date', ascending=False, na_position='last')

        dfs, code = spreadsheet(LTD_combined_ISBN, ltdraw, fme_cleaned, LTD, Accrued, frontlist, deep_frontlist,
                                deep_backlist,
                                public_domain, roy1, merged_df, LSI2022, LSI2023,
                                df_names=['LTD by Pub Date', 'LTD_raw', 'FME', 'LTD', 'Accrued', 'Frontlist',
                                          'Deep Frontlist',
                                          'Deep Backlist',
                                          'Public Domain',
                                          'Royalty 2022', 'Merged'],
                                key='ltd_lsi_expander', import_folder="resources/data_tables/LSI")
        st.code(code)

    try:
        copy_directdf = Leo.ingest_direct_sales(userdocs_directsales_path)
        FYI.info("read direct sales data files")
    except Exception as e:
        st.error('error while ingesting direct sales data files')
        st.error(e)

    try:
        sloughhousedf = Leo.slowhorses_by_monthly_net_comp(LTD, 2.0)
        FYI.info('slow horses calculated')
    except Exception as e:
        st.error("Error calculating slow horses")
        st.write(e)

    months_so_far_this_year = Leo.months_so_far_this_year(thisyear)

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

    with st.expander("Jumbos", expanded=False):
        jumbodf = Leo.jumbo(680, LTD)
        FYI.info('jumbo dataframes created')
        st.caption("Jumbos are books of more than 680 pages or list price $99 or higher")
        Jumbos_copy = jumbodf.copy(deep=True)
        Jumbos_copy = Jumbos_copy[Jumbos_copy['public_domain_work'] == True]
        # get median and mean of Net Compensation column
        pd_jumbos_median_net_comp = Jumbos_copy['Net Compensation'].median
with tab2:
    with st.expander("Payments Data and Reporting"):
        st.markdown("**History**")
        payments_df = pd.read_csv("resources/sources_of_truth/payments2authors/payments_lifetime.csv")
        payments_df = st.data_editor(payments_df, key="payments", num_rows="dynamic")
        button = st.button("Update Payments History")
        if button:
            payments_df.to_csv("resources/sources_of_truth/payments2authors/payments_lifetime.csv")
            st.info(f"Updated payments_df")
            st.write(st.session_state["payments"])
