import sqlite3

def reset_slots():
    conn = sqlite3.connect("parkright.db")
    cursor = conn.cursor()

    # Reset all slots to available (0)
    cursor.execute("UPDATE slots SET is_occupied = 0")

    conn.commit()
    conn.close()
    print("All slots reset to available.")

if __name__ == "__main__":
    reset_slots()
