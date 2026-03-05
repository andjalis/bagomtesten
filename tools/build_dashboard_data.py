"""
build_dashboard_data.py — Pre-aggregation Pipeline

This script parses the massive `results.csv` and `history.db` files and
pre-computes all the statistical aggregations needed by the Streamlit dashboard.
It outputs tiny, lightweight JSON files into `data/precomputed/` so the dashboard
can load instantly on low-memory servers like Render's Free/Starter tiers.

Run this script locally whenever you have finished a large scrape/simulation run:
    python tools/build_dashboard_data.py
"""

import sys
import os
import json
import sqlite3
from pathlib import Path

# Add project root to sys.path so config modules can be found
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

import pandas as pd
from config import normalize_parties_df, DB_PATH, CSV_PATH

OUT_DIR = PROJECT_ROOT / "data" / "precomputed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def main():
    print(f"Loading {CSV_PATH} (This may take a minute...)")
    if not os.path.exists(CSV_PATH):
        print(f"Error: Could not find {CSV_PATH}. Have you run simulate_lhs.py?")
        return

    # 1. Load the raw data
    usecols = ["run_id", "municipality", "candidate_rank", "candidate_name", "party", "match_pct"]
    dtypes = {
        "municipality": "category",
        "candidate_rank": "int8",
        "candidate_name": "category",
        "party": "category",
        "match_pct": "int16"
    }
    df = pd.read_csv(CSV_PATH, usecols=usecols, dtype=dtypes, low_memory=False)
    
    # Attach candidate_image from DB if possible
    try:
        conn = sqlite3.connect(DB_PATH)
        media_df = pd.read_sql_query("SELECT candidate_name, candidate_image FROM candidate_media", conn)
        conn.close()
        if not media_df.empty:
            media_df = media_df.drop_duplicates(subset=["candidate_name"])
            df = df.merge(media_df, on="candidate_name", how="left")
    except Exception as e:
        print(f"Warning: Could not attach candidate media - {e}")
        
    if "candidate_image" not in df.columns:
        df["candidate_image"] = ""
    else:
        df["candidate_image"] = df["candidate_image"].fillna("")
        
    df = normalize_parties_df(df)
    top1 = df[df["candidate_rank"] == 1].copy()

    print(f"Loaded {len(df):,} total rows, {len(top1):,} Top-1 rows.")

    # 2. Extract Data Foundations (Global KPIs)
    print("Building global_kpis.json...")
    try:
        conn = sqlite3.connect(DB_PATH)
        runs_df = pd.read_sql_query("SELECT COUNT(DISTINCT municipality) as storkredse, COUNT(DISTINCT answer_hash) as user_variants FROM runs WHERE status='done'", conn)
        conn.close()
        storkredse = int(runs_df['storkredse'].iloc[0]) if not runs_df.empty else 10
        user_variants = int(runs_df['user_variants'].iloc[0]) if not runs_df.empty else 100000
    except:
        storkredse, user_variants = 10, 100000

    # Bias index components
    party_counts = top1['party'].value_counts()
    n_total = len(top1)
    k_parties = len(party_counts)
    expected = n_total / k_parties if k_parties > 0 else 1
    chi_square = ((party_counts - expected) ** 2 / expected).sum()
    max_chi = n_total * (k_parties - 1)
    bias_index = (chi_square / max_chi * 100) if max_chi > 0 else 0

    top_party = party_counts.index[0] if len(party_counts) > 0 else "N/A"
    top_party_count = int(party_counts.iloc[0]) if len(party_counts) > 0 else 0
    top_party_pct = (top_party_count / n_total * 100) if n_total > 0 else 0
    top_party_overrep = (top_party_count / expected) if expected > 0 else 1

    cand_counts = top1['candidate_name'].value_counts()
    top_cand = cand_counts.index[0] if len(cand_counts) > 0 else "N/A"
    top_cand_count = int(cand_counts.iloc[0]) if len(cand_counts) > 0 else 0

    # Find the party of the top candidate
    top_cand_party = "Ukendt"
    if top_cand != "N/A":
        cand_party_match = top1[top1['candidate_name'] == top_cand]['party']
        if not cand_party_match.empty:
            top_cand_party = str(cand_party_match.iloc[0])

    kpis = {
        "storkredse": storkredse,
        "total_candidates": 714,
        "total_simulations": n_total,
        "k_parties": k_parties,
        "bias_index": bias_index,
        "top_party": top_party,
        "top_party_count": top_party_count,
        "top_party_pct": top_party_pct,
        "top_party_overrep": float(top_party_overrep),
        "top_candidate": top_cand,
        "top_candidate_count": top_cand_count,
        "top_candidate_party": top_cand_party,
    }
    with open(OUT_DIR / "global_kpis.json", "w", encoding="utf-8") as f:
        json.dump(kpis, f, ensure_ascii=False)

    # 3. Party Rankings (Distribution bar chart)
    print("Building party_rankings.json...")
    party_stats = party_counts.reset_index()
    party_stats.columns = ["Party", "Count"]
    party_stats["Procent"] = party_stats["Count"] / party_stats["Count"].sum() * 100
    party_stats["Expected"] = 100 / k_parties if k_parties > 0 else 0
    party_stats["Deviation"] = party_stats["Procent"] - party_stats["Expected"]
    party_stats.to_json(OUT_DIR / "party_rankings.json", orient="records", force_ascii=False)

    # 4. Match Distributions (Violin / Box plots)
    # We don't want to save 10 million floats. Violin plots just need the quantiles and a sample
    print("Building party_match_distributions.json...")
    match_samples = []
    # Taking a stratified sample of match percentages to keep the file very small (< 1MB)
    # while preserving the exact distribution shape for the UI
    sampled_match = df.groupby("party", observed=False).apply(
        lambda x: x.sample(n=min(len(x), 5000), random_state=42)
    ).reset_index(drop=True)
    
    sampled_match[["party", "match_pct"]].to_json(OUT_DIR / "party_match_distributions.json", orient="records", force_ascii=False)

    # 5. Party Pairs (Heatmap)
    print("Building party_pairs.json...")
    df_sorted = df.sort_values(["run_id", "candidate_rank"])
    rank1 = df_sorted[df_sorted["candidate_rank"] == 1][["run_id", "party"]].rename(columns={"party": "Rank1_Party"})
    rank2 = df_sorted[df_sorted["candidate_rank"] == 2][["run_id", "party"]].rename(columns={"party": "Rank2_Party"})
    
    pairs = pd.merge(rank1, rank2, on="run_id", how="inner")
    pair_counts = pairs.groupby(["Rank1_Party", "Rank2_Party"], observed=False).size().reset_index(name="Count")
    
    heatmap_data = []
    for r1 in pair_counts["Rank1_Party"].unique():
        subset = pair_counts[pair_counts["Rank1_Party"] == r1]
        total = subset["Count"].sum()
        for _, row in subset.iterrows():
            heatmap_data.append({
                "Rank1_Party": r1,
                "Rank2_Party": row["Rank2_Party"],
                "Count": int(row["Count"]),
                "Percentage": float(row["Count"] / total * 100) if total > 0 else 0
            })
    pd.DataFrame(heatmap_data).to_json(OUT_DIR / "party_pairs.json", orient="records", force_ascii=False)

    # 6. Candidate Gaming (Rank distributions)
    print("Building candidate_gaming.json...")
    top1_stats = (
        top1.groupby(["candidate_name", "party", "candidate_image"], observed=False)
        .agg(count=("run_id", "count"), municipality=("municipality", "first"))
        .reset_index()
    )
    total_appearances = df.groupby("candidate_name", observed=False).size().reset_index(name="total_count")
    top1_stats = pd.merge(top1_stats, total_appearances, on="candidate_name", how="inner")
    
    # We only need stats for the top 50 candidates to keep it light
    top_candidates = top1_stats.sort_values("count", ascending=False).head(50)
    top_c_names = top_candidates["candidate_name"].tolist()
    
    rank_breakdown = (
        df[df["candidate_name"].isin(top_c_names)]
        .groupby(["candidate_name", "party", "candidate_rank"], observed=False)
        .size().reset_index(name="Antal")
    )
    
    gaming_data = {
        "top_candidates": json.loads(top_candidates.to_json(orient="records", force_ascii=False)),
        "rank_breakdown": json.loads(rank_breakdown.to_json(orient="records", force_ascii=False))
    }
    with open(OUT_DIR / "candidate_gaming.json", "w", encoding="utf-8") as f:
        json.dump(gaming_data, f, ensure_ascii=False)

    # 7. Question Impact (Effect Size)
    print("Building question_impact.json...")
    try:
        conn = sqlite3.connect(DB_PATH)
        # Join runs with results to get the rank-1 match_pct
        query = """
        SELECT r.answers_json, res.match_pct 
        FROM runs r 
        JOIN results res ON r.id = res.run_id 
        WHERE r.status='done' AND res.rank=1
        """
        runs_df = pd.read_sql_query(query, conn)
        cursor = conn.cursor()
        cursor.execute("SELECT question_number, question_text FROM questions")
        q_texts = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        
        if not runs_df.empty:
            answers_list = runs_df['answers_json'].apply(json.loads).tolist()
            q_df = pd.DataFrame(answers_list, columns=[f"Q{i+1}" for i in range(25)])
            q_df['match_pct'] = runs_df['match_pct']
            
            impact_data = []
            for i in range(1, 26):
                q_col = f"Q{i}"
                if q_col in q_df.columns:
                    means = q_df.groupby(q_col, observed=False)['match_pct'].mean()
                    if len(means) > 1:
                        effect_size = means.max() - means.min()
                        impact_data.append({
                            "Spørgsmål": f"Q{i}",
                            "Tekst": q_texts.get(i, ""),
                            "Indflydelse (effect size)": float(effect_size)
                        })
            
            impact_df = pd.DataFrame(impact_data).sort_values("Indflydelse (effect size)", ascending=False)
            impact_df.to_json(OUT_DIR / "question_impact.json", orient="records", force_ascii=False)
    except Exception as e:
        print(f"Warning: Could not build question_impact.json - {e}")

    # 8. Kommune Stats (Geographic Distribution)
    print("Building kommune_stats.json...")
    red_block = ["Socialdemokratiet", "Socialistisk Folkeparti", "Enhedslisten", "Radikale Venstre", "Alternativet"]
    blue_block = ["Venstre", "Liberal Alliance", "Konservative", "Danmarksdemokraterne", "Dansk Folkeparti", "Borgernes Parti"]

    def assign_block(p):
        if p in red_block: return "Rød blok"
        if p in blue_block: return "Blå blok"
        return "Andet"

    top1_kommune = top1.copy()
    top1_kommune["Blok"] = top1_kommune["party"].apply(assign_block)
    
    kommune_stats = []
    for muni, group in top1_kommune.groupby("municipality", observed=False):
        block_counts = group["Blok"].value_counts()
        total = len(group)
        if total == 0: continue
            
        red_pct = float(block_counts.get("Rød blok", 0) / total * 100)
        blue_pct = float(block_counts.get("Blå blok", 0) / total * 100)
        
        top_party = group["party"].value_counts().index[0]
        top_candidate = group["candidate_name"].value_counts().index[0]
        
        kommune_stats.append({
            "Kommune": str(muni),
            "Red_Pct": red_pct,
            "Blue_Pct": blue_pct,
            "Vinder_Blok": "Rød blok" if red_pct > blue_pct else ("Blå blok" if blue_pct > red_pct else "Lige"),
            "Top_Party": str(top_party),
            "Top_Candidate": str(top_candidate),
            "Total_Tests": int(total)
        })
        
    pd.DataFrame(kommune_stats).to_json(OUT_DIR / "kommune_stats.json", orient="records", force_ascii=False)

    print("Success! Pre-aggregation completed. Data saved to data/precomputed/")

if __name__ == "__main__":
    main()
