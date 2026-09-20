"""
calculation.py
Perhitungan seluruh parameter turunan (indeks stabilitas, level konveksi,
tropopause, lapse rate, karakteristik kelembapan & angin, wind shear,
windex, hodograph) dari data profil radiosonde.

Sebagian besar perhitungan memakai MetPy (metpy.calc) karena implementasi
mandiri untuk CAPE/CIN, LCL/LFC/EL, dan indeks-indeks stabilitas rawan
kesalahan numerik. Formula yang tidak tersedia di MetPy (mis. WINDEX)
diimplementasikan manual dan sumbernya dicatat pada docstring masing-masing
fungsi -- nilai ini sebaiknya tetap diverifikasi silang bila dipakai untuk
keputusan operasional.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import metpy.calc as mpcalc
from metpy.units import units

COMPASS_16 = [
    "Utara", "Utara-Timur Laut", "Timur Laut", "Timur-Timur Laut",
    "Timur", "Timur-Tenggara", "Tenggara", "Selatan-Tenggara",
    "Selatan", "Selatan-Barat Daya", "Barat Daya", "Barat-Barat Daya",
    "Barat", "Barat-Barat Laut", "Barat Laut", "Utara-Barat Laut",
]


def dominant_direction(dirs_deg: pd.Series) -> str:
    """Arah angin dominan berdasarkan distribusi frekuensi 16 sektor mata angin
    (analisis wind-rose sederhana: sektor dengan jumlah kemunculan terbanyak)."""
    d = dirs_deg.dropna().to_numpy()
    if len(d) == 0:
        return "-"
    sector = np.floor(((d % 360) + 11.25) / 22.5).astype(int) % 16
    counts = np.bincount(sector, minlength=16)
    return COMPASS_16[int(np.argmax(counts))]


def clean_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Bersihkan tabel level: butuh tekanan & suhu valid, urut tekanan menurun,
    dan tekanan harus unik & monoton turun (syarat MetPy)."""
    d = df.copy()
    d = d.dropna(subset=["tekanan_hpa", "suhu_c"])
    d = d.sort_values("tekanan_hpa", ascending=False)
    d = d.drop_duplicates(subset=["tekanan_hpa"], keep="first")
    d = d.reset_index(drop=True)
    return d


def basic_statistics(df: pd.DataFrame) -> dict:
    d = df
    return {
        "suhu_max": d["suhu_c"].max(), "suhu_min": d["suhu_c"].min(),
        "titik_embun_max": d["titik_embun_c"].max(), "titik_embun_min": d["titik_embun_c"].min(),
        "rh_max": d["kelembapan_rh"].max(), "rh_min": d["kelembapan_rh"].min(),
        "tekanan_max": d["tekanan_hpa"].max(), "tekanan_min": d["tekanan_hpa"].min(),
        "ketinggian_max": d["ketinggian_m"].max(), "ketinggian_min": d["ketinggian_m"].min(),
        "kecepatan_angin_max": d["kecepatan_angin_kt"].max(), "kecepatan_angin_min": d["kecepatan_angin_kt"].min(),
        "arah_angin_dominan": dominant_direction(d["arah_angin_deg"]),
    }


def _qty(df):
    p = df["tekanan_hpa"].to_numpy() * units.hPa
    T = df["suhu_c"].to_numpy() * units.degC
    Td = df["titik_embun_c"].to_numpy() * units.degC
    return p, T, Td


