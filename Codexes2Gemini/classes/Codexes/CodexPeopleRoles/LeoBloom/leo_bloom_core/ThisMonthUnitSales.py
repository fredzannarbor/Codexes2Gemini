import numpy as np
import pandas as pd


def modify_ThisMonthsUnitSales(fme, tmus):
    fme_copy = fme.sort_values(by='ISBN', ascending=True, na_position='first').copy()
    # Add column Units Sold from tmus
    tmus = tmus.dataframe
    tmus['ISBN'] = tmus['ISBN'].fillna(0).astype(str)
    fme_copy['ISBN'] = fme_copy['ISBN'].astype(str)

    fme_copy = fme_copy.merge(tmus[['ISBN', 'Units Sold']], on='ISBN', how='left')

    fme_copy.fillna({'Units Sold': 0}, inplace=True)

    # list all columns that have mixed data types

    # Changed Units Sold to dtype int
    fme_copy['Units Sold'] = fme_copy['Units Sold'].fillna(0).astype('int')
    fmecopy2 = fme_copy.copy()
    # Changed Net Qty to dtype int
    fme_copy['Net Qty'] = fme_copy['Net Qty'].fillna(0).astype('int')

    fme_copy["Net New Qty"] = fme_copy["Net Qty"] + fme_copy["Units Sold"]

    fme_copy['months_in_print'] = (pd.to_datetime('today') - fme_copy['Pub Date']) / np.timedelta64(1, 'M')
    # Divide Net  New Qty/months_in_print and multiply * 12. Add as Annualized Net Qty.
    fme_copy['Annualized Net Qty'] = (fme_copy['Net New Qty'] / fme_copy['months_in_print']) * 12

    # delete all columns whose name contains "Discount"
    fme_copy = fme_copy.loc[:, ~fme_copy.columns.str.contains('Discount')]

    # delete all columns whose name contains "List" except "US List"
    fme_copy = fme_copy.loc[:, ~(fme_copy.columns.str.contains('List') & ~fme_copy.columns.str.contains('US List'))]

    # delete all columns containing "Agency"
    fme_copy = fme_copy.loc[:, ~fme_copy.columns.str.contains('Agency')]

    fme_copy2 = fme_copy.sort_values(by='Pub Date', ascending=False, na_position='last')

    # list all columns that have mixed data types
    mixedtypes = fme_copy.dtypes[fme_copy.dtypes != 'object']
    print(mixedtypes)

    return fme_copy2


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


def show_all_backlist(fme_copy):
    fme_copy = fme_copy[fme_copy['months_in_print'] >= 18]
    return fme_copy


def hide_royaltied(fme_copy):
    # if royaltied is false
    fme_copy = fme_copy[~fme_copy['royaltied']]
    return fme_copy
