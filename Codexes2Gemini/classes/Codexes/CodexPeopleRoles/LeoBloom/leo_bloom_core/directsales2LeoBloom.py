import glob

import pandas as pd


# calculates and reports royalties for direct sales for all royaltied authors

def ingest_direct_sales(userdocs_directsales_path):
    print(userdocs_directsales_path)
    directtarget = userdocs_directsales_path + '/' + '2*.xls*'

    directdf = pd.DataFrame()
    directdata = None
    for i in glob.glob(directtarget):
        print(i)
        try:
            directdata = pd.read_excel(i)
            print(directdata)
        except Exception as e:
            print('could not read direct sales file', i)
        directdf = directdf.append(directdata)

        print('directdf', directdf.columns)
    directdf.to_excel(userdocs_directsales_path + '/alldirectsales.xlsx')
    return directdf


def calculate_and_report_direct_sale_royalties(year, directdf,
                                               userdocs_path='/Users/fred/bin/nimble/unity/app/userdocs/37/leo_bloom_core'):
    authordata = pd.read_excel(userdocs_path + '/authordata/royaltied_authors.xlsx')
    list_of_author_results = []
    dict_of_author_messages = {}
    for index, row in authordata.iterrows():  # looping over authors by id number
        # print(row)
        author_sales_units = directdf[directdf['royaltied_author_id'] == row['royaltied_author_id']][
            'YTD_net_quantity'].sum()

        # calculate net revenue for the current  author from direct sales

        author_direct_sales_net_revenue = directdf[directdf['royaltied_author_id'] == row['royaltied_author_id']][
            'USDeq_pub_comp'].sum()

        royaltydue = (author_direct_sales_net_revenue * .30).round(2)
        # address escalators in future
        # print(row['royaltied_author_id'], author_sales_units, 'units', 'royalty due', royaltydue)

        row_results = {'royaltied_author_id': row['royaltied_author_id'],
                       'royalty_units': author_sales_units, 'royalty_net_revenue': author_direct_sales_net_revenue,
                       'royalty_due': royaltydue,
                       'year': year, "ASIN/ISBN": directdf['ASIN/ISBN'], "Title": directdf['Title'],
                       "Currency": directdf['Currency']}
        list_of_author_results.append(row_results)
        dict_of_author_messages[row['royaltied_author_id']] = {'royalty_units': author_sales_units,
                                                               'royalty_net_revenue': author_direct_sales_net_revenue,
                                                               'royalty_due': royaltydue,
                                                               "ASIN/ISNB": directdf['ASIN/ISBN'],
                                                               "Title": directdf['Title'],
                                                               "Currency": directdf['Currency']}

    direct_sales_royalties_df = pd.DataFrame(list_of_author_results,
                                             columns=['royaltied_author_id', 'royalty_units', 'royalty_net_revenue',
                                                      'royalty_due', 'year'])

    direct_sales_royalties_df.to_excel(userdocs_path + '/royaltyreports/directsales_royalties.xlsx')

    return direct_sales_royalties_df


if __name__ == "__main__":
    userdocs_path = '/Users/fred/bin/nimble/unity/app/userdocs/37/leo_bloom_core'
    userdocs_directsales_path = userdocs_path + '/directsales'
    directdf = ingest_direct_sales(userdocs_directsales_path)
    direct_sales_royalties_df = calculate_and_report_direct_sale_royalties('2022', directdf)
