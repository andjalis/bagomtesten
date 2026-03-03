# DR Kandidattest — Bias & Algoritme Analyse 🗳️

En fuldautomatiseret analyse-motor, der systematisk gennemfører DR's Kandidattest for Folketingsvalget med det formål at afdække eventuel skjult bias i algoritmens kandidatanbefalinger.

## Formål
DR's Kandidattest anbefaler kandidater baseret på enighed. Ved at generere over 1 million simulerede tests med tilfældige svar har vi skabt en statistisk "baseline", der afslører, om visse partier eller kandidater bliver favoriseret af selve testens struktur eller spørgsmålsudvælgelse (algoritmisk bias).

---

## Metodik & Proces

### 1. Reverse-Engineering af Match-algoritmen 🧩
Vi har matematisk eftervist DR's match-metode for at sikre simulationens præcision.
- **Algoritme:** Lineær afstandsberegning (Manhattan distance), hvor afstanden mellem brugerens og kandidatens svar (0-3) beregnes per spørgsmål.
- **Validering:** Eftervist ved at sammenligne simulationer med over 8.000 ægte bruger-tests i `history.db`. Fejlmarginen er < 1%, hvilket bekræfter modellens nøjagtighed.

### 2. Landsdækkende Kandidat-Data 🛰️
For at sikre et komplet sammenligningsgrundlag har vi opsamlet data fra samtlige opstillede kandidater.
- **Indsamling:** Playwright-baseret scraping af ID 1–950 på DR's platform.
- **Omfang:** **714 kandidater** med verificerede navne, partier og alle 25 svar.
- **Teknik:** Brug af 10 parallelle browser-instanser (concurrency) og progressiv scroll-ekstraktion for at sikre 100% datakomplethed.

### 3. Massiv Landsdækkende Simulation 🎲
Dette er kernen i bias-analysen.
- **Volumen:** **1.100.000 simulerede test-kørsler** (100.000 pr. storkreds).
- **Proces:** Hver kørsel genererer tilfældige svar og beregner match mod alle relevante kandidater i storkredsen.
- **Benchmarking:** Ved at sammenligne disse tilfældige kørsler med ægte data, kan vi se hvem der "vinder statistisk set", selv uden politisk holdning.

---

## Arkitektur: Pre-Aggregation Pipeline

For at sikre lynhurtig load-tid og eliminere RAM-begrænsninger på Render.com bruger dashboardet et **to-trins setup**:

### Trin 1: Data-Compiler (`tools/build_dashboard_data.py`)
Et Python-script du kører **lokalt** én gang efter fremstilling af nye simulationsresultater. Scriptet:
1. Loader den komplette `results.csv` (5 mio. rækker, ~125 MB)
2. Udregner alle statistikker (gennemsnit, optællinger, fordelinger, korrelationer)
3. Gemmer færdig-tyggede JSON-filer i `data/precomputed/` (~3 MB totalt)

**Genererede JSON-filer:**
| Fil | Indhold |
|-----|---------|
| `global_kpis.json` | Nøgletal: bias index, total simuleringer, top-parti |
| `party_rankings.json` | Parti-fordeling af top-1 anbefalinger |
| `party_match_distributions.json` | Match-% fordelinger til violin/box plots |
| `party_pairs.json` | Heatmap: "Hvis X er nr. 1, hvem er nr. 2?" |
| `question_impact.json` | Spørgsmåls-indflydelse (effect size) |
| `candidate_gaming.json` | Top-kandidater og rank-fordeling |
| `kommune_stats.json` | Geografisk blok-fordeling pr. kommune |

### Trin 2: Letvægts Dashboard (`dashboard/app.py`)
Streamlit-appen læser **kun** de små JSON-filer — ingen tung CSV-parsing, ingen store DataFrames i hukommelsen. Serverens RAM-forbrug er under 100 MB.

---

## Sådan bruges projektet

### Første gang (fuld kørsel)

```bash
# 1. Installér afhængigheder
pip install -r requirements.txt

# 2. Opsæt Playwright (til scraping)
playwright install chromium

# 3. Scrap kandidatdata
python scrape_all_candidates.py

# 4. Kør simulering
python simulate_all.py

# 5. Byg dashboard-data (pre-aggregation)
python tools/build_dashboard_data.py

# 6. Start dashboardet
streamlit run dashboard/app.py
```

