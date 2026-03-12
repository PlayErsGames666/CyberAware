import sqlite3
import os

db_path = r'c:\Users\HP\Desktop\DuoProject\CyberAware\myworld\cyberaware\db.sqlite3'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print('Tables in db.sqlite3:')
    for table in tables:
        print(f'  - {table[0]}')
    
    print('\nRecord counts:')
    for table in tables:
        cursor.execute(f'SELECT COUNT(*) FROM {table[0]}')
        count = cursor.fetchone()[0]
        print(f'    {table[0]}: {count} records')
    
    # Show some sample data from key tables
    print('\nSample data:')
    for table in tables:
        if 'auth_user' in table[0] or 'members_member' in table[0]:
            cursor.execute(f'SELECT * FROM {table[0]} LIMIT 3')
            rows = cursor.fetchall()
            cursor.execute(f"PRAGMA table_info({table[0]})")
            columns = [col[1] for col in cursor.fetchall()]
            print(f'\n{table[0]}:')
            print(f'  Columns: {columns}')
            for row in rows:
                print(f'  {row}')
    
    conn.close()
else:
    print('Database file not found')
