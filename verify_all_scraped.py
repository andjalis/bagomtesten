import json
import sqlite3
import numpy as np
import pandas as pd

def calc_match_linear(user_answers, candidate_answers):
    """Calculate match percentage using linear distance."""
    # DR uses (1 - total_distance / max_distance) * 100
    # max_distance per question is 3 (abs(0-3)).
    score, max_score = 0, 0
    for u, c in zip(user_answers, candidate_answers):
        if u is not None and c is not None and 0 <= u <= 3 and 0 <= c <= 3:
            diff = abs(u - c)
            score += 3 - diff
            max_score += 3
    if max_score > 0:
        return round((score / max_score) * 100)
    return 0

# Load scraped candidates
with open("all_candidates.json", "r", encoding="utf-8") as f:
    candidates_list = json.load(f)

# Map by name for easy lookup
scraped_map = {c["name"]: c["answers"] for c in candidates_list if c["answers"] and len(c["answers"]) == 25}

# Load historical runs from DB
conn = sqlite3.connect("history.db")
query = """
    SELECT rn.answers_json, res.candidate_name, res.match_pct
    FROM runs rn
    JOIN results res ON rn.id = res.run_id
    WHERE rn.status = 'done'
    LIMIT 2000
"""
df = pd.read_sql_query(query, conn)
conn.close()

results = []
for idx, row in df.iterrows():
    name = row["candidate_name"]
    if name in scraped_map:
        try:
            u_ans = json.loads(row["answers_json"])
            c_ans = scraped_map[name]
            actual_pct = row["match_pct"]
            sim_pct = calc_match_linear(u_ans, c_ans)
            
            results.append({
                "name": name,
                "actual": actual_pct,
                "sim": sim_pct,
                "error": abs(actual_pct - sim_pct)
            })
        except:
            pass

if not results:
    print("No matching candidates found between scraped data and DB samples.")
else:
    res_df = pd.DataFrame(results)
    avg_error = res_df["error"].mean()
    perfect_matches = (res_df["error"] == 0).sum()
    total = len(res_df)
    
    print(f"Verified {total} matches across candidates.")
    print(f"Average Error: {avg_error:.2f}%")
    print(f"Perfect Matches (0% error): {perfect_matches} ({perfect_matches/total*100:.1f}%)")
    
    if avg_error > 2:
        print("\nTop errors:")
        print(res_df.sort_values("error", ascending=False).head(10))
