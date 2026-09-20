"""
visualization.py
Seluruh fungsi pembuatan grafik dashboard. Skew-T Log-P memakai MetPy +
Matplotlib (agar tetap presisi secara meteorologis dengan skew, isobar,
garis adiabatik, dan wind barb), sedangkan grafik-grafik lain memakai
Plotly agar interaktif. Skema warna memakai palet peach-salmon-rose-mauve-
maroon (senada dengan app.py), background chart disamakan dengan
background utama app.

Revisi styling:
- SEMUA judul grafik dibuat berbentuk "chip" dengan background putih semi-
  transparan, rata tengah (menggantikan title bawaan Plotly yang polos).
- SEMUA grafik sekarang diberi judul sumbu X dan sumbu Y.
- Judul grafik Skew-T diubah menjadi "Grafik Skew-T Log-P" + kotak background.
- Judul grafik distribusi diubah menjadi "Distribusi Jumlah Titik Pengamatan
  Berdasarkan Indikator".
- Ukuran grafik dibuat lebih landscape (lebar > tinggi).
- REVISI (presisi layout): fig_lapse_rate & fig_donut_stabilitas kini memakai
  height & margin bawah yang SAMA PERSIS supaya sejajar presisi saat
  ditampilkan berdampingan di app.py. Donut diperbesar (hole diperkecil +
  domain diperluas) dan posisi legend digeser turun agar sejajar dengan
  judul sumbu "Ketinggian (km)" pada grafik di sampingnya.
- REVISI: ditambahkan fig_bar_status_inversi() -- bar chart distribusi
  status inversi, warna disamakan dengan fig_cape_cin_bar (ROSE solid),
  ditempatkan di bawah fig_donut_stabilitas() di app.py.


"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from metpy.plots import SkewT
from metpy.units import units
import metpy.calc as mpcalc

# ---------------------------------------------------------------------------
# PALET WARNA — senada dengan app.py: peach - salmon - rose - mauve - maroon - marun tua
# ---------------------------------------------------------------------------
PEACH = "#FFE7DA"        # peach terang — background utama (disamakan dengan app)
SALMON = "#FB9590"       # salmon
ROSE = "#DC586D"         # rose
MAUVE = "#A33757"        # mauve
MAROON = "#852E4E"       # maroon keunguan
MAROON_DARK = "#4C1D3D"  # marun tua/paling gelap

APP_BG = PEACH  # background utama app.py — dipakai supaya semua chart menyatu

# alias supaya kompatibel dengan pemanggilan lama (mis. app.py multi-waktu)
PINK_UTAMA = ROSE
PINK_GELAP = MAUVE
PINK_MEDIUM = SALMON
PINK_PALE = PEACH
PINK_ROSE = MAROON

BIRU = MAROON_DARK
BIRU_MUDA = SALMON
BIRU_TUA = MAROON_DARK
BIRU_PALE = "rgba(255,187,148,0.35)"   # peach transparan, untuk elemen dekoratif halus

PALETTE = [ROSE, MAROON_DARK, SALMON, MAUVE, MAROON]

# ---------------------------------------------------------------------------
# Layout dasar untuk semua grafik Plotly.
# Judul grafik TIDAK memakai title bawaan Plotly lagi -> lihat _pill_title().
# xaxis_title_font_color / yaxis_title_font_color dipakai (bukan key "xaxis"/
# "yaxis" utuh) supaya tidak bentrok dengan figure yang sudah mendefinisikan
# dict xaxis=/yaxis= sendiri (mis. fig_hodograph).
# ---------------------------------------------------------------------------
PLOTLY_LAYOUT = dict(
    template="plotly_white",
    font=dict(family="Arial, sans-serif", size=13, color=MAROON_DARK),
    margin=dict(l=50, r=25, t=70, b=45),
    plot_bgcolor="#FFF6EF",   # sedikit lebih terang dari background utama agar garis grafik kontras
    paper_bgcolor=APP_BG,
    xaxis_title_font_color=MAROON,
    yaxis_title_font_color=MAROON,
    xaxis_tickfont_color=MAROON,
    yaxis_tickfont_color=MAROON,
)


def _pill_title(text: str, top_margin: int = 78) -> dict:
    """
    Layout dict untuk judul grafik berbentuk "chip"/pill dengan background
    putih semi-transparan, SELALU rata tengah — konsisten dengan subtitle-box
    di app.py. Menggantikan title bawaan Plotly (yang polos, tanpa background).
    """
    layout = dict(PLOTLY_LAYOUT)
    margin = dict(layout.get("margin", {}))
    margin["t"] = top_margin
    layout["margin"] = margin
    layout["title"] = dict(text="")  # kosongkan title bawaan
    layout["annotations"] = [dict(
        text=f"<b>{text}</b>",
        xref="paper", yref="paper",
        x=0.5, y=1.0, xanchor="center", yanchor="bottom", yshift=18,
        showarrow=False,
        align="center",
        font=dict(size=15, color=MAROON_DARK, family="Arial, sans-serif"),
        bgcolor="rgba(255,255,255,0.68)",
        bordercolor=ROSE,
        borderwidth=1,
        borderpad=8,
    )]
    return layout


def fig_skewt(profile_df: pd.DataFrame):
    d = profile_df.dropna(subset=["tekanan_hpa", "suhu_c", "titik_embun_c"]).sort_values(
        "tekanan_hpa", ascending=False)
    p = d["tekanan_hpa"].to_numpy() * units.hPa
    T = d["suhu_c"].to_numpy() * units.degC
    Td = d["titik_embun_c"].to_numpy() * units.degC

    # Figure landscape (lebar > tinggi)
    fig = plt.figure(figsize=(9, 6.5))
    skew = SkewT(fig, rotation=45)
    skew.plot(p, T, color=MAROON, linewidth=2.0, label="Suhu")
    skew.plot(p, Td, color=MAROON_DARK, linewidth=2.0, label="Titik Embun")

    try:
        prof = mpcalc.parcel_profile(p, T[0], Td[0])
        skew.plot(p, prof, color=ROSE, linestyle="--", linewidth=1.5, label="Parcel Permukaan")
    except Exception:
        pass

    try:
        has_wind = d["kecepatan_angin_kt"].notna().any() and d["arah_angin_deg"].notna().any()
        if has_wind:
            spd = d["kecepatan_angin_kt"].to_numpy() * units.knots
            wdir = d["arah_angin_deg"].to_numpy() * units.deg
            u, v = mpcalc.wind_components(spd, wdir)
            step = max(len(p) // 25, 1)
            skew.plot_barbs(p[::step], u[::step], v[::step])
    except Exception:
        pass

    skew.plot_dry_adiabats(color="#FFD9BE", linewidth=0.6)
    skew.plot_moist_adiabats(color="#F7C3B5", linewidth=0.6)
    skew.plot_mixing_lines(color="#F0A8A0", linewidth=0.6)
    skew.ax.set_xlim(-90, 45)
    skew.ax.set_ylim(1000, 100)

    # Judul sumbu X/Y yang deskriptif — warna MAROON
    skew.ax.set_xlabel("Suhu (°C)", fontsize=11, color=MAROON)
    skew.ax.set_ylabel("Tekanan (hPa)", fontsize=11, color=MAROON)
    # Angka skala (tick) juga disamakan warnanya dengan judul sumbu
    skew.ax.tick_params(axis="x", colors=MAROON)
    skew.ax.tick_params(axis="y", colors=MAROON)

    # Judul grafik: "chip" background putih semi-transparan, rata tengah, kotak
    # (bukan rounded) dan diberi jarak (pad) lebih besar dari garis grafik.
    skew.ax.set_title(
        "Grafik Skew-T Log-P",
        fontsize=14, fontweight="bold", color=MAROON_DARK, loc="center", pad=22,
        bbox=dict(facecolor="white", alpha=0.78, edgecolor=ROSE, boxstyle="square,pad=0.4"),
    )
    skew.ax.legend(loc="upper right", fontsize=8, frameon=True, facecolor="white", framealpha=0.7)
    skew.ax.set_facecolor("#FFF6EF")
    fig.patch.set_facecolor(APP_BG)
    fig.tight_layout()
    return fig


def fig_profil_vertikal_parameter(df: pd.DataFrame, parameter: str):
    label_map = {
        "Kecepatan Angin (kt)": "kecepatan_angin_kt",
        "Kelembapan Relatif (%)": "kelembapan_rh",
        "Suhu (°C)": "suhu_c",
        "Tekanan (hPa)": "tekanan_hpa",
        "Titik Embun (°C)": "titik_embun_c",
    }
    col = label_map[parameter]
    d = df.dropna(subset=["ketinggian_m", col]).sort_values("ketinggian_m")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=d[col], y=d["ketinggian_m"] / 1000.0, mode="lines+markers",
        line=dict(color=ROSE, width=2.5), marker=dict(size=4, color=MAROON_DARK),
        name=parameter,
    ))
    fig.update_layout(
        xaxis_title=parameter, yaxis_title="Ketinggian (km)",
        height=360, **_pill_title(f"{parameter} berdasarkan Ketinggian (km)"),
    )
    return fig


def fig_arah_angin_ketinggian(df: pd.DataFrame):
    d = df.dropna(subset=["arah_angin_deg", "ketinggian_m"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=d["arah_angin_deg"], y=d["ketinggian_m"] / 1000.0, mode="markers",
        marker=dict(color=MAROON_DARK, size=7, opacity=0.85, line=dict(width=1, color=ROSE)),
    ))
    fig.update_layout(
        xaxis_title="Arah Angin (°)", yaxis_title="Ketinggian (km)",
        height=360, **_pill_title("Arah Angin (°) berdasarkan Ketinggian (km)"),
    )
    return fig


def fig_distribusi_titik(df: pd.DataFrame):
    counts = df["indikator"].value_counts()
    fig = go.Figure(go.Bar(x=counts.index, y=counts.values, marker_color=ROSE,
                            marker_line=dict(color=MAROON_DARK, width=1)))
    fig.update_layout(
        xaxis_title="Indikator", yaxis_title="Jumlah Titik",
        height=300, **_pill_title("Distribusi Jumlah Titik Pengamatan Berdasarkan Indikator"),
    )
    return fig


def fig_cape_cin_bar(stab: dict):
    parcels = ["MU", "ML", "SB"]
    cape_vals = [stab.get("cape_mu") or 0, stab.get("cape_ml") or 0, stab.get("cape_sb") or 0]
    cin_vals = [abs(stab.get("cin_mu") or 0), abs(stab.get("cin_ml") or 0), abs(stab.get("cin_sb") or 0)]

    fig_cape = go.Figure(go.Bar(y=parcels, x=cape_vals, orientation="h", marker_color=ROSE,
                                 marker_line=dict(color=MAROON_DARK, width=1)))
    fig_cape.update_layout(
        xaxis_title="CAPE (J/kg)", yaxis_title="Parcel",
        height=310, **_pill_title("CAPE (J/kg) berdasarkan Parcel"),
    )

    fig_cin = go.Figure(go.Bar(y=parcels, x=cin_vals, orientation="h", marker_color=PINK_MEDIUM,
                                marker_line=dict(color=MAROON_DARK, width=1)))
    fig_cin.update_layout(
        xaxis_title="CIN (J/kg)", yaxis_title="Parcel", xaxis_autorange="reversed",
        height=310, **_pill_title("CIN (J/kg) berdasarkan Parcel"),
    )
    return fig_cape, fig_cin


def fig_lapse_rate(lapse_df: pd.DataFrame):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=lapse_df["ketinggian_km"], y=lapse_df["lapse_rate"], mode="lines+markers",
        line=dict(color=ROSE, width=2.5), marker=dict(size=4, color=MAROON_DARK),
    ))
    fig.update_layout(
        xaxis_title="Ketinggian (km)", yaxis_title="Lapse Rate (°C/km)",
        yaxis_autorange="reversed", height=430,
        **_pill_title("Lapse Rate (°C/km) berdasarkan Ketinggian (km)"),
    )
    # Margin bawah disamakan presisi dengan fig_donut_stabilitas supaya kedua
    # grafik ini (yang ditampilkan berdampingan di app.py) sejajar presisi.
    fig.update_layout(margin=dict(b=75))
    return fig


def fig_donut_stabilitas(lapse_df: pd.DataFrame):
    counts = lapse_df["stabilitas_lapisan"].value_counts()
    colors = {"Stabil": ROSE, "Sangat Stabil (Inversi)": MAROON_DARK,
              "Netral / Labil Bersyarat": SALMON, "Labil": MAROON}
    fig = go.Figure(go.Pie(
        labels=counts.index, values=counts.values,
        hole=0.5,
        # Domain dipadatkan & digeser NAIK (y mulai lebih tinggi, rentang
        # lebih pendek) supaya donut "didorong ke atas" -- ruang di bawahnya
        # jadi lebih ringkas sebelum masuk ke fig_bar_status_inversi().
        domain=dict(x=[0.14, 0.92], y=[0.30, 1.0]),
        marker=dict(colors=[colors.get(k, SALMON) for k in counts.index],
                    line=dict(color="#FFFFFF", width=1.5)),
        textfont=dict(size=13),
        
    ))
    fig.update_layout(
        height=283,  # dinaikkan dari 260 -> mengimbangi top_margin yang kini
                     # disamakan dengan fig_lapse_rate (78, bukan 55) supaya
                     # ukuran/posisi donut di dalam area plot tetap konsisten.
        showlegend=True,
        legend=dict(orientation="h", y=0.20, x=0.5, xanchor="center", yanchor="top",
                    font=dict(size=11)),
        # top_margin TIDAK di-override lagi (pakai default 78, sama persis
        # dengan fig_lapse_rate) supaya "chip" judul "Distribusi Stabilitas
        # Lapisan" sejajar horizontal dengan "Lapse Rate (°C/km) berdasarkan
        # Ketinggian (km)" saat kedua grafik ditampilkan berdampingan.
        **_pill_title("Distribusi Stabilitas Lapisan"),
    )
    fig.update_layout(margin=dict(b=15))
    fig.update_yaxes(showticklabels=False)
    return fig


def fig_bar_status_inversi(lapse_df: pd.DataFrame):
    """Bar chart HORIZONTAL distribusi status inversi (kategori: 'Inversi
    Suhu' / 'Tidak Inversi', lihat calculation.lapse_rate_table). Warna
    disamakan dengan fig_cape_cin_bar (ROSE solid). Ditempatkan di bawah
    fig_donut_stabilitas() (yang kini diperkecil/didorong ke atas) di
    app.py, dengan tinggi disesuaikan supaya batas bawahnya mendekati
    sejajar dengan note_box di bawah fig_lapse_rate() pada kolom kiri.
    Catatan: kesejajaran ini perkiraan visual, bukan presisi pixel-perfect,
    karena tinggi note_box (HTML/CSS) dinamis mengikuti panjang teksnya."""
    counts = lapse_df["status_inversi"].value_counts()
    fig = go.Figure(go.Bar(
        y=counts.index, x=counts.values, orientation="h",
        marker_color=ROSE,
        marker_line=dict(color=MAROON_DARK, width=1),
    ))
    fig.update_layout(
        xaxis_title="Jumlah Lapisan", yaxis_title="Status Inversi",
        height=290, showlegend=False,
        **_pill_title("Distribusi Status Inversi"),
    )
    fig.update_layout(margin=dict(b=75))
    return fig


def fig_humidity_lines(df: pd.DataFrame):
    d = df.dropna(subset=["tekanan_hpa"]).copy()
    d["dpd"] = d["suhu_c"] - d["titik_embun_c"]
    try:
        p = d["tekanan_hpa"].to_numpy() * units.hPa
        T = d["suhu_c"].to_numpy() * units.degC
        Td = d["titik_embun_c"].to_numpy() * units.degC
        rh = mpcalc.relative_humidity_from_dewpoint(T, Td)
        mr = mpcalc.mixing_ratio_from_relative_humidity(p, T, rh).to("g/kg").magnitude
        d["mixing_ratio"] = mr
    except Exception:
        d["mixing_ratio"] = np.nan

    d = d.sort_values("tekanan_hpa", ascending=False)

    fig_dpd = go.Figure(go.Scatter(x=d["tekanan_hpa"], y=d["dpd"], mode="lines",
                                    line=dict(color=ROSE, width=2.5)))
    fig_dpd.update_layout(
        xaxis_title="Tekanan (hPa)", yaxis_title="Depresi Titik Embun (°C)",
        xaxis_autorange="reversed", height=320,
        **_pill_title("Depresi Titik Embun (°C) berdasarkan Tekanan (hPa)"),
    )

    fig_rh = go.Figure(go.Scatter(x=d["tekanan_hpa"], y=d["kelembapan_rh"], mode="lines",
                                   line=dict(color=MAROON_DARK, width=2.5)))
    fig_rh.update_layout(
        xaxis_title="Tekanan (hPa)", yaxis_title="Kelembapan Relatif (%)",
        xaxis_autorange="reversed", height=320,
        **_pill_title("Kelembapan Relatif (%) berdasarkan Tekanan (hPa)"),
    )

    fig_mr = go.Figure(go.Scatter(x=d["tekanan_hpa"], y=d["mixing_ratio"], mode="lines",
                                   line=dict(color=MAUVE, width=2.5)))
    fig_mr.update_layout(
        xaxis_title="Tekanan (hPa)", yaxis_title="Mixing Ratio (g/kg)",
        xaxis_autorange="reversed", height=320,
        **_pill_title("Mixing Ratio (g/kg) berdasarkan Tekanan (hPa)"),
    )
    return fig_dpd, fig_rh, fig_mr


def fig_kecepatan_angin_tekanan(df: pd.DataFrame):
    d = df.dropna(subset=["tekanan_hpa", "kecepatan_angin_kt"]).sort_values("tekanan_hpa", ascending=False)
    hover = [
        f"Ketinggian: {row.ketinggian_m:.0f} m<br>Arah: {row.arah_angin_deg:.0f}°<br>Indikator: {row.indikator}"
        for row in d.itertuples()
    ]
    fig = go.Figure(go.Scatter(
        x=d["tekanan_hpa"], y=d["kecepatan_angin_kt"], mode="lines+markers",
        line=dict(color=ROSE, width=2.5), marker=dict(size=4, color=MAROON_DARK),
        text=hover, hovertemplate="Tekanan: %{x} hPa<br>Kecepatan Angin: %{y} kt<br>%{text}<extra></extra>",
    ))
    fig.update_layout(
        xaxis_title="Tekanan (hPa)", yaxis_title="Kecepatan Angin (kt)",
        xaxis_autorange="reversed", height=380,
        **_pill_title("Profil Kecepatan Angin berdasarkan Tekanan"),
    )
    return fig


def fig_hodograph(hodo_df: pd.DataFrame):
    d = hodo_df.sort_values("ketinggian_m")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=d["u_kt"], y=d["v_kt"], mode="lines+markers",
        line=dict(color=ROSE, width=2.5),
        marker=dict(size=5, color=d["ketinggian_m"] / 1000.0, colorscale=[[0, SALMON], [1, MAROON_DARK]],
                    showscale=True, colorbar=dict(title="km")),
        hovertemplate="u: %{x:.1f} kt<br>v: %{y:.1f} kt<extra></extra>",
    ))

    # ---- Skala sumbu dibuat "robust" terhadap outlier ------------------------
    # Sebelumnya skala dihitung dari nilai MAKSIMUM absolut u/v. Jika ada satu
    # titik data yang tidak wajar (mis. kesalahan parsing / nilai angin ekstrem
    # yang tidak realistis), skala jadi meregang jauh (mis. sampai ratusan kt)
    # sementara mayoritas data hanya berkisar puluhan kt, sehingga hodograf
    # terlihat "kecil" menggerombol di tengah. Di sini dipakai persentil ke-95
    # (bukan maksimum mutlak) supaya satu outlier tidak mendikte seluruh skala.
    # CATATAN: ini hanya memperbaiki tampilan/zoom, bukan memvalidasi data —
    # kalau nilai u/v memang sering melebihi ~100 kt, ada baiknya dicek ulang
    # sumber datanya (kemungkinan salah parsing kolom kecepatan/arah angin).
    combined = pd.concat([d["u_kt"].abs(), d["v_kt"].abs()]).dropna()
    if not combined.empty:
        robust_max = float(np.nanpercentile(combined, 95))
        max_r = max(robust_max * 1.3, 15)
    else:
        max_r = 15

    for r in np.linspace(max_r / 3, max_r, 3):
        theta = np.linspace(0, 2 * np.pi, 100)
        fig.add_trace(go.Scatter(x=r * np.cos(theta), y=r * np.sin(theta), mode="lines",
                                 line=dict(color="#F0A8A0", width=1), showlegend=False, hoverinfo="skip"))
    fig.update_layout(
        xaxis=dict(scaleanchor="y", scaleratio=1, range=[-max_r, max_r], title="Komponen U (kt)"),
        yaxis=dict(range=[-max_r, max_r], title="Komponen V (kt)"),
        height=620,
        **_pill_title("Hodograf Angin"),
    )
    return fig