def convective_levels(df: pd.DataFrame) -> dict:
    """LCL, CCL, LFC, EL memakai parsel permukaan (surface-based)."""
    d = clean_profile(df)
    p, T, Td = _qty(d)
    out = {"lcl_hpa": None, "ccl_hpa": None, "lfc_hpa": None, "el_hpa": None}
    try:
        lcl_p, _ = mpcalc.lcl(p[0], T[0], Td[0])
        out["lcl_hpa"] = float(lcl_p.to("hPa").magnitude)
    except Exception:
        pass
    try:
        ccl_p, _, _ = mpcalc.ccl(p, T, Td)
        out["ccl_hpa"] = float(np.atleast_1d(ccl_p.to("hPa").magnitude)[0])
    except Exception:
        pass
    try:
        prof = mpcalc.parcel_profile(p, T[0], Td[0])
        lfc_p, _ = mpcalc.lfc(p, T, Td, parcel_temperature_profile=prof)
        out["lfc_hpa"] = float(np.atleast_1d(lfc_p.to("hPa").magnitude)[0]) if not np.isnan(np.atleast_1d(lfc_p.magnitude)[0]) else None
    except Exception:
        pass
    try:
        prof = mpcalc.parcel_profile(p, T[0], Td[0])
        el_p, _ = mpcalc.el(p, T, Td, parcel_temperature_profile=prof)
        out["el_hpa"] = float(np.atleast_1d(el_p.to("hPa").magnitude)[0]) if not np.isnan(np.atleast_1d(el_p.magnitude)[0]) else None
    except Exception:
        pass
    return out


def stability_indices(df: pd.DataFrame) -> dict:
    """K Index, Lifted Index, Total Totals, Showalter Index, SWEAT Index,
    dan CAPE/CIN untuk parsel SB (surface-based), ML (mixed-layer 500 m),
    dan MU (most-unstable)."""
    d = clean_profile(df)
    p, T, Td = _qty(d)
    result = {}

    try:
        result["k_index"] = float(mpcalc.k_index(p, T, Td).magnitude)
    except Exception:
        result["k_index"] = None
    try:
        result["total_totals"] = float(mpcalc.total_totals_index(p, T, Td).magnitude)
    except Exception:
        result["total_totals"] = None
    try:
        result["showalter_index"] = float(mpcalc.showalter_index(p, T, Td).magnitude[0])
    except Exception:
        result["showalter_index"] = None
    try:
        prof = mpcalc.parcel_profile(p, T[0], Td[0])
        result["lifted_index"] = float(mpcalc.lifted_index(p, T, prof).magnitude[0])
    except Exception:
        result["lifted_index"] = None

    spd = d["kecepatan_angin_kt"].to_numpy() * units.knots
    wdir = d["arah_angin_deg"].to_numpy() * units.deg
    try:
        result["sweat_index"] = float(np.atleast_1d(mpcalc.sweat_index(p, T, Td, spd, wdir).magnitude)[0])
    except Exception:
        result["sweat_index"] = None

    for label, fn in [("sb", mpcalc.surface_based_cape_cin),
                      ("ml", mpcalc.mixed_layer_cape_cin),
                      ("mu", mpcalc.most_unstable_cape_cin)]:
        try:
            cape, cin = fn(p, T, Td)
            result[f"cape_{label}"] = float(cape.magnitude)
            result[f"cin_{label}"] = float(cin.magnitude)
        except Exception:
            result[f"cape_{label}"] = None
            result[f"cin_{label}"] = None

    try:
        dcape, _, _ = mpcalc.downdraft_cape(p, T, Td)
        result["dcape"] = float(dcape.magnitude)
    except Exception:
        result["dcape"] = None

    return result


