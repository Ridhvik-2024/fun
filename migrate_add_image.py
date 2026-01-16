import sqlite3

DB_PATH = "tracker.db"

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

try:
    cur.execute("ALTER TABLE meals ADD COLUMN image TEXT")
    print(" Column 'image' added")
except sqlite3.OperationalError as e:
    print(" Migration skipped:", e)

con.commit()
con.close()
