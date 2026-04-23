#!/usr/bin/env python3
"""Calcul automat pentru producerea biogazului si valorificarea energetica.
"""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path
from typing import Dict, Iterable, List

import matplotlib.pyplot as plt
from openpyxl import Workbook

# Parametri impliciti (pot fi suprascrisi prin coloane in CSV)
DEFAULTS = {
    "x_su": 0.23,
    "x_co": 0.95,
    "V_bo": 0.66,
    "eta_B": 0.819,
    "frac_cogen": 1.0 / 3.0,
    "x_CH4": 0.416,
    "q_CH4": 9.94,
    "C": 0.75,
}

HEADER_ALIASES = {
    "data": "data",
    "date": "data",
    "zi": "data",
    "m_kg_zi": "m_kg_zi",
    "mkgzi": "m_kg_zi",
    "masa": "m_kg_zi",
    "masakgzi": "m_kg_zi",
    "masakg": "m_kg_zi",
    "x_su": "x_su",
    "xsu": "x_su",
    "xcu": "x_su",
    "x_co": "x_co",
    "xco": "x_co",
    "v_bo": "V_bo",
    "vbo": "V_bo",
    "eta_b": "eta_B",
    "etab": "eta_B",
    "hb": "eta_B",
    "h_b": "eta_B",
    "frac_cogen": "frac_cogen",
    "fraccogen": "frac_cogen",
    "x_ch4": "x_CH4",
    "xch4": "x_CH4",
    "q_ch4": "q_CH4",
    "qch4": "q_CH4",
    "c": "C",
}


def normalize_header(name: str) -> str:
    """Normalizeaza antetul pentru mapare robusta a coloanelor."""
    return "".join(ch for ch in name.strip().lower() if ch.isalnum())


def normalize_input_row(row: Dict[str, str]) -> Dict[str, str]:
    """Mapeaza anteturile CSV la denumirile interne ale scriptului."""
    normalized: Dict[str, str] = {}
    for key, value in row.items():
        mapped_key = HEADER_ALIASES.get(normalize_header(key))
        if mapped_key:
            normalized[mapped_key] = value
    return normalized


def parse_float(value: str) -> float:
    """Convertește text in float si accepta atat punct cat si virgula zecimala."""
    cleaned = value.strip().replace(" ", "")
    if not cleaned:
        raise ValueError("Valoare numerica lipsa")
    return float(cleaned.replace(",", "."))


def detect_delimiter(sample: str) -> str:
    """Detecteaza delimitatorul CSV folosind Sniffer; fallback pe ';'."""
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;")
        return dialect.delimiter
    except csv.Error:
        return ";"


def parse_row(
    row: Dict[str, str],
    row_index: int,
) -> Dict[str, float]:
    """Parseaza si valideaza o linie de intrare."""
    if "m_kg_zi" not in row:
        raise KeyError(
            "Coloana obligatorie 'm_kg_zi' lipseste din fisierul de intrare."
        )

    parsed = {}
    parsed["m_kg_zi"] = parse_float(row["m_kg_zi"])

    for key, default_value in DEFAULTS.items():
        raw = row.get(key, "")
        if raw.strip():
            parsed[key] = parse_float(raw)
        else:
            parsed[key] = default_value

    # Validari simple pentru a evita rezultate nerealiste din date introduse gresit.
    if not (0.0 < parsed["x_CH4"] <= 1.0):
        print(
            f"Avertizare [rand {row_index}]: x_CH4={parsed['x_CH4']} invalid, "
            f"se foloseste valoarea implicita {DEFAULTS['x_CH4']}."
        )
        parsed["x_CH4"] = DEFAULTS["x_CH4"]
    if not (5.0 <= parsed["q_CH4"] <= 15.0):
        print(
            f"Avertizare [rand {row_index}]: q_CH4={parsed['q_CH4']} invalid, "
            f"se foloseste valoarea implicita {DEFAULTS['q_CH4']}."
        )
        parsed["q_CH4"] = DEFAULTS["q_CH4"]

    if not (0.0 < parsed["eta_B"] <= 1.0):
        print(
            f"Avertizare [rand {row_index}]: eta_B={parsed['eta_B']} invalid, "
            f"se foloseste valoarea implicita {DEFAULTS['eta_B']}."
        )
        parsed["eta_B"] = DEFAULTS["eta_B"]

    if not (0.0 < parsed["frac_cogen"] <= 1.0):
        print(
            f"Avertizare [rand {row_index}]: frac_cogen={parsed['frac_cogen']} invalid, "
            f"se foloseste valoarea implicita {DEFAULTS['frac_cogen']}."
        )
        parsed["frac_cogen"] = DEFAULTS["frac_cogen"]

    if not (0.0 < parsed["C"] <= 1.0):
        print(
            f"Avertizare [rand {row_index}]: C={parsed['C']} invalid, "
            f"se foloseste valoarea implicita {DEFAULTS['C']}."
        )
        parsed["C"] = DEFAULTS["C"]

    return parsed


