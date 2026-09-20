"""
report.py
---------
Builds a downloadable summary report (Markdown text) combining header
metadata, key statistics, derived indices, and the automatic insight
paragraphs from interpretation.py. Returned as a plain string so app.py can
offer it as a `st.download_button` without any extra file-format
dependency (Markdown renders fine as plain text too).
"""

from __future__ import annotations

from datetime import datetime


def _fmt(value, unit: str = "", decimals: int = 2) -> str:
    if value is None:
        return "--"
    try:
        return f"{value:.{decimals}f}{unit}"
    except (TypeError, ValueError):
        return f"{value}{unit}"


def build_markdown_report(parsed, calc_results: dict, insights: dict) -> str:
    h = parsed.header
    s = parsed.surface
    lvl = calc_results["convective_levels"]
    cape_cin = calc_results["cape_cin"]
    stab = calc_results["stability_indices"]
    tropo = calc_results["tropopause"]
    hum = calc_results["humidity"]
    stats = calc_results["basic_statistics"]

    lines = []
    lines.append(f"# Laporan Analisis Kondisi Atmosfer Berbasis Data Radiosonde")
    lines.append("")
    lines.append(f"Dibuat: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    lines.append("## 1. Informasi Observasi")
    lines.append(f"- Tanggal: {h.get('Date', '--')}")
    lines.append(f"- Waktu (UTC): {h.get('Time', '--')}")
    lines.append(f"- Stasiun: {h.get('Station name', '--')}")
    lines.append(f"- Indeks WMO: {h.get('WMO Station index', '--')}")
    lines.append(f"- Sonde ID: {h.get('Sonde ID', '--')}")
    lines.append(f"- Posisi: {h.get('Position', '--')}")
    lines.append("")

    lines.append("## 2. Statistik Data Radiosonde")
    lines.append(f"- Suhu: {_fmt(stats['suhu_min_C'])} s.d. {_fmt(stats['suhu_max_C'])} °C")
    lines.append(f"- Titik Embun: {_fmt(stats['titik_embun_min_C'])} s.d. {_fmt(stats['titik_embun_max_C'])} °C")
    lines.append(f"- Kelembapan Relatif: {_fmt(stats['rh_min_pct'])} s.d. {_fmt(stats['rh_max_pct'])} %")
    lines.append(f"- Tekanan: {_fmt(stats['tekanan_min_hPa'])} s.d. {_fmt(stats['tekanan_max_hPa'])} hPa")
    lines.append(f"- Ketinggian: {_fmt(stats['ketinggian_min_m']/1000, decimals=2)} s.d. {_fmt(stats['ketinggian_max_m']/1000, decimals=2)} km")
    lines.append(f"- Kecepatan Angin: {_fmt(stats['wind_speed_min_kt'])} s.d. {_fmt(stats['wind_speed_max_kt'])} kt")
    lines.append(f"- Arah Angin Dominan: {calc_results.get('dominant_wind_overall', '--')}")
    lines.append("")

    lines.append("## 3. Level Konveksi Atmosfer")
    lines.append(f"- LCL: {_fmt(lvl.get('LCL_hPa'), ' hPa')}")
    lines.append(f"- CCL: {_fmt(lvl.get('CCL_hPa'), ' hPa')}")
    lines.append(f"- LFC: {_fmt(lvl.get('LFC_hPa'), ' hPa')}")
    lines.append(f"- EL: {_fmt(lvl.get('EL_hPa'), ' hPa')}")
    lines.append("")
    lines.append(f"_{insights.get('convective_levels', '')}_")
    lines.append("")

    lines.append("## 4. Tropopause")
    lines.append(f"- Estimasi Tropopause Primer: {_fmt(tropo.get('primary_km'), ' km')}")
    lines.append(f"- Tropopause Sekunder: {_fmt(tropo.get('secondary_km'), ' km')}")
    lines.append("")

    lines.append("## 5. Parameter Stabilitas Atmosfer")
    for parcel in ["SB", "ML", "MU"]:
        c = cape_cin.get(parcel, {})
        lines.append(f"- {parcel}CAPE: {_fmt(c.get('CAPE_Jkg'), ' J/kg')} | {parcel}CIN: {_fmt(c.get('CIN_Jkg'), ' J/kg')}")
    lines.append(f"- K Index: {_fmt(stab.get('K_Index'))}")
    lines.append(f"- LI: {_fmt(stab.get('LI'))}")
    lines.append(f"- TT: {_fmt(stab.get('TT'))}")
    lines.append(f"- SI: {_fmt(stab.get('SI'))}")
    lines.append("")
    lines.append(f"_{insights.get('stability', '')}_")
    lines.append("")

    lines.append("## 6. Karakteristik Kelembapan Atmosfer")
    lines.append(f"- RH Mean 1000-700 hPa: {_fmt(hum.get('RH_mean_1000_700_pct'), ' %')}")
    lines.append(f"- Mean DPD 1000-700 hPa: {_fmt(hum.get('DPD_mean_1000_700_C'), ' °C')}")
    lines.append(f"- Surface Mixing Ratio: {_fmt(hum.get('surface_mixing_ratio_gkg'), ' g/kg')}")
    lines.append(f"- PWAT: {_fmt(hum.get('PWAT_mm'), ' mm')}")
    lines.append("")
    lines.append(f"_{insights.get('humidity', '')}_")
    lines.append("")

    lines.append("## 7. Karakteristik Angin Atmosfer")
    lines.append(f"- Wind Shear (0-6 km): {_fmt(calc_results.get('wind_shear_0_6km_kt'), ' kt')}")
    lines.append(f"- WindEx: {_fmt(calc_results.get('windex_kt'), ' kt')}")
    lines.append("")
    lines.append(f"_{insights.get('wind', '')}_")
    lines.append("")

    lines.append("## 8. Indeks Potensi Cuaca Buruk")
    lines.append(f"- SWEAT Index: {_fmt(stab.get('SWEAT'))}")
    lines.append(f"- DCAPE: {_fmt(calc_results.get('dcape_Jkg'), ' J/kg')}")
    lines.append("")
    lines.append(f"_{insights.get('sweat_dcape', '')}_")
    lines.append("")

    lines.append("## 9. Kesimpulan")
    lines.append(insights.get("conclusion", ""))
    lines.append("")

    return "\n".join(lines)