#  Copyright (c) 2024. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com
"""
This class creates financial reporting objects to be shared by the leo_bloom_core library.
Priorities are:
- accuracy
- modularity
- reusability

Begin with the following objects:
Lifetime Paid Compensation Received from LSI
Estimated Unpaid Compensation Owed by LSI
Full Metadata Export from LSI

New objects:
 Merge Lifetime Paid and Estimatedd Unpaid Compensation Owed by LSI
 Merge Full Metadata Export with Merged Compensation on ISBN

"""
import logging
import sys
import traceback

import numpy as np
import pandas as pd
import streamlit as st
from isbnlib import to_isbn10

from Codexes2Gemini.classes.Codexes.CodexPeopleRoles.LeoBloom.leo_bloom_core.FinancialReportingObjects_utilities import \
    add_amazon_buy_links
from Codexes2Gemini.classes.Codexes.CodexPeopleRoles.LeoBloom.leo_bloom_core.FinancialReportingObjects_utilities import \
    load_spreadsheet
from Codexes2Gemini.classes.Utilities.utilities import configure_logger


# Next: create all_unit_sales as UnitSalesThroughToday

class FinancialReportingObjects:
    def __init__(self, root="~/.codexes2gemini"):
        # initialize FRO with default file values
        # they can be overridden when creating specific objects
        try:
            # TODO - create test data files
            self.LSI_LTD_paid_file_path = f"{root}/resources/data_tables/LSI/LSI_LTD_paid_comp.csv"
            self.LSI_unpaid_file_path = f"{root}/resources/data_tables/LSI/LSI_estimated_unpaid_comp.xlsx"

            self.fme_file_path = f"{root}/resources/data_tables/LSI/Full_Metadata_Export.xlsx"
            self.add2fme_file_path = f"{root}/resources/sources_of_truth/add2fme.xlsx"
            logging.info(f"Created LTD, unpaid, combined, FME objects")
            self.lsi_royalties_due_file_path = f"{root}/resources/data_tables/LSI/LSI_royalties_due.csv"
            self.LSI_year_data_file_path = f"{root}/resources/data_tables/LSI/2023LSIComp.xlsx"
            self.actual_payment_history_file_path = f"{root}/resources/sources_of_truth/payments2authors/actual_payments_partial.xlsx"
            self.ThisMonthUnitSales_file_path = f"{root}/resources/data_tables/LSI/ThisMonthUnitSales.xlsx"
            self.dataframe = pd.DataFrame
            # duplicate column "

        except Exception as e:
            logging.error(f"Could not create all the FROs")
            logging.error(f"{e}")
            st.error(f"{e}")

    # for help debugging
    def identify_mixed_type_columns(df):
        mixed_type_columns = []
        for col in df.columns:
            num_of_data_types = len(df[col].apply(type).unique())
            if num_of_data_types > 1:
                mixed_type_columns.append(col)
                print(f"{col}: {df[col].apply(type).unique()}")
        return mixed_type_columns


class LifetimePaidCompensation(FinancialReportingObjects):
    def __init__(self, parent_instance, file_path=None):

        if file_path is None:
            file_path = parent_instance.LSI_LTD_paid_file_path
        self.LSI_LTD_paid_file_path = file_path
        self.data = load_spreadsheet(self.LSI_LTD_paid_file_path)
        self.LSI_LTD_paid_df = self.data.astype(
            {"ISBN": str, "Title": str, "Author": str, "Format": str, "Gross Qty": int, "Returned Qty": int,
             "Net Qty": int, "Net Compensation": float, "Sales Market": str})
        self.is_LTD_paid_df_valid_shape(self.LSI_LTD_paid_df)
        if self.is_LTD_paid_df_valid_shape(self.LSI_LTD_paid_df):
            self.dataframe = self.LSI_LTD_paid_df
        else:
            raise Exception("dataframe creation error")

    def is_LTD_paid_df_valid_shape(self, LSI_LTD_paid_df):
        number_columns = len(LSI_LTD_paid_df.columns)
        number_rows = len(LSI_LTD_paid_df.index)
        if number_columns != 9 or number_rows < 629:
            raise ValueError("Invalid shape of lifetime paid compensation object.")
        return True


