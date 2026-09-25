import pandas as pd
from database.db_manager import get_connection

df = pd.read_excel('data.xlsx', sheet_name='07_Action_Register', skiprows=4)
df.columns = df.iloc[0]
df = df.dropna(subset=['Action'])
df = df[1:] # remove header row

conn = get_connection()
conn.execute('DELETE FROM action_register')
for _, row in df.iterrows():
    status = 'Done' if row['Status'] == 'Completed' else 'Planned'
    conn.execute(
        "INSERT INTO action_register (task_name, status, priority, created_at) VALUES (?, ?, ?, date('now'))",
        (str(row['Action']), status, str(row['Priority']))
    )
conn.commit()
conn.close()
print('Tasks imported!')
