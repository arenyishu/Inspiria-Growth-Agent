import pandas as pd
from datetime import timedelta
from database.db_manager import upsert_crm_conversions, get_connection

print('Reading Google Sheet...')
df = pd.read_excel('data.xlsx', sheet_name='11_Data_Conversions', skiprows=3)
df.columns = df.iloc[0]
df = df.dropna(subset=['Conversion ID'])
df = df[1:] # remove header row

# Shift dates to end at 2026-09-24
max_date = pd.to_datetime(df['Conversion Date']).max()
target_max = pd.to_datetime('2026-09-24')
offset = target_max - max_date

df['Conversion Date'] = pd.to_datetime(df['Conversion Date']) + offset
df['Conversion Date'] = df['Conversion Date'].dt.strftime('%Y-%m-%d')

print(f'Importing {len(df)} rows...')
upsert_crm_conversions(df)
print('Done!')
