"""
database.py
Penyimpanan "database" parameter atmosfer hasil analisis ke file CSV lokal.
Satu baris = satu tanggal observasi. Jika tanggal yang sama sudah ada,
data tidak akan disimpan ulang (sesuai permintaan pengguna).
"""

from __future__ import annotations

import os
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "database_parameter_atmosfer.csv")

DB_COLUMNS = [
    "tanggal", "stasiun", "indeks_wmo", "sonde_id", "waktu_utc",
    "lcl_hpa", "ccl_hpa", "lfc_hpa", "el_hpa",
    "cape_sb", "cape_ml", "cape_mu", "cin_sb", "cin_ml", "cin_mu",
    "k_index", "lifted_index", "showalter_index", "total_totals", "sweat_index", "dcape",
    "estimasi_tropopause_primer_km", "tropopause_primer_km", "tropopause_sekunder_km",
    "rh_mean_1000_700", "dpd_mean_1000_700", "surface_mixing_ratio", "pwat_mm",
    "wind_shear_kt", "windex",
]


def _ensure_dir():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def load_database() -> pd.DataFrame:
    _ensure_dir()
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(columns=DB_COLUMNS)
    return pd.read_csv(DB_PATH)


def date_exists(tanggal_iso: str) -> bool:
    df = load_database()
    if df.empty:
        return False
    return tanggal_iso in df["tanggal"].astype(str).tolist()


def build_row(analysis: dict) -> dict:
    h = analysis["header"]
    conv = analysis["convective_levels"]
    stab = analysis["stability_indices"]
    tropo = analysis["tropopause"]
    humid = analysis["humidity"]
    return {
        "tanggal": h.get("tanggal_iso"),
        "stasiun": h.get("stasiun"),
        "indeks_wmo": h.get("indeks_wmo"),
        "sonde_id": h.get("sonde_id"),
        "waktu_utc": h.get("waktu_utc"),
        "lcl_hpa": conv.get("lcl_hpa"), "ccl_hpa": conv.get("ccl_hpa"),
        "lfc_hpa": conv.get("lfc_hpa"), "el_hpa": conv.get("el_hpa"),
        "cape_sb": stab.get("cape_sb"), "cape_ml": stab.get("cape_ml"), "cape_mu": stab.get("cape_mu"),
        "cin_sb": stab.get("cin_sb"), "cin_ml": stab.get("cin_ml"), "cin_mu": stab.get("cin_mu"),
        "k_index": stab.get("k_index"), "lifted_index": stab.get("lifted_index"),
        "showalter_index": stab.get("showalter_index"), "total_totals": stab.get("total_totals"),
        "sweat_index": stab.get("sweat_index"), "dcape": stab.get("dcape"),
        "estimasi_tropopause_primer_km": tropo.get("estimasi_tropopause_primer_km"),
        "tropopause_primer_km": tropo.get("tropopause_primer_km"),
        "tropopause_sekunder_km": tropo.get("tropopause_sekunder_km"),
        "rh_mean_1000_700": humid.get("rh_mean_1000_700"),
        "dpd_mean_1000_700": humid.get("dpd_mean_1000_700"),
        "surface_mixing_ratio": humid.get("surface_mixing_ratio"),
        "pwat_mm": h.get("pwat_mm"),
        "wind_shear_kt": analysis.get("wind_shear_kt"),
        "windex": analysis.get("windex"),
    }


def save_analysis(analysis: dict) -> tuple:
    """Simpan satu baris hasil analisis. Mengembalikan (berhasil: bool, pesan: str)."""
    tanggal_iso = analysis["header"].get("tanggal_iso")
    if not tanggal_iso:
        return False, "Tanggal observasi tidak terbaca dari file, data tidak disimpan."
    if date_exists(tanggal_iso):
        return False, f"Data untuk tanggal {tanggal_iso} sudah ada di database, tidak disimpan ulang."
    df = load_database()
    row = build_row(analysis)
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df = df.sort_values("tanggal").reset_index(drop=True)
    _ensure_dir()
    df.to_csv(DB_PATH, index=False)
    return True, f"Data tanggal {tanggal_iso} berhasil disimpan ke database."


def delete_date(tanggal_iso: str):
    df = load_database()
    df = df[df["tanggal"].astype(str) != str(tanggal_iso)]
    _ensure_dir()
    df.to_csv(DB_PATH, index=False)