def tropopause_levels(significant_points_full: pd.DataFrame) -> dict:
    """Tropopause primer & sekunder dari indikator 'Tp' pada data mentah,
    serta estimasi independen tropopause primer berbasis kriteria WMO
    (lapse rate turun <= 2 C/km dan rata-rata lapse rate 2 km di atasnya
    juga <= 2 C/km)."""
    d = significant_points_full.copy()
    d = d.dropna(subset=["tekanan_hpa", "ketinggian_m"]).sort_values("ketinggian_m").reset_index(drop=True)

    tp_rows = d[d["indikator"].astype(str).str.strip() == "Tp"]
    tp_km = sorted((tp_rows["ketinggian_m"] / 1000.0).tolist())
    tropopause_primer_km = tp_km[0] if len(tp_km) >= 1 else None
    tropopause_sekunder_km = tp_km[1] if len(tp_km) >= 2 else None

    # Estimasi WMO: cari level pertama dgn lapse rate <= 2 C/km, dan rata-rata
    # lapse rate ke semua level dalam 2 km di atasnya juga <= 2 C/km.
    h = d["ketinggian_m"].to_numpy() / 1000.0  # km
    T = d["suhu_c"].to_numpy()
    estimasi_km = None
    valid = ~np.isnan(h) & ~np.isnan(T)
    h, T = h[valid], T[valid]
    if len(h) > 3:
        lapse = -np.diff(T) / np.diff(h)
        for i in range(len(lapse)):
            h0 = h[i + 1]
            if h0 < 5:  # tropopause diasumsikan di atas 5 km
                continue
            if lapse[i] > 2.0:
                continue
            # syarat WMO: rata-rata lapse rate dari h0 ke SETIAP level dalam
            # 2 km di atasnya juga harus <= 2 C/km
            mask = (h > h0) & (h <= h0 + 2.0)
            if mask.sum() == 0:
                estimasi_km = h0
                break
            avg_lapse = -(T[mask] - T[i + 1]) / (h[mask] - h0)
            if np.all(avg_lapse <= 2.0):
                estimasi_km = h0
                break
    return {
        "estimasi_tropopause_primer_km": estimasi_km,
        "tropopause_primer_km": tropopause_primer_km,
        "tropopause_sekunder_km": tropopause_sekunder_km,
    }


def lapse_rate_table(df: pd.DataFrame) -> pd.DataFrame:
    """Tabel lapse rate per lapisan antar titik data + status inversi +
    klasifikasi stabilitas lapisan berdasarkan perbandingan terhadap laju
    penurunan suhu adiabatik kering (~9.8 C/km) dan lembap rerata (~6.5 C/km)."""
    d = df.dropna(subset=["ketinggian_m", "suhu_c"]).sort_values("ketinggian_m").reset_index(drop=True)
    h = d["ketinggian_m"].to_numpy() / 1000.0
    T = d["suhu_c"].to_numpy()
    rows = []
    for i in range(1, len(d)):
        dz = h[i] - h[i - 1]
        if dz <= 0:
            continue
        lapse = -(T[i] - T[i - 1]) / dz
        inversi = "Inversi Suhu" if lapse < 0 else "Tidak Inversi"
        if lapse < 0:
            status = "Sangat Stabil (Inversi)"
        elif lapse < 6.5:
            status = "Stabil"
        elif lapse < 9.8:
            status = "Netral / Labil Bersyarat"
        else:
            status = "Labil"
        rows.append({
            "ketinggian_km": round(h[i], 2),
            "suhu_c": round(T[i], 2),
            "lapse_rate": round(lapse, 2),
            "status_inversi": inversi,
            "stabilitas_lapisan": status,
        })
    return pd.DataFrame(rows)


def humidity_characteristics(df: pd.DataFrame) -> dict:
    """RH rerata & DPD rerata pada lapisan 1000-700 hPa, mixing ratio permukaan,
    dan PWAT (dihitung ulang dari profil sebagai pembanding nilai dari header)."""
    d = clean_profile(df)
    layer = d[(d["tekanan_hpa"] <= 1000) & (d["tekanan_hpa"] >= 700)]
    rh_mean = layer["kelembapan_rh"].mean()
    dpd_mean = (layer["suhu_c"] - layer["titik_embun_c"]).mean()

    p, T, Td = _qty(d)
    try:
        mr_surface = float(mpcalc.mixing_ratio_from_relative_humidity(
            p[0], T[0],
            mpcalc.relative_humidity_from_dewpoint(T[0], Td[0])
        ).to("g/kg").magnitude)
    except Exception:
        mr_surface = None
    try:
        pwat = float(mpcalc.precipitable_water(p, Td).to("mm").magnitude)
    except Exception:
        pwat = None

    return {
        "rh_mean_1000_700": rh_mean,
        "dpd_mean_1000_700": dpd_mean,
        "surface_mixing_ratio": mr_surface,
        "pwat_mm": pwat,
    }


