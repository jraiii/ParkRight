# setup_db.py
import sqlite3

def setup():
    conn = sqlite3.connect("parkright.db")
    cursor = conn.cursor()

    # Create establishments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS establishments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
    """)

    # Create slots table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        number TEXT,
        is_occupied INTEGER DEFAULT 0,
        establishment_id INTEGER,
        FOREIGN KEY(establishment_id) REFERENCES establishments(id)
    )
    """)

    conn.commit()
    conn.close()
    print("Database setup complete.")

if __name__ == "__main__":
    setup()