class EstimatedUnpaidCompensation(FinancialReportingObjects):
    def __init__(self, parent_instance, file_path=None):
        super().__init__()
        if file_path is None:
            file_path = parent_instance.LSI_unpaid_file_path
        self.LSI_unpaid_file_path = file_path
        self.data = load_spreadsheet(self.LSI_unpaid_file_path)
        self.LSI_unpaid_df = self.data.astype(
            {"ISBN": str, "Title": str, "Author": str, "Format": str, "Gross Qty": int, "Returned Qty": int,
             "Net Qty": int, "Net Compensation": float, "Sales Market": str})
        self.is_LSI_unpaid_df_valid_shape(self.LSI_unpaid_df)
        if self.is_LSI_unpaid_df_valid_shape(self.LSI_unpaid_df):
            self.dataframe = self.LSI_unpaid_df
        else:
            raise Exception("dataframe creation error")

    def is_LSI_unpaid_df_valid_shape(self, LSI_unpaid_df):
        return LSI_unpaid_df.shape[1] == 9


class LSI_LTD_Paid_And_Unpaid_Compensation(FinancialReportingObjects):
    def __init__(self, parent_instance, LSI_LTD_paid_file_path=None, LSI_unpaid_file_path=None):
        super().__init__()
        self.ltd_paid_df = LifetimePaidCompensation(parent_instance, LSI_LTD_paid_file_path).dataframe
        self.unpaid_df = EstimatedUnpaidCompensation(parent_instance, LSI_unpaid_file_path).dataframe
        # get len paid rows
        self.len_paid_rows = len(self.ltd_paid_df)
        # concatenate the dfs
        self.LSI_paid_and_unpaid_df = pd.concat([self.ltd_paid_df, self.unpaid_df])
        self.LSI_pup_rows = len(self.LSI_paid_and_unpaid_df)
        self.LSI_pup_columns = len(self.LSI_paid_and_unpaid_df.columns)
        self.is_LSI_paid_and_unpaid_df_valid_shape(self.len_paid_rows, self.LSI_pup_rows, self.LSI_pup_columns)
        self.dataframe = self.LSI_paid_and_unpaid_df

    def is_LSI_paid_and_unpaid_df_valid_shape(self, paid_rows, pup_rows, pup_columns):
        if pup_columns != 9 or pup_rows < paid_rows:
            raise ValueError("Invalid shape of combined dataframesf")
        return True

    def set_dtypes_for_LSI_LTD_Paid_And_Unpaid(self):
        self.dataframe = self.groupby('ISBN').agg({
            'Title': 'first',
            'Author': 'first',
            'Format': 'first',
            'Gross Qty': 'sum',
            'Returned Qty': 'sum',
            'Net Qty': 'sum',
            'Net Compensation': 'sum',
            'Sales Market': 'first'
        }).reset_index()
        self.dataframe = self.dataframe.sort_values(by='Net Compensation', ascending=False, na_position='last')
        return self


class ThisMonthUnitSales(FinancialReportingObjects):
    def __init__(self, parent_instance, file_path=None):
        super().__init__()
        if file_path is None:
            file_path = parent_instance.ThisMonthUnitSales_file_path
            self.data = load_spreadsheet(file_path)
        else:
            self.data = load_spreadsheet(file_path)
        self.columns = ["Title", "Author", "Format", "ISBN", "Units Sold"]
        self.dataframe = self.data.astype(
            {"ISBN": str, "Title": str, "Author": str, "Format": str, "Units Sold": int})
        # rename Units Sold to This Month Units Sold
        self.dataframe["This Month Units Sold"] = self.dataframe["Units Sold"].astype(int)


