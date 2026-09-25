from database.db_manager import get_connection
conn = get_connection()
conn.execute('DELETE FROM crm_conversions')
conn.execute('DELETE FROM action_register')
conn.commit()
conn.close()
print('Cleared dummy CRM and Task data.')
