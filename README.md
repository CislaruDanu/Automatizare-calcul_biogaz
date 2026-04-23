# Calculator biogaz (capitol 4)

Acest script calculeaza automat productia de biogaz si indicatorii energetici zilnici dintr-un fisier CSV.

## 1) Cerinte

- Python 3.9+

Nu sunt necesare librarii externe.

## 2) Fisierul de intrare (CSV)

Coloana obligatorie:
- `m_kg_zi` = masa zilnica de substrat [kg/zi]

Coloane optionale (daca lipsesc, se folosesc valorile implicite):
- `data` (text)
- `x_su` (implicit 0.23)
- `x_co` (implicit 0.95)
- `V_bo` (implicit 0.66)
- `eta_B` (implicit 0.819)
- `frac_cogen` (implicit 1/3)
- `x_CH4` (implicit 0.416)
- `q_CH4` (implicit 9.94)
- `C` (implicit 0.75)

Scriptul accepta delimitator `;` sau `,` si valori numerice cu punct sau virgula zecimala.

## 3) Rulare

```powershell
python biogaz_calculator.py --input date_intrare_exemplu.csv --output rezultate_biogaz.csv
```

## 4) Rezultate generate

In fisierul de iesire se calculeaza:
- `k_m3_per_kg`
- `V_B_m3_zi`
- `V_B_real_m3_zi`
- `V_B_cogen_m3_zi`
- `Q_kWh_zi`
- `E_kWh_zi`
- `P_combustibil_kWh_zi`
- `eta_cog`

## 5) Observatii

Formula `P_combustibil` este implementata conform relatiilor prezentate in textul capitolului:
`P_combustibil = V_B_cogen * q_CH4`.