WIND_HEIGHT_BINS_FT = [
    (0, 5000, "0-5.000 ft"), (5000, 9000, "5.000-9.000 ft"),
    (9000, 23000, "9.000-23.000 ft"), (23000, 39000, "23.000-39.000 ft"),
    (39000, 55000, "39.000-55.000 ft"), (55000, 100000, ">55.000 ft"),
]


def wind_characteristics(df: pd.DataFrame) -> pd.DataFrame:
    """Tabel arah angin dominan & kecepatan angin rata-rata per kategori
    ketinggian (dalam kaki, 1 m = 3.28084 ft)."""
    d = df.dropna(subset=["ketinggian_m", "arah_angin_deg", "kecepatan_angin_kt"]).copy()
    d["ketinggian_ft"] = d["ketinggian_m"] * 3.28084
    rows = []
    for lo, hi, label in WIND_HEIGHT_BINS_FT:
        layer = d[(d["ketinggian_ft"] >= lo) & (d["ketinggian_ft"] < hi)]
        if layer.empty:
            continue
        rows.append({
            "kategori_ketinggian": label,
            "arah_angin_dominan": dominant_direction(layer["arah_angin_deg"]),
            "kecepatan_angin_kt": round(layer["kecepatan_angin_kt"].mean(), 2),
        })
    return pd.DataFrame(rows)


def wind_shear_0_6km(df: pd.DataFrame) -> float:
    """Bulk wind shear 0-6 km AGL (kt)."""
    d = clean_profile(df)
    p = d["tekanan_hpa"].to_numpy() * units.hPa
    spd = d["kecepatan_angin_kt"].to_numpy() * units.knots
    wdir = d["arah_angin_deg"].to_numpy() * units.deg
    h = d["ketinggian_m"].to_numpy() * units.m
    u, v = mpcalc.wind_components(spd, wdir)
    try:
        shear_u, shear_v = mpcalc.bulk_shear(p, u, v, height=h, depth=6000 * units.m)
        mag = (shear_u ** 2 + shear_v ** 2) ** 0.5
        return float(mag.to("knots").magnitude)
    except Exception:
        return float("nan")


def windex(df: pd.DataFrame, humidity: dict) -> float:
    """WINDEX (McCann, 1994) - estimasi potensi hembusan angin kencang
    (downburst) dari konveksi kering/lembap sedang.

    WINDEX = 5 * sqrt( Hm * Rq * (Gamma^2 - 30 + Ql - 2*Qm) )

    Hm    : tinggi level lebur 0 C (km AGL)
    Gamma : laju penurunan suhu rata-rata permukaan - level lebur (C/km)
    Rq    : rasio pencampuran permukaan / 12 (dibatasi 0-1)
    Ql    : rasio pencampuran permukaan (g/kg)
    Qm    : rasio pencampuran pada level lebur (g/kg)

    [Confidence: Medium - beberapa varian formula WINDEX beredar di literatur
    operasional; hasil ini sebaiknya diverifikasi silang bila dipakai untuk
    keputusan operasional peringatan dini.]
    """
    d = clean_profile(df)
    if d.empty or d["suhu_c"].min() > 0:
        return float("nan")
    # cari level lebur (T menyentuh 0 C) melalui interpolasi linear
    h_km = d["ketinggian_m"].to_numpy() / 1000.0
    T = d["suhu_c"].to_numpy()
    idx = np.where(np.diff(np.sign(T)))[0]
    if len(idx) == 0:
        return float("nan")
    i = idx[0]
    frac = T[i] / (T[i] - T[i + 1])
    Hm = h_km[i] + frac * (h_km[i + 1] - h_km[i])
    Hm = Hm - h_km[0]  # AGL

    Ql = humidity.get("surface_mixing_ratio")
    if Ql is None:
        return float("nan")
    Gamma = (T[0] - 0.0) / Hm if Hm > 0 else np.nan
    Rq = min(max(Ql / 12.0, 0), 1)
    Qm = 0.0  # mixing ratio pada level lebur diasumsikan sangat kecil (dekat 0)
    inside = Gamma ** 2 - 30 + Ql - 2 * Qm
    if inside < 0 or Hm <= 0 or np.isnan(Gamma):
        return 0.0
    return float(5 * np.sqrt(Hm * Rq * inside))


