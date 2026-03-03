import json
import sqlite3

def main():
    with open("all_candidates.json", "r", encoding="utf-8") as f:
        candidates_list = json.load(f)

    scraped_names = {c["name"] for c in candidates_list if c.get("answers") and len(c["answers"]) == 25}
    all_scraped_names = {c["name"] for c in candidates_list}

    conn = sqlite3.connect("history.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT candidate_name FROM results")
    historical_names = {row[0] for row in cursor.fetchall()}
    conn.close()

    missing_from_scrape = historical_names - scraped_names
    missing_answers = all_scraped_names - scraped_names

    print(f"--- Fuldstændighedstjek ---")
    print(f"Totale unikke kandidater i historik (history.db): {len(historical_names)}")
    print(f"Totale scraped kandidater (all_candidates.json): {len(all_scraped_names)}")
    print(f"Totale scraped kandidater med fulde 25 svar: {len(scraped_names)}")
    
    print(f"\nKandidater i historiske data, men som mangler fra scrape eller ikke har alle svar:")
    for name in missing_from_scrape: # Forventer Jens Kier her baseret på forrige samtaler
        print(f"- {name}")

    print(f"\nKandidater scraped, men som mangler svar (< 25 svar):")
    for name in missing_answers:
        print(f"- {name}")

if __name__ == "__main__":
    main()
