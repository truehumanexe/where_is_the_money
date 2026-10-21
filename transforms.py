import numpy as np
import pandas as pd
from pathlib import Path
import csv

root = Path("./data")
raw_path = root/"raw"
clean_path = root/"clean"
map_name = "data_map.csv"


def census_truncation_transform():
    raw_df = pd.read_csv(raw_path/'pppub25.csv')
    market_cols = [
        'WSAL_VAL', # Wages & Salaries
        'SEMP_VAL', # Self-Employment
        'FRSE_VAL', # Farm Income
        # 'INT_VAL',  # Interest
        # 'DIV_VAL',  # Dividends
        # 'RNT_VAL',  # Rent, Royalties, Estates, Trusts
        # 'RET_VAL'   # Pensions & Taxable Retirement Distributions
    ]

    # MARSUPWT associates a given income with a particular number of people
    # it needs to be divded by 100

    income_df = raw_df[market_cols]
    df = raw_df[['MARSUPWT']].copy()
    df['unweighted_usd'] = income_df.sum(axis = 1)
    df.rename({"MARSUPWT":"population"}, inplace=True, axis = 1)
    df.to_csv(raw_path/'pppub25_truncated.csv', index=False) # the original file is too large


def census_personal_income_transform(file = 'pppub25_truncated.csv'):
    df = pd.read_csv(raw_path/file)

    df = df[df['unweighted_usd'] > 0]
    df['population']= df['population']/100
    df['usd'] = df['unweighted_usd'] * df['population']
    df['bin'] = log_lin_bin(df['unweighted_usd'], factor = 1)
    df[df['bin'] < 10000] = 10000
    df[df['bin'] > 1000000] = 1000000
    df = df.groupby('bin').agg({'population':'sum', 'usd':'sum'})
    df.reset_index(inplace=True)
    df.to_csv(clean_path/'us_income.csv', index=False)


def census_income_adjustment():
    census_df = pd.read_csv(clean_path/"us_income.csv")
    upper_income = census_df.loc[census_df['bin'] == 1000000, 'population'].values[0] * 1000000
    census_df.loc[census_df['bin'] == 1000000, 'usd'] =  upper_income
    census_df.to_csv(clean_path/'us_income_adjusted.csv', index = False)


def bea_transform():
    import csv 
    lines=[]

    with open(raw_path/'personal_income_bea.csv', mode='r') as f:
        lines = f.readlines()

    lines = lines[5:49]
    lines = csv.reader(lines)
    lines = list(map(lambda x: {'key':x[1].strip(), 'value':x[2].strip()}, lines))
    df = pd.DataFrame(lines)
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df['value'] *= 1e9
    df.to_csv(clean_path/'bea_income.csv', index=False)


def log_lin_bin(column, factor = 1):
    floor = np.pow(10,np.floor(np.log10(column)))
    bin = np.floor(column/floor/factor) * floor * factor
    bin = np.where(bin == 0, floor, bin).astype(int)
    return bin


def SCFP_transform(file = 'SCFP2022.csv'):
    df = pd.read_csv(raw_path/file)

    # Define variables
    # STOCKS: Direct & indirect stock holdings
    # HOUSES + ORESRE: Primary residence + other real estate
    # CHECKING
    # SAVING
    # DEBT
    # NETWORTH: Total net worth

    cols = 'YY1,WGT,NETWORTH'.split(',')
    df = df[cols]
    f = 'NETWORTH'
    d = df.loc[:, ['YY1', 'WGT', f]].copy()
    d.loc[d[f] <= 0,f] = 1 # needed for log operation later
  
    d['bin'] = log_lin_bin(d[f])
    d.loc[d[f] == 1,f] = 0
    d.loc[d['bin'] == 1,'bin'] = 0
    d[f.lower()] = d[f] * d['WGT']
    d.loc[(d['bin'] < 10000) & (d['bin'] > 1), 'bin'] = 10000
    d.loc[(d['bin'] >= 1000000), 'bin'] = 1000000
    d = d.groupby('bin').agg({'WGT':'sum', f.lower():'sum'})
    d.reset_index(inplace=True)
    d.rename({'networth':'usd', 'WGT':'population'},axis = 1, inplace = True)

    df = d

    df.to_csv(clean_path/'us_wealth.csv', index=False)