def calculate(values: Dict[str, float]) -> Dict[str, float]:
    """Aplica relatiile de calcul pentru o zi de operare."""
    m = values["m_kg_zi"]
    x_su = values["x_su"]
    x_co = values["x_co"]
    V_bo = values["V_bo"]
    eta_B = values["eta_B"]
    frac_cogen = values["frac_cogen"]
    x_CH4 = values["x_CH4"]
    q_CH4 = values["q_CH4"]
    C = values["C"]

    # (4.3)
    k = x_su * x_co * V_bo

    # (4.1)/(4.4)
    V_B = m * k

    # (4.5)
    V_B_real = V_B * eta_B

    # (4.6)
    V_B_cogen = V_B_real * frac_cogen

    # (4.8)/(4.9)
    Q = V_B_cogen * x_CH4 * q_CH4

    # (4.11)/(4.12)
    E = Q * C

    # (4.14)/(4.15) 
    P_combustibil = V_B_cogen * q_CH4

    # (4.13)
    eta_cog = (E + Q) / P_combustibil if P_combustibil else 0.0

    return {
        "k_m3_per_kg": k,
        "V_B_m3_zi": V_B,
        "V_B_real_m3_zi": V_B_real,
        "V_B_cogen_m3_zi": V_B_cogen,
        "Q_kWh_zi": Q,
        "E_kWh_zi": E,
        "P_combustibil_kWh_zi": P_combustibil,
        "eta_cog": eta_cog,
    }


OUTPUT_COLUMNS = [
    ("data", "Data"),
    ("m_kg_zi", "m,kg/zi"),
    ("V_B_cogen_m3_zi", "V_(B,cogen),m3/zi"),
    ("Q_kWh_zi", "Q,kWh/zi"),
    ("E_kWh_zi", "E,kWh/zi"),
    ("P_combustibil_kWh_zi", "P_combustibil,kWh/zi"),
    ("eta_B", "η_B"),
    ("k_m3_per_kg", "k"),
    ("x_CH4", "x_CH4"),
    ("q_CH4", "q_(CH_4)"),
    ("C", "C"),
    ("eta_cog", "η_cog"),
]


def read_input(path: Path) -> List[Dict[str, str]]:
    """Citeste toate liniile din CSV."""
    sample = path.read_text(encoding="utf-8-sig")
    delimiter = detect_delimiter(sample[:2048])
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        return [normalize_input_row(row) for row in reader]


def build_output_rows(input_rows: List[Dict[str, str]]) -> List[Dict[str, object]]:
    """Genereaza randurile de iesire cu intrari + rezultate calculate."""
    output_rows: List[Dict[str, object]] = []
    for idx, row in enumerate(input_rows, start=1):
        if not any(str(value).strip() for value in row.values()):
            continue

        values = parse_row(row, idx)
        result = calculate(values)

        output_row: Dict[str, object] = {
            "data": row.get("data", "").strip(),
            "m_kg_zi": values["m_kg_zi"],
            "V_B_cogen_m3_zi": result["V_B_cogen_m3_zi"],
            "Q_kWh_zi": result["Q_kWh_zi"],
            "E_kWh_zi": result["E_kWh_zi"],
            "P_combustibil_kWh_zi": result["P_combustibil_kWh_zi"],
            "eta_B": values["eta_B"],
            "k_m3_per_kg": result["k_m3_per_kg"],
            "x_CH4": values["x_CH4"],
            "q_CH4": values["q_CH4"],
            "C": values["C"],
            "eta_cog": result["eta_cog"],
        }
        output_rows.append(output_row)

    return output_rows


