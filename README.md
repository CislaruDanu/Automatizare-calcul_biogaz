# Automatizare calcul biogaz

Aplicație Python pentru automatizarea calculelor producției de biogaz și a performanței cogenerării, pe baza datelor zilnice din fișiere CSV.  
Programul calculează indicatorii energetici pentru fiecare zi, exportă rezultatele în format **XLSX/CSV** și generează grafice cu ajutorul bibliotecii **Matplotlib**.

---

## Scopul proiectului

Acest proiect a fost realizat pentru:
- reducerea timpului necesar calculelor manuale;
- eliminarea erorilor de transcriere și de calcul;
- standardizarea procesului de analiză zilnică;
- vizualizarea evoluției parametrilor principali (Q, randament instalație biogaz, randament cogenerare).

Aplicația este utilizată în contextul analizei datelor de exploatare pentru o instalație de biogaz asociată unei fabrici de zahăr.

---

## Funcționalități

- citire automată date din fișier CSV;
- detectare automată delimitator (`;` sau `,`);
- mapare robustă a antetelor (acceptă variații de denumiri coloane);
- validare valori de intrare și fallback pe valori implicite;
- calcul automat pentru fiecare zi de operare;
- export rezultate în:
  - `.xlsx` (implicit)
  - `.csv`
- afișare rezultate în terminal (format lizibil);
- generare automată 3 grafice `.png`:
  1. `Q` [kWh/zi]
  2. `eta_B` (randamentul instalației de biogaz)
  3. `eta_cog` (randamentul global al cogenerării)
- mod de monitorizare (`--watch`) pentru recalcul automat la modificarea fișierului de intrare.

---

## Structura generală a calculelor

Pe baza datelor de intrare, scriptul aplică relațiile de calcul definite în lucrare pentru:
- coeficientul specific de producere biogaz `k`;
- volumul zilnic de biogaz;
- volumul real și volumul direcționat către cogenerare;
- energia disponibilă `Q`;
- energia electrică `E`;
- puterea combustibilului echivalent;
- randamentul global al cogenerării `eta_cog`.

---

## Cerințe software

- Python 3.9+ (recomandat 3.10/3.11)
- pachete Python:
  - `matplotlib`
  - `openpyxl`

Instalare dependențe:

```bash
pip install matplotlib openpyxl
```

---

## Fișierul de intrare (CSV)

### Coloane minime necesare
- `m_kg_zi` (obligatoriu) – masa zilnică de substrat [kg/zi]

### Coloane opționale (dacă lipsesc, se folosesc valorile implicite)
- `data`
- `x_su`
- `x_co`
- `V_bo`
- `eta_B`
- `frac_cogen`
- `x_CH4`
- `q_CH4`
- `C`

Programul acceptă și variante similare de antet (ex.: `masa`, `mkgzi`, `xch4`, etc.).

### Exemplu CSV
```csv
data;m_kg_zi;x_su;x_co;V_bo;eta_B;frac_cogen;x_CH4;q_CH4;C
2026-02-27;120000;0.23;0.95;0.66;0.819;0.3333;0.416;9.94;0.75
2026-02-28;118500;0.23;0.95;0.66;0.819;0.3333;0.416;9.94;0.75
```

---

## Rulare

### 1) Rulare simplă
```bash
python calcul_biogaz.py --input Data.csv --output rezultate_biogaz.xlsx
```

### 2) Cu export CSV
```bash
python calcul_biogaz.py -i Data.csv -o rezultate_biogaz.csv
```

### 3) Detectare automată fișier intrare
Dacă nu specifici `--input`, scriptul încearcă automat:
- `Data.csv`
- `data.csv`
- `date_intrare_exemplu.csv`
- sau un singur `.csv` găsit în directorul curent.

```bash
python calcul_biogaz.py
```

### 4) Mod monitorizare (recalcul automat)
```bash
python calcul_biogaz.py -i Data.csv -o rezultate_biogaz.xlsx --watch --interval 2
```

---

## Fișiere generate

La rulare, aplicația poate genera:
- `rezultate_biogaz.xlsx` sau `rezultate_biogaz.csv`
- `grafic_Q_kWh_zi.png`
- `grafic_eta_B.png`
- `grafic_eta_cog.png`

Dacă fișierul de ieșire este deschis și nu poate fi suprascris, se creează automat un fișier nou cu sufixul `_nou`.

---

## Interpretarea rezultatelor

- **Q [kWh/zi]** indică energia obținută din biogazul direcționat către cogenerare.
- **eta_B** reflectă randamentul global al instalației de producere a biogazului.
- **eta_cog** reflectă randamentul global al conversiei energetice în cogenerare.

Analiza combinată a valorilor tabelare și a graficelor permite observarea trendurilor zilnice, detectarea abaterilor și evaluarea stabilității funcționării.

---

## Legătura cu lucrarea de licență

Acest repository conține implementarea practică pentru subcapitolul de automatizare al lucrării de licență (Producerea biogazului din reziduuri ale industriei zahărului: analiză aplicată la o Fabrică de Zahăr), realizată de către Cîșlaru Danu (Bacău 2026).  
În lucrare sunt prezentate principiile de calcul și interpretarea rezultatelor, iar aici este disponibil codul sursă complet utilizat pentru prelucrarea automată a datelor.

---

## Autor

**Danu Cislaru**  
Repository: `CislaruDanu/Automatizare-calcul_biogaz`
