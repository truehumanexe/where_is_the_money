import numpy as np
import pandas as pd
from pathlib import Path

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

def clean_fred_data():
    data_map = pd.read_csv(root/map_name)
    subjects = data_map.loc[data_map['source'] == 'FRED', 'subject'].values

    for s in subjects:
        try:
            fred_transform(s, save = True)

        except Exception as e:
            print(f'Transform failed: {s}')
    print("FRED data transforms completed")
    