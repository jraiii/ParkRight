# seed.py
import sqlite3

def seed():
    conn = sqlite3.connect("parkright.db")
    cursor = conn.cursor()

    establishments = [
        ("SM Bataan",),
        ("Vista Mall Bataan",),
        ("Robinsons Galleria Bataan",),
        ("Capitol Square",)
    ]
    cursor.executemany("INSERT OR IGNORE INTO establishments (name) VALUES (?)", establishments)

    # Add slots for each establishment
    cursor.execute("SELECT id, name FROM establishments")
    for est_id, est_name in cursor.fetchall():
        slots = [(f"S{i}", 0, est_id) for i in range(1, 11)]
        cursor.executemany("INSERT INTO slots (number, is_occupied, establishment_id) VALUES (?, ?, ?)", slots)

    conn.commit()
    conn.close()
    print("Seed data inserted.")

if __name__ == "__main__":
    seed()