class AllUnitSalesThruToday(FinancialReportingObjects):
    def __init__(self, parent_instance, file_path=None):
        super().__init__(parent_instance)
        self.lsi_ltd_units = LSI_LTD_Paid_And_Unpaid_Compensation(parent_instance, file_path).dataframe
        self.this_month_unit_sales = ThisMonthUnitSales(parent_instance, file_path).dataframe
        self.full_metadata_enhanced = FullMetadataEnhanced(parent_instance).dataframe
        self.df_with_unit_sales = self.modify_ThisMonthsUnitSales(self.full_metadata_enhanced, self.lsi_ltd_units,
                                                                  self.this_month_unit_sales)
        self.df_coerced = self.coerce_mixed_type_columns(self.df_with_unit_sales)
        self.dataframe = self.df_with_unit_sales
        self.autosave_path = "resources/data_tables/LSI/autosaves/all_unit_sales_thru_today.xlsx"
        try:
            self.dataframe.to_excel(self.autosave_path)
            self.autosave_success = True
        except Exception as e:
            self.autosave_success = False
            logging.error(f"Autosave of class AUS failed: {e}")

    def coerce_mixed_type_columns(self, df):
        for col in df.columns:
            majority_type = df[col].map(type).mode()[0]
            if majority_type == int:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(np.int64)
            elif majority_type == float:
                df[col] = df[col].astype(float, errors='ignore')
            elif majority_type == str:
                df[col] = df[col].astype(str)
            else:
                print(f"Datatype {majority_type} not handled")

        return df

    def get_units_sold_from_lsi_ltd(self, lsi_ltd_units):
        # get columns that contain quantity info
        cols = ["ISBN", "LTD Net Qty"]
        df = lsi_ltd_units[cols]
        return df

    def modify_ThisMonthsUnitSales(self, full_metadata_enhanced, lsi_ltd_units, this_month_unit_sales):
        fme_copy = full_metadata_enhanced.drop_duplicates(subset=['ISBN']).copy()
        fme_copy = fme_copy.sort_values(by='ISBN', ascending=True, na_position='first').copy()
        # Add column Units Sold from tmus
        tmus = this_month_unit_sales.drop_duplicates(subset=['ISBN']).copy()
        lsi_ltd_units = lsi_ltd_units.drop_duplicates(subset=['ISBN']).copy()
        # tmus['ISBN'] = tmus['ISBN'].fillna(0).astype(str)
        fme_copy['ISBN'] = fme_copy['ISBN'].astype(str)
        fme_copy = fme_copy.merge(tmus[['ISBN', 'This Month Units Sold']], on='ISBN', how='left')
        fme_copy = fme_copy.merge(lsi_ltd_units, on='ISBN', how='left')
        # st.write(fme_copy.columns)

        fme_copy.fillna({"LTD Net Qty": 0}, inplace=True)
        fme_copy.fillna({'This Month Units Sold': 0}, inplace=True)
        fme_copy["Through Today Net New Qty"] = fme_copy["LTD Net Qty"] + fme_copy["This Month Units Sold"]
        fme_copy['months_in_print'] = (pd.to_datetime('today') - fme_copy[
            'Pub Date']).dt.days / 30.44  # Approximate days per month
        fme_copy['months_in_print'] = fme_copy['months_in_print'].round(2)  # Round to two decimal places
        fme_copy['Annualized Net Qty'] = (
                    (fme_copy['Through Today Net New Qty'] / fme_copy['months_in_print']) * 12).round(2)
        fme_copy = fme_copy.sort_values(by='Pub Date', ascending=False, na_position='last')
        return fme_copy

    def crosscheck_unit_sale_totals(self):
        # st.write(f"LSI paid {LSIpaid.lsi_ltd_paid_units}")
        #         # st.write(f"AUSdf net qty {ausdf['Net Qty'].sum()}")
        #         # st.write(f"AUSdf Net New Qty {ausdf['Net New Qty'].sum()}")
        return True

    def show_frontlist_only(fme_copy):
        '''
        filter out all pub dates >= 18 months ago
        '''
        fme_copy = fme_copy[fme_copy['months_in_print'] <= 18]
        return fme_copy

    def hide_forthcoming(fme_copy):
        fme_copy = fme_copy[fme_copy['months_in_print'] > 0]
        return fme_copy

    def show_middle_backlist_only(fme_copy):
        '''
        months in print > 18 and less than 60
        '''
        fme_copy = fme_copy[(fme_copy['months_in_print'] >= 18) & (fme_copy['months_in_print'] <= 60)]
        return fme_copy

    def show_deep_backlist_only(fme_copy):
        '''
        mip > 60 months
        '''
        fme_copy = fme_copy[fme_copy['months_in_print'] > 60]
        return fme_copy

    def show_all_backlist_only(fme_copy):
        fme_copy = fme_copy[fme_copy['months_in_print'] >= 18]
        return fme_copy

    def hide_royaltied(fme_copy):
        # if royaltied is false
        fme_copy = fme_copy[~fme_copy['royaltied']]
        return fme_copy