def hodograph_data(df: pd.DataFrame) -> pd.DataFrame:
    d = df.dropna(subset=["ketinggian_m", "kecepatan_angin_kt", "arah_angin_deg"]).copy()
    spd = d["kecepatan_angin_kt"].to_numpy() * units.knots
    wdir = d["arah_angin_deg"].to_numpy() * units.deg
    u, v = mpcalc.wind_components(spd, wdir)
    d["u_kt"] = u.magnitude
    d["v_kt"] = v.magnitude
    return d


def run_full_analysis(rsdata) -> dict:
    """Jalankan seluruh perhitungan untuk satu file .CRA yang sudah di-parse
    (parser.RadiosondeData) dan kembalikan satu dict hasil analisis lengkap,
    siap dipakai oleh interpretation.py, visualization.py, dan disimpan ke
    database.py."""
    sig_full = rsdata.tables.get("significant_points", pd.DataFrame())
    df = clean_profile(sig_full)

    stats = basic_statistics(df)
    conv = convective_levels(df)
    stab = stability_indices(df)
    tropo = tropopause_levels(sig_full)
    lapse_df = lapse_rate_table(df)
    humid = humidity_characteristics(df)
    wind_tbl = wind_characteristics(df)
    shear = wind_shear_0_6km(df)
    wdx = windex(df, humid)
    hodo = hodograph_data(df)

    header = {
        "tanggal": rsdata.tanggal, "tanggal_iso": rsdata.tanggal_iso,
        "waktu_utc": rsdata.waktu_utc, "stasiun": rsdata.stasiun,
        "indeks_wmo": rsdata.indeks_wmo, "sonde_id": rsdata.sonde_id,
        "posisi_lat": rsdata.posisi_lat, "posisi_lon": rsdata.posisi_lon,
        "posisi_text": rsdata.posisi_text,
        "waktu_mulai": rsdata.waktu_mulai, "durasi_penerbangan": rsdata.durasi_penerbangan,
        "waktu_burst": rsdata.waktu_burst,
        "ketinggian_maksimum_m": rsdata.ketinggian_maksimum_m,
        "tekanan_minimum_hpa": rsdata.tekanan_minimum_hpa,
        "alasan_terminasi": rsdata.alasan_terminasi,
        "tekanan_permukaan_hpa": rsdata.tekanan_permukaan_hpa,
        "suhu_permukaan_c": rsdata.suhu_permukaan_c,
        "kelembapan_relatif_permukaan": rsdata.kelembapan_relatif_permukaan,
        "kecepatan_angin_permukaan_kt": rsdata.kecepatan_angin_permukaan_kt,
        "arah_angin_permukaan_deg": rsdata.arah_angin_permukaan_deg,
        "pwat_mm": rsdata.pwat_mm,
    }

    return {
        "header": header,
        "profile_df": df,
        "tables": rsdata.tables,
        "stats": stats,
        "convective_levels": conv,
        "stability_indices": stab,
        "tropopause": tropo,
        "lapse_rate_table": lapse_df,
        "humidity": humid,
        "wind_table": wind_tbl,
        "wind_shear_kt": shear,
        "windex": wdx,
        "hodograph_df": hodo,
    }