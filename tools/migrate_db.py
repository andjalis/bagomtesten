import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path("history.db")
CSV_PATH = Path("results.csv")

def migrate():
    print("Starting migration...")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if candidate_media already exists
    c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='candidate_media'")
    if c.fetchone()[0] == 1:
        print("Candidate media table already exists. Migration might have run already.")
        # But we still need to check if results table has those columns
    else:
        print("Creating candidate_media table...")
        c.execute("""
        CREATE TABLE candidate_media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            candidate_name TEXT NOT NULL,
            candidate_url TEXT,
            candidate_image TEXT,
            FOREIGN KEY (run_id) REFERENCES runs(id)
        )
        """)
        
        print("Migrating media data from results...")
        c.execute("""
        INSERT INTO candidate_media (run_id, candidate_name, candidate_url, candidate_image)
        SELECT run_id, candidate_name, candidate_url, candidate_image FROM results
        """)
    
    # Create new results table
    print("Rebuilding results table without media columns...")
    c.execute("""
    CREATE TABLE results_new (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER NOT NULL,
        rank INTEGER NOT NULL,
        candidate_name TEXT NOT NULL,
        party TEXT NOT NULL,
        match_pct INTEGER NOT NULL,
        FOREIGN KEY (run_id) REFERENCES runs(id)
    )
    """)
    
    c.execute("""
    INSERT INTO results_new (id, run_id, rank, candidate_name, party, match_pct)
    SELECT id, run_id, rank, candidate_name, party, match_pct FROM results
    """)
    
    c.execute("DROP TABLE results")
    c.execute("ALTER TABLE results_new RENAME TO results")
    
    conn.commit()
    conn.close()
    
    # Clean CSV
    print("Cleaning CSV...")
    if CSV_PATH.exists():
        df = pd.read_csv(CSV_PATH)
        if "candidate_url" in df.columns or "candidate_image" in df.columns:
            drops = [col for col in ["candidate_url", "candidate_image"] if col in df.columns]
            df = df.drop(columns=drops)
            df.to_csv(CSV_PATH, index=False)
            print(f"Dropped {drops} from CSV.")
    
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