class FullMetadataIngest(FinancialReportingObjects):
    def __init__(self, parent_instance, fme_file_path=None):
        super().__init__()
        if fme_file_path is None:
            self.fme_file_path = parent_instance.fme_file_path
        self.dataframe = load_spreadsheet(self.fme_file_path)

        # check validity of fme
        if self.dataframe.shape[1] < 100:
            raise ValueError("Invalid shape of Full Metadata Export dataframe.")
        if self.dataframe.shape[0] < 1:
            raise ValueError("FME has no rows")
        fme = self.dataframe
        try:
            # logging.info(fme.shape)
            fme['isbn_10_bak'] = fme['ISBN'].apply(lambda x: to_isbn10(x) if len(str(x)) == 13 else x)
            fme['Ean'].fillna(0, inplace=True)
            fme['Ean'] = fme['Ean'].astype(int)
            fme['Ean'] = fme['Ean'].astype(str).replace(',', '')
            # #logging.info(fme.head())
            fme["Pub Date"] = pd.to_datetime(fme["Pub Date"])
            # add Net Qty and Net Compensation from through_latest_month matching on ISBN

            fme_with_buy_links = add_amazon_buy_links(fme)
            fme_with_buy_links.to_excel("resources/data_tables/LSI/Nimble_Books_Catalog.xlsx")
            # fme_with_buy_links.to_excel('resources/data_tables/LSI/Nimble_Books_Catalog.xlsx')
            self.dataframe_with_buy_links = fme_with_buy_links
        except Exception as e:
            st.error(e)
        self.dataframe = fme


class Add2FME(FinancialReportingObjects):
    '''
    proprietary or analytic data from Nimble Books to add to the FME by matching on ISBN
    '''

    def __init__(self, parent_instance, file_path=None):
        super().__init__(parent_instance)
        if file_path is None:
            self.file_path = parent_instance.add2fme_file_path
        self.dataframe = load_spreadsheet(self.file_path)


class FullMetadataEnhanced:
    INVALID_SHAPE_ERROR = "Invalid shape of Full Metadata Export dataframe."
    NO_ROWS_ERROR = "FME has no rows"

    def __init__(self, parent_instance, fme_file_path=None, add2fme_file_path=None):
        self.full_metadata_export = FullMetadataIngest(parent_instance, fme_file_path)
        self.add2fme = Add2FME(parent_instance, add2fme_file_path)
        self.lsi_ltd_paid_df = LSI_LTD_Paid_And_Unpaid_Compensation(parent_instance).dataframe
        self.dataframe = self.merge_data_frames()

    def merge_data_frames(self):
        fme_df = self.full_metadata_export.dataframe_with_buy_links
        add2fme_df = self.add2fme.dataframe
        lsi_ltd_paid_df = self.lsi_ltd_paid_df
        enhanced_df = fme_df.merge(add2fme_df[['ISBN', 'royaltied']], on='ISBN', how='left')
        enhanced_df = enhanced_df.merge(
            lsi_ltd_paid_df[['ISBN', 'Gross Qty', 'Returned Qty', 'Net Qty', 'Net Compensation']], on='ISBN',
            how='left')
        enhanced_df['royaltied'] = enhanced_df['royaltied'].fillna(False).astype('bool')
        # copy Net Qty to LTD Net Qty
        enhanced_df["LTD Net Qty"] = enhanced_df["Net Qty"]
        return enhanced_df


class SlowHorses(FinancialReportingObjects):
    # must add all unit sales
    def __init__(self, parent_instance):
        # lifetime net qty <=5
        self.dataframe = AllUnitSalesThruToday(parent_instance).dataframe
        # slow horses are titles with less than 10 lifetime sales
        self.slow_horses = self.dataframe[(self.dataframe['Net New Qty'] <= 5) & (self.df['Net New Qty'] > 0)]
        self.glue_factory = self.dataframe[self.dataframe['Net New Qty'] == 0]


class LSI_Year_Data(FinancialReportingObjects):

    def __init__(self, parent_instance, file_path=None):
        if file_path is None:
            file_path = parent_instance.LSI_year_data_file_path
        self.LSI_year_data_file_path = '/Users/fred/.codexes2gemini/resources/data_tables/LSI/2023LSIComp.xlsx'
        self.dataframe = load_spreadsheet(self.LSI_year_data_file_path)
        self.LSI_year_data_df = self.dataframe.astype(
            {"ISBN": str, "Title": str, "Author": str, "Format": str, "Gross Qty": int, "Returned Qty": int,
             "Net Qty": int, "Net Compensation": float, "Sales Market": str})
        # self.is_LSI_year_data_df_valid_shape(self.LSI_year_data_df)


class LSI_Years_Data(FinancialReportingObjects):

    def __init__(self, parent_instance, years=[2022, 2023], file_path=None):
        super().__init__()
        self.years_dict = dict(zip(years, years))
        self.LSI_years_requested = years

    def add_default_years(self, years_dict=None, root=''):
        if years_dict is None:
            years_dict = {
                "2022": f"{root}/resources/data_tables/LSI/2022LSIcomp.xlsx",
                "2023": f"{root}/resources/data_tables/LSI/2023LSIComp.xlsx"
            }
        self.LSI_years_dict.update(years_dict)

    def add_to_dictionary(self, key, value):
        self.LSI_years_dict[key] = value