def write_output(path: Path, rows: Iterable[Dict[str, object]]) -> Path:
    """Scrie rezultatele in CSV sau XLSX si returneaza calea finala salvata."""
    rows = list(rows)
    if not rows:
        raise ValueError("Fisierul de intrare nu contine date.")

    fieldnames = [display_name for _, display_name in OUTPUT_COLUMNS]
    if path.suffix.lower() == ".xlsx":
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Biogaz"
        worksheet.append(fieldnames)

        for row in rows:
            formatted_row = []
            for source_key, _ in OUTPUT_COLUMNS:
                value = row.get(source_key, "")
                if isinstance(value, float):
                    formatted_row.append(round(value, 6))
                else:
                    formatted_row.append(value)
            worksheet.append(formatted_row)
        try:
            workbook.save(path)
            return path
        except PermissionError:
            fallback_path = path.with_name(f"{path.stem}_nou{path.suffix}")
            workbook.save(fallback_path)
            print(
                "Avertizare: fisierul de iesire era deschis si nu a putut fi suprascris. "
                f"Rezultatele au fost salvate in: {fallback_path}"
            )
            return fallback_path
    else:
        try:
            with path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
                writer.writeheader()
                for row in rows:
                    formatted = {}
                    for source_key, display_name in OUTPUT_COLUMNS:
                        value = row.get(source_key, "")
                        if isinstance(value, float):
                            formatted[display_name] = f"{value:.6f}"
                        else:
                            formatted[display_name] = value
                    writer.writerow(formatted)
            return path
        except PermissionError:
            fallback_path = path.with_name(f"{path.stem}_nou{path.suffix}")
            with fallback_path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
                writer.writeheader()
                for row in rows:
                    formatted = {}
                    for source_key, display_name in OUTPUT_COLUMNS:
                        value = row.get(source_key, "")
                        if isinstance(value, float):
                            formatted[display_name] = f"{value:.6f}"
                        else:
                            formatted[display_name] = value
                    writer.writerow(formatted)
            print(
                "Avertizare: fisierul de iesire era deschis si nu a putut fi suprascris. "
                f"Rezultatele au fost salvate in: {fallback_path}"
            )
            return fallback_path


def print_pretty_results(rows: List[Dict[str, object]]) -> None:
    """Afiseaza rezultatele intr-un format usor de citit, pe coloane separate."""
    ordered_fields = [
        "V_B_cogen_m3_zi",
        "Q_kWh_zi",
        "E_kWh_zi",
        "P_combustibil_kWh_zi",
        "eta_cog",
    ]
    pretty_labels = {
        "V_B_cogen_m3_zi": "V_(B,cogen) [m3/zi]",
        "Q_kWh_zi": "Q [kWh/zi]",
        "E_kWh_zi": "E [kWh/zi]",
        "P_combustibil_kWh_zi": "P_combustibil [kWh/zi]",
        "eta_cog": "eta_cog [-]",
    }

    print("\n" + "=" * 72)
    print("REZULTATE CALCUL BIOGAZ")
    print("=" * 72)

    for i, row in enumerate(rows, start=1):
        label = row.get("data", f"Ziua {i}")
        print(f"\n[{label}]")
        print("-" * 72)
        for field in ordered_fields:
            value = row.get(field, "-")
            if isinstance(value, float):
                value_str = f"{value:.6f}"
            else:
                value_str = str(value)
            display_name = pretty_labels.get(field, field)
            print(f"{display_name:<28}: {value_str}")

    print("=" * 72)


def plot_results(rows: List[Dict[str, object]], output_dir: Path) -> None:
    """Genereaza si afiseaza graficele pentru Q, eta_B si eta_cog."""
    def soften_y_axis(ax, values: List[float], widen_factor: float = 2.8) -> None:
        """Largeste intervalul pe axa Y pentru o vizualizare mai putin abrupta."""
        if not values:
            return

        vmin = min(values)
        vmax = max(values)
        if vmin == vmax:
            base = abs(vmin) if vmin != 0 else 1.0
            half_span = base * 0.15
        else:
            half_span = ((vmax - vmin) * widen_factor) / 2.0

        center = (vmin + vmax) / 2.0
        ax.set_ylim(center - half_span, center + half_span)

    labels = []
    q_values = []
    eta_b_values = []
    eta_cog_values = []

    for i, row in enumerate(rows, start=1):
        label = str(row.get("data") or f"Ziua {i}")
        labels.append(label)
        q_values.append(float(row.get("Q_kWh_zi", 0.0)))
        eta_b_values.append(float(row.get("eta_B", 0.0)))
        eta_cog_values.append(float(row.get("eta_cog", 0.0)))

    output_dir.mkdir(parents=True, exist_ok=True)

    # Grafic 1: Q
    fig1, ax1 = plt.subplots(figsize=(12, 4))
    ax1.plot(labels, q_values, marker="o", linewidth=2, color="#1f77b4")
    ax1.set_title("Q - energia obtinuta din biogaz [kWh/zi]")
    ax1.set_xlabel("Data")
    ax1.set_ylabel("Q [kWh/zi]")
    soften_y_axis(ax1, q_values)
    ax1.grid(True, linestyle="--", alpha=0.4)
    ax1.tick_params(axis="x", rotation=45)
    fig1.tight_layout()
    fig1.savefig(output_dir / "grafic_Q_kWh_zi.png", dpi=150)

    # Grafic 2: eta_B
    fig2, ax2 = plt.subplots(figsize=(12, 4))
    ax2.plot(labels, eta_b_values, marker="o", linewidth=2, color="#2ca02c")
    ax2.set_title("Randamentul global al sistemului de productie a biogazului (ηB)")
    ax2.set_xlabel("Data")
    ax2.set_ylabel("ηB")
    soften_y_axis(ax2, eta_b_values)
    ax2.grid(True, linestyle="--", alpha=0.4)
    ax2.tick_params(axis="x", rotation=45)
    fig2.tight_layout()
    fig2.savefig(output_dir / "grafic_eta_B.png", dpi=150)

    # Grafic 3: eta_cog
    fig3, ax3 = plt.subplots(figsize=(12, 4))
    ax3.plot(labels, eta_cog_values, marker="o", linewidth=2, color="#d62728")
    ax3.set_title("Randamentul global al cogenerarii (ηcog)")
    ax3.set_xlabel("Data")
    ax3.set_ylabel("ηcog")
    soften_y_axis(ax3, eta_cog_values)
    ax3.grid(True, linestyle="--", alpha=0.4)
    ax3.tick_params(axis="x", rotation=45)
    fig3.tight_layout()
    fig3.savefig(output_dir / "grafic_eta_cog.png", dpi=150)

    # Afisare grafice pe ecran
    plt.show()


