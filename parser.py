"""
parser.py
Parser untuk file radiosonde format .CRA (Eoscan / Vaisala style report).

Struktur file (blok dipisah baris kosong):
    Header umum (Sonde ID, Date, Time, WMO Station index, Country,
    Station name, Position)
    Info penerbangan balon (Start, Vz ..., Duration flight, at .. hPa,
    at .. m, to .. km, Burst, Termination reason)
    Surface data (Ground pressure, Ground temperature, dst)
    Significants points: <tabel>
    Standard levels: <tabel>
    Particular levels: <tabel>
    Additional, regional and national levels: <tabel>
    Standards Wind Altitudes points: <tabel> (tanpa kolom waktu/indikator)

Semua tabel level memakai kolom (tab-separated):
    Time  Alt  P(hPa)  T(C)  DP(C)  RH(%)  WF(kts)  WD(deg)  ind.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

LEVEL_COLUMNS = [
    "waktu_terbang", "ketinggian_m", "tekanan_hpa", "suhu_c",
    "titik_embun_c", "kelembapan_rh", "kecepatan_angin_kt",
    "arah_angin_deg", "indikator",
]

SECTION_HEADERS = {
    "Significants points:": "significant_points",
    "Standard levels:": "standard_levels",
    "Particular levels:": "particular_points",
    "Additional, regional and national levels:": "additional_levels",
    "Standards Wind Altitudes points:": "wind_altitude_points",
}


def _clean_lines(raw: str) -> list:
    return [ln.rstrip("\r\n") for ln in raw.split("\n")]


def _parse_ddmm(token: str) -> Optional[float]:
    """Parse token seperti 7°043.140'S menjadi desimal derajat (+N/E, -S/W)."""
    m = re.match(r"(\d+)\xb0(\d+\.\d+)'?([NSEW])", token)
    if not m:
        m = re.match(r"(\d+)\xb0(\d+\.\d+)'?([NSEW])", token.replace("\u00b0", "\xb0"))
    if not m:
        return None
    deg, minute, hemi = m.groups()
    val = float(deg) + float(minute) / 60.0
    if hemi in ("S", "W"):
        val = -val
    return val


def _to_float(token: str) -> Optional[float]:
    token = token.strip()
    if token in ("", "--", "-"):
        return None
    try:
        return float(token)
    except ValueError:
        return None


@dataclass
class RadiosondeData:
    tanggal: Optional[str] = None
    waktu_utc: Optional[str] = None
    stasiun: Optional[str] = None
    indeks_wmo: Optional[str] = None
    sonde_id: Optional[str] = None
    posisi_lat: Optional[float] = None
    posisi_lon: Optional[float] = None
    posisi_text: Optional[str] = None

    waktu_mulai: Optional[str] = None
    durasi_penerbangan: Optional[str] = None
    waktu_burst: Optional[str] = None
    ketinggian_maksimum_m: Optional[float] = None
    tekanan_minimum_hpa: Optional[float] = None
    alasan_terminasi: Optional[str] = None

    tekanan_permukaan_hpa: Optional[float] = None
    suhu_permukaan_c: Optional[float] = None
    kelembapan_relatif_permukaan: Optional[float] = None
    kecepatan_angin_permukaan_kt: Optional[float] = None
    arah_angin_permukaan_deg: Optional[float] = None
    pwat_mm: Optional[float] = None

    tables: dict = field(default_factory=dict)  # name -> DataFrame

    @property
    def tanggal_iso(self) -> Optional[str]:
        """Tanggal dalam format YYYY-MM-DD, dipakai sebagai key unik database."""
        if not self.tanggal:
            return None
        try:
            d, m, y = self.tanggal.split("/")
            return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
        except Exception:
            return self.tanggal


