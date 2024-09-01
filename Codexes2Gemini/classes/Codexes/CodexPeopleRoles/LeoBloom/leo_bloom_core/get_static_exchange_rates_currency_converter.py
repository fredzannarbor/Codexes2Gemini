#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 20 01:47:58 2021

@author: fred
"""

import pandas as pd
from app.utilities.LeoBloom.LeoBloom import create_date_variables
from currency_converter import CurrencyConverter

today, thisyear, starting_day_of_current_year, daysYTD, annualizer, this_year_month = create_date_variables()

import datetime

c = CurrencyConverter(fallback_on_missing_rate=True)

colnames = ['GBP', 'EUR', 'JPY', 'INR', 'CAD', 'BRL', 'MXN', 'AUD']
df = pd.DataFrame(data=None, columns=colnames)

pr = pd.period_range(start='2010-08', end='2011-03', freq='M')

prTupes = tuple([(period.month, period.year) for period in pr])

c = CurrencyConverter(fallback_on_missing_rate=True)

colnames = ['GBP', 'EUR', 'JPY', 'INR', 'CAD', 'BRL', 'MXN', 'AUD']
df = pd.DataFrame(data=None, columns=colnames)

start_datetime = datetime.datetime(2010, 1, 1)
end_datetime = datetime.datetime(today.year, today.month, today.day)

timedelta_index = pd.date_range(start=start_datetime, end=end_datetime, freq='M').to_series()
for index, value in timedelta_index.iteritems():
    print(index, value)
    dt = index.to_pydatetime()

    exchangedate = dt
    print(exchangedate)

    cgbp = c.convert(1, 'GBP', 'USD', date=(exchangedate))
    ceur = c.convert(1, 'EUR', 'USD', date=(exchangedate))
    cjpy = c.convert(1, 'JPY', 'USD', date=(exchangedate))
    cinr = c.convert(1, 'INR', 'USD', date=(exchangedate))
    ccad = c.convert(1, 'CAD', 'USD', date=(exchangedate))
    cbrl = c.convert(1, 'BRL', 'USD', date=(exchangedate))
    cmxn = c.convert(1, 'MXN', 'USD', date=(exchangedate))
    caud = c.convert(1, 'AUD', 'USD', date=(exchangedate))

    row = [cgbp, ceur, cjpy, cinr, ccad, cbrl, cmxn, caud]
    df.loc[exchangedate] = row

print(df)

df.to_csv('app/utilities/leo_bloom_core/exchangerates/new_historic.csv')
