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

## Sådan bruges dashboardet

Dashboardet (`dashboard.py`) visualiserer resultaterne og hjælper med at identificere bias:

- **Top 5 Vindere:** Viser hvilke kandidater der oftest optræder i toppen ved tilfældige svar.
- **Metodik-info:** Forklarer statistisk usikkerhed og margin of error.
- **Metrikker:**
  - **Gennemsnitligt Match:** Hvor nemt er det at opnå enighed med en kandidat?
  - **Vinder-frekvens:** Hvor ofte lander en kandidat som nr. 1?
  - **"Sweet Spot" Analyse:** Hvilket svarmønster maksimerer chancerne for at blive matchet?

---

## Projektstruktur

```
Kandidattest/
├── config.py                 # Farver, stier og datanormalisering
├── scrape_all_candidates.py  # Optimeret landsdækkende scraper (10 parallelle tabs)
├── simulate_all.py           # Simulation af 1.1 mio. tests (NumPy-optimeret)
├── all_candidates.json       # Database med 714 verificerede kandidatsvar
├── simulated_all_results.csv # Resultater af den massive simulation (~1GB)
├── dashboard.py              # Streamlit dashboard til visualisering
├── history.db                # SQLite database med ægte historisk data
└── README.md                 # Denne fil
```

---

## Opsætning

Kræver **Python 3.10+**.

```bash
# 1. Installér afhængigheder
pip install -r requirements.txt

# 2. Opsæt Playwright
playwright install chromium

# 3. Kør dashboardet
streamlit run dashboard.py
```

### Vedligeholdelse
Hvis du vil opdatere dataene:
```bash
# Opdatér kandidatsvar
python scrape_all_candidates.py

# Kør ny simulation
python simulate_all.py
```

> **Note:** `simulated_all_results.csv` gemmer kun Top 5 matches per run for at optimere diskplads, mens den stadig bevarer fuld statistisk værdi for bias-analysen.