def auto_detect_input_file() -> Path:
    """Alege automat fisierul de intrare cand --input nu este furnizat."""
    for preferred_name in ["Data.csv", "data.csv", "date_intrare_exemplu.csv"]:
        preferred = Path(preferred_name)
        if preferred.exists():
            return preferred

    csv_files = sorted(Path.cwd().glob("*.csv"))
    filtered = [p for p in csv_files if p.name.lower() != "rezultate_biogaz.csv"]
    if len(filtered) == 1:
        return filtered[0]

    if len(filtered) > 1:
        names = ", ".join(p.name for p in filtered)
        raise ValueError(
            "Sunt mai multe fisiere CSV disponibile. "
            f"Specifica explicit --input. Fisiere detectate: {names}"
        )

    raise FileNotFoundError(
        "Nu a fost gasit niciun fisier CSV de intrare in folderul curent. "
        "Adauga un fisier CSV sau foloseste --input <fisier.csv>."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Calculeaza productia de biogaz si indicatorii energetici zilnici "
            "pe baza unui fisier CSV."
        )
    )
    parser.add_argument(
        "--input",
        "-i",
        required=False,
        help="Calea catre CSV-ul de intrare (optional; daca lipseste, se auto-detecteaza)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="rezultate_biogaz.xlsx",
        help="Calea fisierului de iesire (implicit: rezultate_biogaz.xlsx)",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Monitorizeaza fisierul de intrare si recalculeaza automat la modificari",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Intervalul de verificare in secunde pentru --watch (implicit: 2)",
    )
    return parser.parse_args()


def run_once(input_path: Path, output_path: Path) -> None:
    """Ruleaza un ciclu complet de citire, calcul, scriere si afisare."""
    input_rows = read_input(input_path)
    output_rows = build_output_rows(input_rows)
    saved_path = write_output(output_path, output_rows)
    print_pretty_results(output_rows)
    plot_results(output_rows, output_path.parent)
    print(f"Calcul finalizat. Rezultatele au fost salvate in: {saved_path}")


def main() -> None:
    args = parse_args()
    input_path = Path(args.input) if args.input else auto_detect_input_file()
    output_path = Path(args.output)

    if args.watch:
        print(f"Monitorizare activa pentru: {input_path}")
        print("Apasa Ctrl+C pentru oprire.\n")
        last_mtime = None
        try:
            while True:
                if input_path.exists():
                    current_mtime = input_path.stat().st_mtime
                    if last_mtime is None or current_mtime != last_mtime:
                        print(f"\nModificare detectata in {input_path}. Recalculez...")
                        run_once(input_path, output_path)
                        last_mtime = current_mtime
                else:
                    print(f"Fisierul {input_path} nu exista inca. Astept...")
                time.sleep(max(args.interval, 0.5))
        except KeyboardInterrupt:
            print("\nMonitorizarea a fost oprita de utilizator.")
    else:
        if not input_path.exists():
            raise FileNotFoundError(f"Fisierul de intrare nu exista: {input_path}")
        run_once(input_path, output_path)


if __name__ == "__main__":
    main()
