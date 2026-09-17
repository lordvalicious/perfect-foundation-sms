import sqlite3
conn = sqlite3.connect(r'C:\Users\Ryuk\Documents\perfect-foundation-sms\backend\db.sqlite3')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts_user'")
rows = cursor.fetchall()
print("accounts_user table exists:", len(rows) > 0)
if rows:
    print("Table columns:", [desc[0] for desc in cursor.description])
else:
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("All tables:", [t[0] for t in tables])
conn.close()