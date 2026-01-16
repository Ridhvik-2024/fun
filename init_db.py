import sqlite3

DB_PATH = "tracker.db"

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS meals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    meal_type TEXT NOT NULL,
    planned_item TEXT,
    status TEXT CHECK(status IN ('done','partial','skipped')),
    discomfort TEXT,
    notes TEXT,
    updated_at TEXT,
    UNIQUE(date, meal_type)
)
""")

con.commit()
con.close()

print("✅ Database initialized: tracker.db")
