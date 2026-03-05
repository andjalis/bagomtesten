"""Data foundation / Methodology tab — comprehensive methodology explanation."""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st

from config import ANSWER_LABELS, ANSWER_COLORS
from dashboard.sections._plotly_theme import base_layout


def render_data_foundation():
    """Render the methodology tab with detailed, expandable methodology sections."""
    from dashboard.data import load_run_answers, load_db_top1, load_questions, load_global_kpis

    st.header("⚙️ Metode & data")

    kpis = load_global_kpis()
    if kpis:
        st.caption(f"LHS-simulering baseret på **{kpis.get('total_simulations', 0):,}** fuldførte test-kørsler.".replace(",", "."))

    # ── TL;DR: Two summary cards at top ──────────────────────────────────────
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("""
        <div class="info-card">
            <div class="info-card-title">Metodologi & datagrundlag</div>
            <div class="info-card-text">
                <strong>Vi scrapede indledningsvist over 10.000 ægte testkørsler manuelt</strong> fra DR's platform.
                Vores analyse af denne data beviste en 100% lineær og symmetrisk sammenhæng i DR's algoritme (dvs. ingen "sort boks").<br/><br/>
                På baggrund af dette har vi kunnet <strong>simulere resten af svarene ekstremt præcist</strong>. Vi har simuleret testen
                100.000 gange pr. storkreds med systematisk fordelte svar via <strong>Latin Hypercube Sampling (LHS)</strong>.
                Dette garanterer, at det politiske spektrum dækkes fuldt ud uden at belaste DR's servere.<br/><br/>
                Statistisk set <em>burde</em> resultaterne fordele sig rimelig jævnt mellem partierne ved helt tilfældige svar.
                Hvis bestemte partier over-anbefales konsekvent, tyder det på at testens vægtning er skævvredet.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="info-card">
            <div class="info-card-title">Analyse: Hvordan vægtes dine svar?</div>
            <div class="info-card-text">
                Vores data-analyse bekræfter en <strong>lineær og symmetrisk vægtning</strong> i DR's algoritme:
                <ul>
                    <li><strong>Fuld symmetri:</strong> "Enig" og "Uenig" vægtes præcis lige højt.</li>
                    <li><strong>Midter-fordelen:</strong> Svaret "Lidt enig/uenig" giver statistisk set et
                    marginalt højere gennemsnitligt match% (68,1% vs 67,5%) pga. kortere matematisk
                    afstand til alle mulige kandidat-svar.</li>
                    <li><strong>Linearitet:</strong> Springet i match-% er jævnt — en simpel point-model
                    (0, 1, 2, 3) hvor afstanden mellem hvert valg tæller lige meget.</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ── Detailed Methodology Sections ────────────────────────────────────────
    st.subheader("📖 Uddybende metodebeskrivelse")
    st.markdown(
        "Herunder følger en dybdegående gennemgang af hele projektets metodologi — "
        "fra den indledende datahøstning til den endelige statistiske analyse. "
        "Klik på de enkelte faser for at udfolde dem."
    )

    # ── PHASE 1: Data Collection ─────────────────────────────────────────────
    with st.expander("🔬 Fase 1 — Dataindsamling (webscraping af DR's kandidattest)", expanded=False):
        _render_phase_1()

    # ── PHASE 2: Algorithm Reverse Engineering ───────────────────────────────
    with st.expander("🧮 Fase 2 — Reverse engineering af DR's matchning-algoritme", expanded=False):
        _render_phase_2()

    # ── PHASE 3: LHS Simulation ──────────────────────────────────────────────
    with st.expander("🎲 Fase 3 — Latin Hypercube Sampling (LHS) simulation", expanded=False):
        _render_phase_3()

    # ── PHASE 4: Statistical Analysis Methods ────────────────────────────────
    with st.expander("📊 Fase 4 — Statistiske analysemetoder", expanded=False):
        _render_phase_4()

    # ── PHASE 5: Data Quality & Validation ───────────────────────────────────
    with st.expander("✅ Fase 5 — Datakvalitet & validering", expanded=False):
        _render_phase_5()

    # ── PHASE 6: Dashboard Pipeline ──────────────────────────────────────────
    with st.expander("🔧 Fase 6 — Dashboard-pipeline & teknisk arkitektur", expanded=False):
        _render_phase_6()

    st.divider()

    # ── Answer Distribution Chart ────────────────────────────────────────────
    answers_df = load_run_answers()
    questions_dict = load_questions()
    _render_answer_distribution(answers_df, questions_dict)


# ═════════════════════════════════════════════════════════════════════════════
# Phase renderers
# ═════════════════════════════════════════════════════════════════════════════

def _render_phase_1():
    """Phase 1: Data Collection."""
    st.markdown("""
    <div class="method-step">
        <div class="info-card-text">
            <h4>Formål</h4>
            <p>
                At opbygge et komplet, uafhængigt datasæt af DR's Kandidattest til Folketingsvalg 2026 — 
                både bruger-genererede testresultater og samtlige kandidaters egne besvarelser — 
                så vi kan analysere testens algoritmiske egenskaber uden at være afhængige af DR's egne konklusioner.
            </p>

            <h4>1.1 Scraping af testkørsler</h4>
            <p>
                Vi har udført <strong>over 10.000 fuldstændige gennemspilninger</strong> af DR's Kandidattest
                via en automatiseret, headless Playwright-browser (Chromium). Hver kørsel fungerer præcis
                som en rigtig bruger, der besvarer alle 25 spørgsmål og modtager en rangeret liste af
                anbefalede kandidater med match-procenter.
            </p>
            <p>For hver kørsel gemmes:</p>
            <ul>
                <li><strong>Svarkombinationen</strong> — alle 25 svar kodet som heltal (0 = Uenig, 1 = Lidt uenig, 2 = Lidt enig, 3 = Enig)</li>
                <li><strong>Top-resultaterne</strong> — de 5 bedst-matchede kandidater med navn, parti, match-% og storkreds</li>
                <li><strong>Metadata</strong> — unikt kørsel-ID, SHA-256-hash af svarene, tidsstempel og kommune</li>
            </ul>
            <p>
                Svarene blev genereret via <strong>Latin Hypercube Sampling</strong> (se fase 3) for at sikre
                systematisk dækning af hele svarrummet, fremfor tilfældig sampling som kan efterlade blinde pletter.
            </p>

            <h4>1.2 Anti-detekterings-foranstaltninger</h4>
            <p>
                For at undgå at blive blokeret af DR's servere og for at simulere naturlig brugeradfærd
                implementerede vi følgende foranstaltninger:
            </p>
            <ul>
                <li><strong>Randomiserede kommuner:</strong> Hver kørsel vælger tilfældigt blandt 28
                danske kommuner (København, Aarhus, Odense, Aalborg osv.), så anmodningerne
                stammer fra unikke adresser.</li>
                <li><strong>Rotation af User-Agent:</strong> Vi roterer mellem 5 forskellige browser-identificeringer
                (Chrome, Firefox, Safari på Windows og macOS) for at undgå fingerprinting.</li>
                <li><strong>Menneske-lignende forsinkelser:</strong> Mellem hvert klik indsættes en tilfældig
                forsinkelse på 0,5–1,3 sekunder, der emulerer normal bruger-interaktion.</li>
                <li><strong>Cookie-banner-håndtering:</strong> Automatisk accept af DR's cookie-dialog ved behov.</li>
            </ul>

            <h4>1.3 Scraping af kandidatprofiler</h4>
            <p>
                Sideløbende med testkørslerne har vi scraped <strong>samtlige kandidatprofiler</strong> fra
                DR's platform. Vi itererede gennem kandidat-ID'er fra 1 til 950 på URL'en:
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.code("https://www.dr.dk/nyheder/politik/folketingsvalg/din-stemmeseddel/kandidater/{id}")
    
    st.markdown("""
    <div class="method-step">
        <div class="info-card-text">
            <p>For hver kandidat udtrækkes:</p>
            <ul>
                <li><strong>Basisoplysninger:</strong> Navn, parti, storkreds/valgkreds</li>
                <li><strong>Alle 25 svar:</strong> Udtrukket via en "progressive scroll extraction"-teknik,
                der håndterer DR's lazy-loadede DOM ved gradvist at scrolle ned og aflæse nye elementer</li>
            </ul>
            <p>
                Ud af de 950 scannede ID'er fandt vi <strong>714 aktive kandidater</strong> (resten returnerede 404
                eller manglede svar). Alle 714 kandidater har en komplet besvarelse af alle 25 spørgsmål, 
                hvilket er afgørende for vores simulation.
            </p>
            <p>
                Dataudtrækningen anvender 10 parallelle browser-tabs for at holde den totale kørselstid nede,
                og resultater gemmes progressivt til en JSON-fil efter hver kandidat, så fremskridt ikke
                går tabt ved uventede nedbrud.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_phase_2():
    """Phase 2: Algorithm Reverse Engineering."""
    st.markdown("""
    <div class="method-step">
        <div class="info-card-text">
            <h4>Formål</h4>
            <p>
                At afdække den nøjagtige matematiske model, DR's Kandidattest bruger til at beregne
                match-procenter imellem brugersvar og kandidater, så vi kan simulere testen
                offline med 100% troværdighed.
            </p>

            <h4>2.1 Dataanalyse og mønstergenkendelse</h4>
            <p>
                Ved at analysere de over 10.000 scrapede testkørsler identificerede vi en <strong>konsekvent,
                lineær sammenhæng</strong> mellem svar-afstande og match-procenter. Specifikt opdagede vi:
            </p>
            <ul>
                <li><strong>Fuldstændig symmetri:</strong> At svare "Enig" giver præcis same match-afstand
                som "Uenig" i den modsatte retning. Der er ingen asymmetri eller skjult vægtning.</li>
                <li><strong>Lineært afstandsmål:</strong> Hvert spørgsmål koderes som et heltal fra 0 til 3.
                Afstanden mellem brugerens svar og kandidatens svar beregnes som den absolutte forskel
                |bruger – kandidat| for hvert af de 25 spørgsmål.</li>
                <li><strong>Ingen spørgsmålsvægtning:</strong> Alle 25 spørgsmål vægtes 100% ens.
                Der er ingen skjulte prioriteringer af bestemte emneområder.</li>
            </ul>

            <h4>2.2 Den afdækkede formel</h4>
            <p>Match-procenten beregnes ud fra den gennemsnitlige Manhattan-distance:</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.latex(r"Match\% = \left( 1 - \frac{\sum_{i=1}^{n} |S_B^i - S_K^i|}{n \times 3} \right) \times 100")
    
    st.markdown("""
    <div class="method-step">
        <div class="info-card-text">
            <p>
                Hvor $S_B^i$ er brugerens svar på spørgsmål $i$, og $S_K^i$ er kandidatens svar. 
                Nævneren ( $n \times 3$ ) er den maksimalt mulige samlede afstand, da afstanden
                pr. spørgsmål er maksimalt 3.
            </p>

            <h4>2.3 Implikationer af den lineære model</h4>
            <p>Den lineære model har én vigtig konsekvens, som vi kalder <strong>"midterfordelen"</strong>:</p>
            <ul>
                <li>En bruger, der svarer "Lidt enig" eller "Lidt uenig" (dvs. 1 eller 2 på skalaen),
                har en kortere <em>gennemsnitlig</em> afstand til samtlige mulige kandidatsvar end en bruger, der
                svarer "Enig" eller "Uenig" (0 eller 3).</li>
                <li>Konkret viser vores data, at midtersvar i gennemsnit giver en match-% på <strong>ca. 68,1%</strong>
                mod <strong>ca. 67,5%</strong> for ydersvar — en forskel på omtrent 0,6 procentpoint.</li>
                <li>Dette er en inherent egenskab ved enhver lineær afstandsmodel og udgør <em>ikke</em> i sig
                selv en bias. Det er dog værd at være opmærksom på, at kandidater med "moderate" svar
                dermed har en strukturel mikro-fordel.</li>
            </ul>

            <h4>2.4 Verifikation</h4>
            <p>
                Vi verificerede formlen ved at genberegne match-procenter offline for samtlige 10.000+
                scrapede kørsler. I <strong>alle tilfælde</strong> reproducerede vi DR's viste match-procent
                med en afvigelse på maks. ±1 procentpoint (skyldes afrunding). Dette bekræfter, at formlen
                er korrekt, og at vi trygt kan simulere testen offline.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_phase_3():
    """Phase 3: LHS Simulation."""
    st.markdown("""
    <div class="method-step">
        <div class="info-card-text">
            <h4>Formål</h4>
            <p>
                At simulere et astronomisk antal testkørsler — langt flere end hvad der ville være
                praktisk muligt at scrape — for at opnå en statistisk robust analyse af algoritmens
                fairness på tværs af alle mulige svarmønstre.
            </p>

            <h4>3.1 Hvorfor Latin Hypercube Sampling?</h4>
            <p>
                DR's Kandidattest har 25 spørgsmål med 4 svarmuligheder hver. Det totale svarrum
                har altså 4<sup>25</sup> ≈ 1,1 × 10<sup>15</sup> (1,1 billiard) mulige kombinationer.
                Det er umuligt at teste dem alle. Vi er derfor nødt til at <em>sample</em> fra dette rum,
                og her er valget af sampling-metode afgørende.
            </p>
            <p>
                <strong>Ren tilfældig sampling (Monte Carlo)</strong> lider under det problem, at prøverne
                har en tendens til at klumpe sig sammen i visse dele af rummet og efterlade andre dele
                underrepræsenterede — især i høj-dimensionelle rum (her: 25 dimensioner).
            </p>
            <p>
                <strong>Latin Hypercube Sampling</strong> løser dette ved at garantere en jævn fordeling
                i <em>hver eneste dimension</em>. Teknikken opdeler hver dimension i N lige store intervaller
                (hvor N = antal prøver) og sikrer, at der tages præcis én prøve fra hvert interval i
                hver dimension. Resultatet er en stratificeret sampling, der dækker svarrummet langt
                mere uniformt end tilfældig sampling med samme antal prøver.
            </p>

            <h4>3.2 Implementering</h4>
            <p>
                Vi bruger <code>scipy.stats.qmc.LatinHypercube</code> med d=25 dimensioner til at generere
                100.000 svar-kombinationer pr. kørsel. Processen er som følger:
            </p>
            <ol>
                <li><strong>LHS-generering:</strong> Generér N=100.000 prøver i et 25-dimensionelt
                enhedsinterval [0, 1).</li>
                <li><strong>Diskretisering:</strong> Skalér til heltal ved at gange med 4 og tage
                gulvet: svar = ⌊prøve × 4⌋, hvilket giver værdier i {0, 1, 2, 3}.</li>
                <li><strong>Match-beregning:</strong> For hver af de 100.000 svarkombinationer beregnes
                match-procenten mod alle lokale kandidater i den pågældende storkreds.</li>
                <li><strong>Top-5 udvælgelse:</strong> De 5 bedst-matchede kandidater gemmes pr. kørsel.</li>
            </ol>

            <h4>3.3 Skala</h4>
            <p>
                Simuleringen køres <strong>per storkreds</strong>, da kandidatudvalget varierer geografisk.
                Med 10 storkredse × 100.000 kørsler pr. storkreds giver det i alt <strong>1.000.000 simulerede
                testkørsler</strong>. For hver kørsel gemmes top-5-resultater, hvilket giver ca. 5 millioner
                datarækker i den rå CSV-fil (ca. 1 GB).
            </p>

            <h4>3.4 Vektoriseret beregning</h4>
            <p>
                For effektivitetens skyld beregnes match-procenterne vektoriseret med <strong>NumPy</strong>.
                I stedet for at iterere over individuelle kørsler og kandidater broadcaster vi
                bruger-svarmatricen (N × 25) mod kandidat-svarmatricen (M × 25) i hukommelses-effektive
                "chunks" af 5.000 kørsler ad gangen, hvilket holder RAM-forbruget nede under 500 MB
                selv for storkredse med 100+ kandidater.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_phase_4():
    """Phase 4: Statistical Analysis Methods."""
    st.markdown("""
    <div class="method-step">
        <div class="info-card-text">
            <h4>Formål</h4>
            <p>
                At omsætte de 1.000.000 simulerede testkørsler til kvantificerbar indsigt om
                algoritmisk fairness. Herunder beskrives de specifikke statistiske metoder,
                der anvendes i dashboardet.
            </p>

            <h4>4.1 Chi-i-anden (χ²) bias-index</h4>
            <p>
                Vores primære mål for algoritmisk skævvridning er et <strong>normaliseret chi-i-anden
                (χ²) bias-index</strong>. Det beregnes således:
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.latex(r"\chi^2 = \sum \frac{(O_i - E_i)^2}{E_i} \quad \rightarrow \quad \text{Bias Index} = \frac{\chi^2}{\chi^2_{max}} \times 100")
    
    st.markdown("""
    <div class="method-step">
        <div class="info-card-text">
            <p>
                Hvor $O_i$ er det observerede antal førstepladser for parti $i$, og $E_i$ er det
                forventede antal ved en fuldstændig fair fordeling ($total / partier$).
            </p>
            <p>
                Indexet normaliseres til en skala fra <strong>0 til 100</strong>, hvor:
            </p>
            <ul>
                <li><strong>0</strong> = perfekt balance: alle partier får præcis lige mange førstepladser</li>
                <li><strong>100</strong> = total skævvridning: ét enkelt parti får alle førstepladser</li>
            </ul>
            <p>I praksis kategoriserer vi resultatet som:</p>
            <ul>
                <li><strong style="color: #34d399;">0–15:</strong> Lav skævvridning — testen er rimelig fair</li>
                <li><strong style="color: #fbbf24;">15–40:</strong> Moderat — systematisk, men begrænset bias</li>
                <li><strong style="color: #f97316;">40–70:</strong> Høj — tydelig favorisering af bestemte partier</li>
                <li><strong style="color: #ef4444;">70–100:</strong> Kritisk — massiv algoritmisk skævvridning</li>
            </ul>

            <h4>4.2 Spørgsmåls-effektstørrelse (effect size)</h4>
            <p>
                For hvert af de 25 spørgsmål beregner vi, hvor meget brugerens svar på netop dét spørgsmål
                påvirker den endelige match-procent. Metoden er som følger:
            </p>
            <ol>
                <li>Gruppér alle kørsler efter deres svar på spørgsmål Q<sub>i</sub> (4 grupper: 0, 1, 2, 3).</li>
                <li>Beregn gennemsnitlig match-% for top-1-kandidaten i hver gruppe.</li>
                <li>Effect size = max(gennemsnit) − min(gennemsnit).</li>
            </ol>
            <p>
                Spørgsmål med høj effektstørrelse er dem, hvor kandidaternes svar er mest spredte —
                dvs. de politisk mest "polariserende" emner.
            </p>

            <h4>4.3 Rød/blå blok-analyse</h4>
            <p>
                Vi klassificerer partierne i to politiske blokke:
            </p>
            <ul>
                <li><strong style="color: #ef4444;">Rød blok:</strong> A, F, Ø, B, Å</li>
                <li><strong style="color: #60a5fa;">Blå blok:</strong> V, I, C, Æ, O, Borgernes Parti</li>
                <li><strong style="color: #475569;">Andet:</strong> M</li>
            </ul>

            <h4>4.4 Parti-par-korrelation</h4>
            <p>
                Vi analyserer, hvilke partier der oftest optræder som nummer 1 og nummer 2 i
                den samme testkørsel. Denne analyse afslører algoritmisk "nærhed" mellem partier og
                vises som en heatmap i dashboardet.
            </p>

            <h4>4.5 Kandidat-gaming-analyse</h4>
            <p>
                Vi undersøger, om individuelle kandidater er over-repræsenterede eller har
                besvaret testen strategisk ("gaming") ved at vælge svar, der minimerer den
                gennemsnitlige afstand til alle mulige brugersvar.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_phase_5():
    """Phase 5: Data Quality & Validation."""
    st.markdown("""
    <div class="method-step">
        <div class="info-card-text">
            <h4>Formål</h4>
            <p>
                At sikre, at vores datasæt er komplet, korrekt og repræsentativt, så analysens
                konklusioner er troværdige.
            </p>

            <h4>5.1 Kandidat-komplethed</h4>
            <p>
                Vi har manuelt verificeret vores datasæt mod DR's live platform. Af de 950
                scannede kandidat-ID'er fandt vi <strong>714 aktive kandidater</strong> med fuldstændige
                besvarelser. Specifikt identificerede vi, at mindst én kandidat (Jens Kier, ID 121) 
                blev fjernet fra platformen undervejs.
            </p>

            <h4>5.2 Svar-korrekthed</h4>
            <p>
                Vi har stikprøve-verificeret kandidaternes scrapede svar mod deres profiler. 
                Vores "progressive scroll extraction"-teknik matcher korrekt kandidat-svar 
                med spørgsmål ved at bruge DOM-positionen af markøren.
            </p>

            <h4>5.3 Algoritme-verifikation</h4>
            <p>
                Vi har verificeret DR's algoritme ved at genberegne match-procenter offline for
                over 10.000 scrapede resultater. Vores model reproducerer DR's match-procent i 
                alle tilfælde (±1 pp afrunding).
            </p>

            <h4>5.4 Simulerings-reproducerbarhed</h4>
            <p>
                Alle LHS-simulationer bruger et deterministisk seed (seed=42), hvilket sikrer, 
                at resultaterne er fuldt reproducerbare.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_phase_6():
    """Phase 6: Dashboard Pipeline."""
    st.markdown("""
    <div class="method-step">
        <div class="info-card-text">
            <h4>Formål</h4>
            <p>
                At gøre analyseresultaterne tilgængelige i et interaktivt dashboard, der kan
                køres på servere med begrænsede ressourcer.
            </p>

            <h4>6.1 Pre-aggregerings-pipeline</h4>
            <p>
                Den rå simulationsdata fylder ca. 1 GB. For at sikre hurtig indlæsning kører vi 
                et pre-aggregerings-script, der gemmer alle nødvendige statistikker som små 
                JSON-filer i <code>data/precomputed/</code>.
            </p>

            <h4>6.2 Teknologisk stack</h4>
            <ul>
                <li><strong>Dashboard:</strong> Streamlit (Python) + Plotly</li>
                <li><strong>Scraping:</strong> Playwright (Python)</li>
                <li><strong>Simulation:</strong> NumPy + SciPy (LHS)</li>
                <li><strong>Database:</strong> SQLite (history.db)</li>
            </ul>

            <h4>6.3 Dataflow</h4>
            <p>Det samlede dataflow kan opsummeres i denne kæde:</p>
            <div style="text-align: center; font-family: 'Courier New', monospace; background: var(--bg-elevated); padding: 15px; border-radius: 8px;">
                DR Kandidattest → Scraper → history.db → LHS Simulation → results.csv → Pipeline → JSON → Dashboard
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# Answer Distribution Chart
# ═════════════════════════════════════════════════════════════════════════════

def _render_answer_distribution(answers_df: pd.DataFrame, questions_dict: dict):
    """Render horizontal stacked bar chart of answer distribution per question."""
    if answers_df is None or answers_df.empty:
        st.info("Ingen simulationsdata tilgængelig til at vise datagrundlaget endnu.")
        return

    st.subheader("📊 Svarfordeling pr. spørgsmål (Baseret på scrapede data)")
    st.caption(
        "Herunder kan du se, hvordan svarfordelingen var på de indledende 10.000 ægte "
        "tests, som blev formuleret og trukket direkte fra DR's servere for at knække algoritmen."
    )

    # Filter out if data is missing or unexpected
    required_cols = [f"Q{i+1}" for i in range(25)]
    if not all(col in answers_df.columns for col in required_cols):
        st.warning("Dataformatet er ugyldigt for svarfordeling.")
        return

    melted = answers_df.melt(
        id_vars=["run_id"],
        value_vars=required_cols,
        var_name="Question_Raw",
        value_name="Answer_Val",
    )
    melted["Svar"] = melted["Answer_Val"].map(ANSWER_LABELS)
    melted["Q_Num"] = melted["Question_Raw"].str.replace("Q", "").astype(int)
    melted["Spørgsmål"] = melted["Q_Num"].apply(
        lambda x: f"{x}. {questions_dict.get(x, f'Spørgsmål {x}')}"
    )

    dist_counts = (
        melted.groupby(["Spørgsmål", "Q_Num", "Svar"])
        .size().reset_index(name="Antal")
        .sort_values("Q_Num")
    )

    fig = px.bar(
        dist_counts, x="Antal", y="Spørgsmål",
        color="Svar", color_discrete_map=ANSWER_COLORS,
        orientation="h",
        title="Total fordeling af svar pr. spørgsmål",
        category_orders={"Svar": ["Uenig", "Lidt uenig", "Lidt enig", "Enig"]},
    )
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>%{x} person(er) svarede <b>%{fullData.name}</b><extra></extra>"
    )
    fig.update_layout(**base_layout(
        barmode="stack", height=900,
        margin=dict(l=0, r=0, t=50, b=0),
        xaxis=dict(title="", showticklabels=False),
        yaxis=dict(autorange="reversed", title="", showgrid=False),
        legend_title_text="",
    ))
    st.plotly_chart(fig, use_container_width=True, key="methodology_answer_dist")
