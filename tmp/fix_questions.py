import sqlite3
import os

DB_PATH = "/Users/andjalis/Desktop/Kandidattest/history.db"

CORRECTIONS = {
    11: "Flere børn med særlige udfordringer bør gå i specialklasse frem for i almindelige skoleklasser",
    16: "Afgifter på benzin og diesel skal sænkes"
}

def fix():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for num, text in CORRECTIONS.items():
        print(f"Fixing question {num}...")
        
        # 1. Delete rows for this number that contain the bad strings
        bad_patterns = ["%DR passer%", "%1/25%", "%Bolig%"]
        for pattern in bad_patterns:
            cur.execute("DELETE FROM questions WHERE question_number = ? AND question_text LIKE ?", (num, pattern))
            print(f"  Deleted rows for Q{num} matching {pattern}: {cur.rowcount}")

        # 2. Check if the correct text already exists
        cur.execute("SELECT id FROM questions WHERE question_number = ? AND question_text = ?", (num, text))
        existing = cur.fetchone()
        
        if not existing:
            # 3. Create it if missing
            cur.execute("INSERT INTO questions (question_number, question_text) VALUES (?, ?)", (num, text))
            print(f"  Inserted correct text for Q{num}")
        else:
            print(f"  Correct text for Q{num} already exists (ID: {existing[0]})")

    conn.commit()
    conn.close()
    print("Database cleanup complete.")

if __name__ == "__main__":
    fix()