def parse_cra_bytes(raw_bytes: bytes) -> RadiosondeData:
    """Parse isi file .CRA (bytes) menjadi RadiosondeData."""
    text = raw_bytes.decode("latin-1", errors="replace")
    lines = _clean_lines(text)

    data = RadiosondeData()
    i = 0
    n = len(lines)

    def peek():
        return lines[i] if i < n else ""

    # ---- header umum & info penerbangan & surface, sampai ketemu section tabel
    while i < n and peek().strip() not in SECTION_HEADERS:
        line = lines[i]
        if "\t" in line:
            key, _, val = line.partition("\t")
            key = key.strip()
            val = val.strip()
        else:
            key, val = line.strip(), ""

        if key.startswith("Sonde ID"):
            data.sonde_id = val
        elif key.startswith("Date"):
            data.tanggal = val
        elif key.startswith("Time"):
            data.waktu_utc = val
        elif key.startswith("WMO Station index"):
            data.indeks_wmo = val
        elif key.startswith("Station name"):
            data.stasiun = val
        elif key.startswith("Position"):
            data.posisi_text = val
            parts = val.split()
            if len(parts) >= 2:
                data.posisi_lat = _parse_ddmm(parts[0])
                data.posisi_lon = _parse_ddmm(parts[1])
        elif key.startswith("Start"):
            data.waktu_mulai = val
        elif key.startswith("Duration flight"):
            data.durasi_penerbangan = val
        elif key.strip() == "at" or key == "":
            pass  # ditangani lewat baris "\tat\t..." di bawah
        elif key.startswith("Burst"):
            data.waktu_burst = val
        elif key.startswith("Termination reason"):
            data.alasan_terminasi = val
        elif key.startswith("Ground pressure"):
            data.tekanan_permukaan_hpa = _to_float(val.replace("hPa", ""))
        elif key.startswith("Ground temperature"):
            data.suhu_permukaan_c = _to_float(val.replace("\xb0C", "").replace("C", ""))
        elif key.startswith("Ground humidity"):
            data.kelembapan_relatif_permukaan = _to_float(val.replace("%", ""))
        elif key.startswith("Ground Wind speed"):
            data.kecepatan_angin_permukaan_kt = _to_float(val.replace("kts", ""))
        elif key.startswith("Ground Wind direction"):
            data.arah_angin_permukaan_deg = _to_float(val.replace("\xb0", ""))
        elif key.startswith("Total precipitable water"):
            data.pwat_mm = _to_float(val.replace("mm", ""))

        # baris "\tat\t14.1 hPa" / "\tat\t28966 m" / "\tto\t18.870 km (Distance)"
        if line.strip().startswith("at\t") or "\tat\t" in line:
            sub = line.strip()
            if sub.startswith("at"):
                _, _, v = sub.partition("\t")
                v = v.strip()
                if "hPa" in v:
                    data.tekanan_minimum_hpa = _to_float(v.replace("hPa", ""))
                elif "m" in v:
                    data.ketinggian_maksimum_m = _to_float(v.replace("m", ""))
        i += 1

    # ---- parse tabel-tabel level
    while i < n:
        header = peek().strip()
        if header in SECTION_HEADERS:
            table_key = SECTION_HEADERS[header]
            i += 1
            # baris kolom (Time Alt P(hPa) ...)
            if i < n:
                i += 1  # lewati baris header kolom
            rows = []
            is_wind_alt = table_key == "wind_altitude_points"
            while i < n and lines[i].strip() != "":
                parts = [p.strip() for p in lines[i].split("\t")]
                if is_wind_alt:
                    # Alt P T DP RH WF WD (7 kolom, tanpa waktu & indikator)
                    if len(parts) >= 7:
                        rows.append({
                            "ketinggian_m": _to_float(parts[0]),
                            "tekanan_hpa": _to_float(parts[1]),
                            "suhu_c": _to_float(parts[2]),
                            "titik_embun_c": _to_float(parts[3]),
                            "kelembapan_rh": _to_float(parts[4]),
                            "kecepatan_angin_kt": _to_float(parts[5]),
                            "arah_angin_deg": _to_float(parts[6]),
                        })
                else:
                    if len(parts) >= 9:
                        rows.append({
                            "waktu_terbang": parts[0],
                            "ketinggian_m": _to_float(parts[1]),
                            "tekanan_hpa": _to_float(parts[2]),
                            "suhu_c": _to_float(parts[3]),
                            "titik_embun_c": _to_float(parts[4]),
                            "kelembapan_rh": _to_float(parts[5]),
                            "kecepatan_angin_kt": _to_float(parts[6]),
                            "arah_angin_deg": _to_float(parts[7]),
                            "indikator": parts[8],
                        })
                i += 1
            df = pd.DataFrame(rows)
            if not df.empty and "tekanan_hpa" in df.columns:
                df = df.sort_values("tekanan_hpa", ascending=False).reset_index(drop=True)
            data.tables[table_key] = df
        else:
            i += 1

    return data


def parse_cra_file(path: str) -> RadiosondeData:
    with open(path, "rb") as f:
        raw = f.read()
    return parse_cra_bytes(raw)