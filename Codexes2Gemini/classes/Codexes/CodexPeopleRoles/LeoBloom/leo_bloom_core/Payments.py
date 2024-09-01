# Python
# Purpose: This file contains the class that handles payment tracking for leo_bloom_core
import pandas as pd
import streamlit as st


class Payments:
    def __init__(self, payments_df):
        self.payments_df = payments_df

    def ingest_payments_from_csv(filename, payments_df):
        # add inbound payments record to payments_df
        new_rows = pd.read_csv(filename)
        try:
            payments_df = pd.concat([payments_df, new_rows])
            payments_df.to_csv(userdocs_path
                               + '/results/'
                               + filename
                               + '.csv')
        except Exception as e:
            st.error(e)
        return payments_df

    def ingest_payments_from_Paypal_csv(self, paypal_filename):
        ppdf = pd.read_csv(paypal_filename)
        # march names in rows to royaltied author dict

        return ppdf

    def ingest_payments_from_Stripe_csv(self, stripe_filename):
        stripedf = pd.read_csv(stripe_filename)
        # match mname in ingest data to nanme in royaltied df
        return stripedf

    def ingest_payments_from_Wise_csv(self, wise_filename):
        wisedf = pd.read_csv(wise_filename)
        # match mname in ingest data to nanme in royaltied df
        return wisedf

    def ingest_payments_from_Stripe_API(self, stripeinfo):
        return stripeAPIdf

    def get_payments(self):
        return self.payments_df

    def get_payments_by_date(self, date):
        return self.payments_df[self.payments_df['Date'] == date]

    def get_payments_by_date_range(self, start_date, end_date):
        return self.payments_df[(self.payments_df['Date'] >= start_date) & (self.payments_df['Date'] <= end_date)]

    def make_payments(self, payments_df):
        makepaydf = payments_df[
            'royaltied_author_id', 'payment_method', 'payment_address', 'due2author', 'payment_currency_code']
        # read list of payments & coordinates
        if makepaydf['payment_method'] == 'PayPal':
            # PayPal API fx
            pass
        return
# we begin with manual ingest of payments info contained in spreadsheets