### Daglig brug (kun dashboard)

```bash
# Start dashboardet (forudsat data er bygget)
streamlit run dashboard/app.py
```

### Opdatering af data

```bash
# Opdatér kandidatsvar
python scrape_all_candidates.py

# Kør ny simulation
python simulate_all.py

# Genbyg dashboard-data
python tools/build_dashboard_data.py
```

---

## Dashboard Features

Dashboardet har 5 interaktive tabs:

### 🌍 Global Analyse
- **KPI Hero Cards:** Bias Index (chi-square), mest over-repræsenterede parti, algoritmens favorit-kandidat
- **Parti-distribution:** Bar chart med top-1 anbefalings-frekvenser
- **Gaming-analyse:** Kandidater der oftest anbefales + rank-distribution
- **Parti-par heatmap:** Hvem er nr. 2 når X er nr. 1?
- **Spørgsmåls-indflydelse:** Hvilke spørgsmål skaber størst forskel?
- **Blok-analyse:** Rød vs. Blå blok pr. kommune

### 🔍 Parti-Drilldown
Dybdegående analyse af ét specifikt parti: geografi, top-kandidater og partidisciplin.

### ⚖️ Sammenlign Partier
Side-by-side sammenligning af to partier med radar chart og nøgletal.

### 📍 Lokalt Nedslag
Interaktiv kommune-vælger med lokal blok-fordeling og top-kandidater.

### ⚙️ Metode & Data
Teknisk dokumentation og svar-distribution på tværs af kandidater.

---

## Projektstruktur

```
Kandidattest/
├── config.py                     # Farver, stier og datanormalisering
├── scrape_all_candidates.py      # Optimeret landsdækkende scraper (10 parallelle tabs)
├── simulate_all.py               # Simulation af 1.1 mio. tests (NumPy-optimeret)
├── all_candidates.json           # 714 verificerede kandidatsvar
├── results.csv                   # Rå simulationsresultater (~125 MB)
│
├── tools/
│   └── build_dashboard_data.py   # Pre-aggregation: CSV → 7 letvægts JSON-filer
│
├── data/
│   └── precomputed/              # Genererede JSON-views (~3 MB)
│       ├── global_kpis.json
│       ├── party_rankings.json
│       ├── party_match_distributions.json
│       ├── party_pairs.json
│       ├── question_impact.json
│       ├── candidate_gaming.json
│       └── kommune_stats.json
│
├── dashboard/
│   ├── app.py                    # Streamlit entry point
│   ├── data.py                   # Data loading layer (læser pre-computed JSONs)
│   ├── css.py                    # Custom CSS styling
│   └── sections/                 # Visualiserings-moduler
│       ├── __init__.py
│       ├── kpi_hero.py           # Hero cards med bias index
│       ├── party_distribution.py # Parti-fordeling bar chart
│       ├── gaming_analysis.py    # Kandidat gaming-analyse
│       ├── party_pairs.py        # Parti-par heatmap
│       ├── question_impact.py    # Spørgsmåls-indflydelse
│       ├── blok_analysis.py      # Rød/Blå blok analyse
│       ├── party_drilldown.py    # Parti deep-dive
│       ├── party_comparison.py   # Sammenlign to partier
│       ├── kommune_analysis.py   # Lokalt nedslag
│       └── data_foundation.py    # Metode & data
│
├── .streamlit/
│   └── config.toml               # Server-konfiguration (headless, CORS)
│
├── history.db                    # SQLite med ægte historisk data
└── README.md                     # Denne fil
```

---

## Deployment (Render.com)

Dashboardet er konfigureret til deployment på Render.com med:
- **Start-kommando:** `streamlit run dashboard/app.py --server.port $PORT --server.address 0.0.0.0`
- **Headless mode:** Aktiveret via `.streamlit/config.toml`
- **RAM-optimering:** Pre-aggregerede JSON-filer sikrer < 100 MB hukommelsesforbrug

> **Vigtigt:** Kør `python tools/build_dashboard_data.py` lokalt og commit `data/precomputed/`-mappen før deploy. Disse JSON-filer skal eksistere i repo'et, da Render ikke har adgang til den store CSV-fil.

> **Note:** `results.csv` er for stor til GitHub (125 MB). Brug Git LFS eller hold den lokalt — Render-serveren behøver den ikke, da al data er pre-aggregeret.