class LSI_Royalties_Due(FinancialReportingObjects):

    # TODO must add lsi_year_data_file_path
    def __init__(self, parent_instance, year=2024, lsi_royalties_due_file_path=None):
        super().__init__()
        if lsi_royalties_due_file_path is not None:
            self.lsi_royalties_due_file_path = lsi_royalties_due_file_path
            try:
                self.dataframe = load_spreadsheet(self.lsi_royalties_due_file_path)
            except Exception as e:
                st.error("Could not load lsi_royalties_due file.")
                st.error(f"{e}")
                logging.error(f"Could not load lsi_royalties_due file: {e}")
                st.write(traceback.print_exc())
        else:
            # if could not load royalties file, create a new blank dataframe
            self.lsi_royalties_due_file_path = parent_instance.lsi_royalties_due_file_path
            self.dataframe = pd.DataFrame()
        # st.write(self.dataframe)
        # replace commas in numbers of ISBN column with nothing
        # self.dataframe["ISBN"] = self.dataframe["ISBN"].astype(str)
        thisyear_royalty_df = self.dataframe
        self.royalties_df_dict = {f"royalties_due_{year}": thisyear_royalty_df}

    def is_LSI_royalty_df_valid(self):
        # check validity of LSI Royalties Due
        if self.dataframe.shape[1] < 100:
            raise ValueError("Invalid shape of LSI Royalties Due dataframe.")
        if self.dataframe.shape[0] < 1:
            raise ValueError("LSI Royalties Due has no rows")

    def create_LSI_royalties_df(self, ltd_enhanced_df, fme, year):
        self.thisyear_royalty_df = ltd_enhanced_df.merge(fme[['ISBN', 'Pub Date', 'royaltied']], on='ISBN', how='left')

        thisyear_royalty_df = self.thisyear_royalty_df

        # Changed Pub Date to dtype datetime
        thisyear_royalty_df['Pub Date'] = pd.to_datetime(thisyear_royalty_df['Pub Date'], format='mixed',
                                                         errors='coerce')

        # add royaltied flag from add2fme

        thisyear_royalty_df = thisyear_royalty_df[thisyear_royalty_df['royaltied'] == True]
        thisyear_royalty_df["due2author"] = thisyear_royalty_df['Net Compensation'] * 0.3

        return thisyear_royalty_df

    def create_due2authors_df(self, year, thisyear_royalty_df):

        self.thisyear_due2authors_df = thisyear_royalty_df.groupby('Author')['due2author'].sum()

        # Sorted due2author in descending order
        self.thisyear_due2authors_df.sort_values(by='due2author', ascending=False, na_position='last')
        # add blank columns
        self.thisyear_due2authors_df  # thisyear_due2authors_df [['paid_amt', 'paid_date', 'paid_mode', 'paid_notes']] = None

        return self.thisyear_due2authors_df


class Actual_Payment_History(FinancialReportingObjects):

    def __init__(self, parent_instance, actual_payment_history_file_path=None):
        if actual_payment_history_file_path is None:
            actual_payment_history_file_path = parent_instance.actual_payment_history_file_path
            try:
                self.dataframe = load_spreadsheet(actual_payment_history_file_path)
            except Exception as e:
                st.error("Could not load actual payment history file.")
                st.error(f"{e}")
                logging.error(f"Could not load actual payment history file: {e}")
                st.write(traceback.print_exc())


def main(port=1455, themebase="light"):
    sys.argv = ["streamlit", "run", __file__, f"--server.port={port}", f'--theme.base={themebase}',
                f'--server.maxUploadSize=40']
    import streamlit.web.cli as stcli
    stcli.main()
    configure_logger("INFO")


if __name__ == '__main__':
    FRO = FinancialReportingObjects()
    ltd = FRO.LifetimePaidCompensation("resources/data_tables/LSI/LSI_LTD_paid_comp.xlsx")
    est = FRO.EstimatedUnpaidCompensation("resources/data_tables/LSI/LSI_estimated_unpaid_comp.csv")
    payment_object = FRO.LTD_Paid_And_Unpaid_Compensation(ltd, est)
    df3 = payment_object.create_LSI_LTD_paid_and_unpaid_comp()
    print(df3)
    metadata_object = FRO.FullMetadataExport(
        "/Users/fred/bookpublishergpt/resources/data_tables/LSI/Full_Metadata_Export.csv")
    fme = metadata_object.create_fme()
    print(fme)
