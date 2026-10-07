import numpy as np
import pandas as pd
from pathlib import Path
import csv

root = Path("./data")
raw_path = root/"raw"
clean_path = root/"clean"
map_name = "data_map.csv"

def fred_transform(subject, save = False):
    data_map = pd.read_csv(root/map_name)
    data_map = data_map.loc[data_map['subject'] == subject,:]

    name = data_map['subject'].values[0]
    unit = data_map['unit'].values[0]
    multiplier = data_map['multiplier'].values[0]
    input_file = data_map['filename'].values[0]
    column_name = input_file.split('.')[0]

    df = pd.read_csv(raw_path/input_file)
    df = df.rename({'observation_date':'date', column_name: unit}, axis = 1)

    df[unit] *= multiplier	

    df['year'] = pd.to_datetime(df['date']).dt.year

    if unit == 'population':
        df = df[['year',unit]].groupby('year').mean().reset_index()
    else:
        df = df[['year',unit]].groupby('year').sum().reset_index()

    if save:
        df.to_csv((clean_path/name).with_suffix('.csv'), index=False)

    return(df)

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
    # df['unweighted_usd'] = raw_df['PTOTVAL']
    df.rename({"MARSUPWT":"people"}, inplace=True, axis = 1)
    df.to_csv(raw_path/'pppub25_truncated.csv', index=False) #this original file is large, I don't want to store it.

def census_personal_income_transform():
    df = pd.read_csv(raw_path/'pppub25_truncated.csv')

    df = df[df['unweighted_usd'] > 0]
    df['people']= df['people']/100
    df['usd'] = df['unweighted_usd'] * df['people']
    df['bin'] = log_bin(df['unweighted_usd'], factor = 1)
    df[df['bin'] < 10000] = 10000
    df[df['bin'] > 1000000] = 1000000
    df = df.groupby('bin').agg({'people':'sum', 'usd':'sum'})
    df['people_cdf'] = df['people'].cumsum()/df['people'].sum()
    df['usd_cdf'] = df['usd'].cumsum()/df['usd'].sum()
    df.reset_index(inplace=True)
    df.rename({"bin":"salary_bin"},axis =1, inplace=True)
    df['people_bin'] = log_bin(df['people'], factor = 1)
    df.to_csv(clean_path/'census_personal_income.csv', index=False)

    # e.g. plot; bins need to go to string for proper display
    # px.bar(y = df['usd'], x = df.index.astype(str))

def quick_stats_transform():
    import csv 
    lines=[]

    with open(raw_path/'personal_income_bea.csv', mode='r') as f:
        lines = f.readlines()

    lines = lines[5:49]
    lines = csv.reader(lines)
    # lines = list(map(lambda x: x.replace('\"', ''), lines))
    # lines = list(map(lambda x: x.split(',')[1:3], lines))
    lines = list(map(lambda x: {'key':x[1].strip(), 'value':x[2].strip()}, lines))
    df = pd.DataFrame(lines)
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df['value'] *= 1e9
    df.to_csv([clean_path/'quick_stats.csv'], index=False)



def clean_fred_data():
    data_map = pd.read_csv(root/map_name)
    subjects = data_map.loc[data_map['source'] == 'FRED', 'subject'].values

    for s in subjects:
        try:
            fred_transform(s, save = True)

        except Exception as e:
            print(f'Transform failed: {s}')
    print("FRED data transforms completed")

def log_bin(column, factor = 1):
    floor = np.pow(10,np.floor(np.log10(column)))
    bin = np.floor(column/floor/factor) * floor * factor
    bin = np.where(bin == 0, floor, bin).astype(int)
    return bin
    