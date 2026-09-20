"""
app.py
Dashboard Analisis Kondisi Atmosfer Berbasis Data Radiosonde (.CRA)
Jalankan dengan: streamlit run app.py
"""

import warnings
warnings.filterwarnings("ignore")

import re
import streamlit as st
import pandas as pd
import numpy as np

from parser import parse_cra_file, parse_cra_bytes
from calculation import run_full_analysis
import interpretation as itp
import policy as pol
import visualization as viz
import database as db

st.set_page_config(page_title="Dashboard Analisis Kondisi Atmosfer Berbasis Data Radiosonde",
                   layout="wide")

# ---------------------------------------------------------------------------
# PALET WARNA — palet baru (peach - salmon - rose - mauve - maroon - marun tua).
# Catatan/note-box sengaja dikecualikan (pakai kuning soft) sesuai permintaan.
# ---------------------------------------------------------------------------
BIRU_TUA = "#4C1D3D"     # paling gelap — judul, teks penting
BIRU_AKSEN = "#A33757"   # mauve — angka metric, aksen insight-box, tab aktif
BIRU_MUDA = "#FB9590"    # salmon — sidebar, header bar
BIRU_PALE = "#FFE7DA"    # peach terang — background utama app
PINK_GELAP = "#DC586D"   # rose — aksen section-header, border dropzone
PINK_MEDIUM = "#852E4E"  # maroon — background dropzone
PINK_PALE = "#FB9590"    # salmon — background file uploader, background tab

CUSTOM_CSS = f"""
<style>
.stApp {{
    background-color: {BIRU_PALE};
}}
[data-testid="stSidebar"] {{
    background-color: {BIRU_MUDA};
}}
.sidebar-title-box {{
    background-color: #ffffff;
    color: {BIRU_TUA};
    border-radius: 30px;
    padding: px 16px;
    font-size: 20px;
    font-weight: 800;
    text-align: center;
    margin-bottom: 16px;
    box-shadow: 0 2px 6px rgba(0,0,0,.10);       
}}
[data-testid="stSidebar"] [data-testid="stRadio"] {{
    background-color: {PINK_MEDIUM};
    border-radius: 14px;
    padding: 14px 16px;
    box-shadow: 0 2px 6px rgba(0,0,0,.10);
}}
[data-testid="stSidebar"] [data-testid="stRadio"] label,
[data-testid="stSidebar"] [data-testid="stRadio"] label p {{
    color: #ffffff !important;
}}
[data-testid="stHeader"] {{
    background-color: {BIRU_PALE};
}}
    .block-container {{padding-top: 2rem;}}
    h1, h2, h3 {{
    color: {BIRU_TUA};
    text-align: center;
}}

h1 {{
    text-align: center;
}}

    /* ===== Section header — dibuat KAPITAL semua + kontras lebih kuat ===== */
    .section-header {{
    background-color: {PINK_GELAP};
    color: #ffffff;
    padding: 10px 16px;
    border-radius: 30px;

    font-size: 15px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;

    text-align: center;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;

    margin-bottom: 12px;

    box-shadow: 0 2px 6px rgba(0,0,0,.18);
}}

    /* ===== Insight / catatan: rata kanan-kiri (justify) + warna lebih kontras ===== */
    .insight-box {{
        background-color: #FBD0DA; border-left: 6px solid {BIRU_AKSEN};
        padding: 14px 18px; border-radius: 6px; font-size: 0.95rem;
        text-align: justify; text-justify: inter-word;
        color: {BIRU_TUA};
        box-shadow: 0 1px 4px rgba(0,0,0,.10);
    }}
    .note-box {{
        background-color: #FFF1B8; border-left: 6px solid #C99A1E;
        padding: 12px 16px; border-radius: 6px; font-size: 0.88rem; color: #4A3B00;
        text-align: justify; text-justify: inter-word; font-weight: 600;
    }}

    /* ===== Kesimpulan: kotak PUTIH polos, beda dari insight-box ===== */
    .conclusion-box {{
        background-color: #ffffff;
        border-radius: 12px;
        padding: 16px 20px;
        border: 1px solid #ECECEC;
        box-shadow: 0 1px 4px rgba(0,0,0,.08);
        text-align: justify;
        text-justify: inter-word;
        color: {BIRU_TUA};
        font-size: 0.95rem;
    }}

    h1 {{
    color: {BIRU_TUA} !important;
}}

/* Container luar file uploader */
[data-testid="stFileUploader"] {{
    background-color: {PINK_PALE} !important;
    border-radius: 15px;
    padding: 12px;
    box-shadow: 0 3px 10px rgba(0,0,0,.10);
}}

/* Kotak upload (dropzone, sebelum file dipilih) — teks putih di atas background maroon */
[data-testid="stFileUploaderDropzone"] {{
    background-color: {PINK_MEDIUM} !important;
    border: 2px dashed {PINK_GELAP} !important;
    border-radius: 12px;
}}
[data-testid="stFileUploaderDropzone"] * {{
    color: #ffffff !important;
}}

/* File yang SUDAH diupload (chip putih) — teks dibuat GELAP supaya kelihatan */
[data-testid="stFileUploader"] section [data-testid="stFileUploaderFile"],
[data-testid="stFileUploader"] section [data-testid="stFileUploaderFile"] * {{
    color: {BIRU_TUA} !important;
}}
[data-testid="stFileUploader"] section [data-testid="stFileUploaderFileName"] {{
    color: {BIRU_TUA} !important;
}}
[data-testid="stFileUploader"] section small {{
    color: {BIRU_TUA} !important;
}}
[data-testid="stFileUploaderDropzone"] button {{
    background-color: #ffffff !important;
    border: 1px solid {BIRU_TUA} !important;
    border-radius: 8px !important;
    color: {BIRU_TUA} !important;
}}
[data-testid="stFileUploaderDropzone"] button * {{
    color: {BIRU_TUA} !important;
}}
[data-testid="stFileUploaderDropzone"] button:hover {{
    background-color: #F5F5F5 !important;
    border: 1px solid {BIRU_TUA} !important;
}}
[data-testid="stFileUploaderDropzone"] button svg {{
    fill: {BIRU_TUA} !important;
}}
[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] label p {{
    color: {BIRU_TUA} !important;
    font-weight: 600;
}}
.info-card{{
    background:#ffffff;
    border-radius:18px;
    padding:18px 22px;
    border:1px solid #ECECEC;
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
    height:280px;
    overflow-y:auto;
    text-align:left;
}}

.policy-card{{
    background:#ffffff;
    border-radius:18px;
    padding:20px;
    border:1px solid #ECECEC;
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
    min-height:170px;
    text-align: justify;
    text-justify: inter-word;
    color: {BIRU_TUA};
}}

.stat-card{{
    background:transparent;
    padding:6px 0 0 0;
}}

/* ===== Tabel info (Informasi Observasi / Penerbangan Balon / Kondisi Permukaan): rata kiri ===== */
.info-table{{
    width:100%;
    border-collapse:collapse;
    table-layout:auto;
    margin:0;
}}

.info-table td{{
    padding:6px 10px;
    vertical-align:top;
    font-size:15px;
    border:none;
    text-align:left;
}}

.info-table td:first-child{{
    font-weight:700;
    white-space:nowrap;
    color:{BIRU_TUA};
}}

.info-table td:last-child{{
    color:#333;
    text-align:left;
}}

.st-emotion-cache-19loc4w {{
    color: white !important;
}}

/* ===== Kotak hint upload: teks HITAM ===== */
.upload-hint {{
    background-color: #FFFBEA;
    border-left: 6px solid #E8C468;
    color: #000000;
    padding: 10px 16px;
    border-radius: 8px;
    font-size: 15px;
    text-align:center;
    font-weight:600;
}}

/* Bagian "Data Profil Vertikal": tab + tabel dibungkus background salmon muda */
[data-testid="stTabs"] {{
    background-color: {PINK_PALE};
    border-radius: 14px;
    padding: 14px;
    box-shadow: 0 3px 10px rgba(0,0,0,.10);
}}

[data-baseweb="tab-list"] {{
    background-color: transparent;
    gap: 6px;
}}

[data-baseweb="tab"] {{
    border-radius: 8px 8px 0 0;
    background-color: rgba(255,255,255,0.55);
    color: {BIRU_TUA};
    font-weight: 700;
}}

/* Tab aktif — background lebih gelap & kontras + font putih */
[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"],
[data-testid="stTabs"] [data-baseweb="tab"][data-selected] {{
    background-color: {BIRU_TUA} !important;
}}

[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] *,
[data-testid="stTabs"] [data-baseweb="tab"][data-selected],
[data-testid="stTabs"] [data-baseweb="tab"][data-selected] * {{
    color: #ffffff !important;
}}

[data-testid="stTabs"] [data-baseweb="tab-highlight"] {{
    background-color: {PINK_GELAP} !important;
}}

/* Tabel (st.dataframe) — background tidak putih polos */
[data-testid="stDataFrame"] {{
    background-color: {PINK_PALE};
    border-radius: 12px;
    padding: 6px;
    border: 1px solid {PINK_GELAP};
}}
[data-testid="stDataFrameResizable"] {{
    background-color: {PINK_PALE} !important;
}}

/* Alert bawaan Streamlit (mis. "data tanggal ... tidak disimpan ulang") — kontras lebih jelas */
[data-testid="stAlert"] {{
    border-radius: 10px !important;
}}
[data-testid="stAlert"] p {{
    color: {BIRU_TUA} !important;
    font-weight: 700 !important;
    font-size: 15px !important;
}}

/* Kartu statistik ringkasan di bagian bawah profil vertikal */
.stat-grid-title{{
    color:{BIRU_TUA};
    font-size:17px;
    font-weight:700;
    margin-bottom:14px;
    text-align:center;
}}

/* teks umum rata tengah (default), kecuali kelas yang override di atas */
.stMarkdown, p, li, label {{
    text-align:center;
}}

/* ===== Sub-judul kecil (label di atas grafik/tabel) — background semi-transparan, rata tengah ===== */
.subtitle-wrap {{
    text-align:center;
    margin: 23px 0 12px 0;
}}
.subtitle-box {{
    display:inline-block;
    background-color: rgba(255,255,255,0.65);
    color: {BIRU_TUA};
    padding: 6px 20px;
    border-radius: 20px;
    font-weight:700;
    font-size:15.5px;
    text-align:center;
    box-shadow: 0 1px 4px rgba(0,0,0,.08);
    border: 1px solid {PINK_GELAP};
}}

/* ===== Kontrol Visualisasi: container dengan KEY -> class .st-key-kontrol_viz ===== */
/* Diisi warna solid (bukan cuma outline) supaya benar-benar terlihat sebagai kotak berwarna */
.st-key-kontrol_viz {{
    background-color: {PINK_PALE} !important;
    border-radius: 16px !important;
    padding: 6px 20px 16px 20px !important;
    border: 1px solid {PINK_GELAP} !important;
    box-shadow: 0 3px 10px rgba(0,0,0,.12);
    margin-bottom: 16px;
    margin-top: 80px;
}}
.st-key-kontrol_viz > div {{
    background-color: transparent !important;
}}
/* Rapatkan jarak vertikal di bagian ATAS kontainer kontrol visualisasi:
   div "control-marker" kosong + subtitle-box di atasnya sengaja dipepetkan. */
.st-key-kontrol_viz .subtitle-wrap {{
    margin-top: 0 !important;
    margin-bottom: 6px !important;
}}
.st-key-kontrol_viz [data-testid="stMarkdownContainer"]:has(.control-marker) {{
    margin: 0 !important;
    padding: 0 !important;
    line-height: 0 !important;
}}
/* Label "Parameter" dan "Ketinggian (m)" — putih */
.st-key-kontrol_viz label,
.st-key-kontrol_viz label p {{
    color: #ffffff !important;
}}
/* fallback untuk versi Streamlit yang memakai struktur wrapper lama */
div[data-testid="stVerticalBlockBorderWrapper"]:has(div.control-marker) {{
    background-color: {PINK_PALE} !important;
    border-radius: 16px !important;
    padding: 6px 20px 16px 20px !important;
    border: 1px solid {PINK_GELAP} !important;
    box-shadow: 0 3px 10px rgba(0,0,0,.12);
    margin-bottom: 16px;
}}
div[data-testid="stVerticalBlockBorderWrapper"]:has(div.control-marker) label,
div[data-testid="stVerticalBlockBorderWrapper"]:has(div.control-marker) label p {{
    color: #ffffff !important;
}}
[data-testid="stFileUploaderDropzone"][data-testid="stFileUploaderDropzone"] * {{
    color: {BIRU_TUA} !important;
}}
[data-baseweb="tab"] {{
    border-radius: 8px 8px 0 0;
    background-color: rgba(255,255,255,0.55);
    color: #ffffff;
    font-weight: 700;
}}
[data-testid="stDataFrame"] [data-testid="stElementToolbar"] ~ div [role="columnheader"],
[data-testid="stDataFrame"] div[role="columnheader"] {{
    color: {BIRU_TUA} !important;
    font-weight: 700;
}}
[data-testid="stFileUploaderDropzone"] span.st-emotion-cache-19loc4w {{
    color: white !important;
    font-weight: 500 !important;
}}

/* ===== Kotak metric custom (pengganti st.metric bawaan agar rata tengah 100% presisi) ===== */
.custom-metric {{
    background-color: {PINK_MEDIUM};
    border: 1px solid {BIRU_TUA};
    border-radius: 12px;
    padding: 14px 10px 12px 10px;
    margin-bottom: 14px;
    text-align: center;
    min-height: 100px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}}
.cm-header {{
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 6px;
    width: 100%;
    margin-bottom: 4px;
}}
.cm-label {{
    color: #ffffff;
    font-size: 14px;
    text-align: center;
    font-weight: 400;
}}
.custom-metric .cm-value {{
    color: #ffffff;
    font-size: 28px;
    font-weight: 800;
    text-align: center;
    width: 100%;
}}
/* Ikon bantuan "?" kecil menempel di sebelah label — tooltip muncul saat hover,
   mirip ikon bantuan bawaan st.metric, tapi 100% terkontrol (tidak tergantung
   struktur internal Streamlit yang berubah-ubah antar versi). */
.cm-help {{
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: rgba(255,255,255,0.28);
    color: #ffffff;
    font-size: 11px;
    font-weight: 700;
    cursor: help;
    flex-shrink: 0;
}}
.cm-help .cm-tooltip {{
    visibility: hidden;
    opacity: 0;
    position: absolute;
    bottom: 135%;
    left: 50%;
    transform: translateX(-50%);
    background: #ffffff;
    color: {BIRU_TUA};
    text-align: left;
    padding: 10px 12px;
    border-radius: 8px;
    font-size: 12.5px;
    font-weight: 400;
    line-height: 1.4;
    width: 230px;
    box-shadow: 0 3px 12px rgba(0,0,0,.25);
    transition: opacity .15s ease;
    z-index: 999;
    pointer-events: none;
}}
.cm-help:hover .cm-tooltip {{
    visibility: visible;
    opacity: 1;
}}

/* ===== Kotak Wind Shear / WindEx — tinggi vertikal DISAMAKAN dengan kotak
   Catatan di sampingnya (bagian "KARAKTERISTIK ANGIN ATMOSFER"). ===== */
.st-key-wind_metrics_box {{
    display: flex;
    align-items: center;
    height: 100%;
}}
.st-key-wind_metrics_box > div {{
    width: 100%;
}}
.matched-note-box {{
    min-height: 100px;
    display: flex;
    align-items: center;
    box-sizing: border-box;
}}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def section_header(text):
    st.markdown(f'<div class="section-header">{text}</div>', unsafe_allow_html=True)


def insight_box(text):
    st.markdown(f'<div class="insight-box">{text}</div>', unsafe_allow_html=True)


def note_box(text, extra_class: str = ""):
    """Kotak catatan (kuning). extra_class opsional dipakai untuk menyamakan
    tinggi/ukuran kotak ini dengan elemen lain di sampingnya (mis. metric)."""
    css_class = ("note-box " + extra_class).strip()
    st.markdown(f'<div class="{css_class}">Catatan: {text}</div>', unsafe_allow_html=True)


def conclusion_box(text):
    """Kotak KESIMPULAN — putih polos, sengaja dibedakan dari insight-box."""
    st.markdown(f'<div class="conclusion-box">{text}</div>', unsafe_allow_html=True)


def subtitle(text):
    """Sub-judul kecil (di atas grafik/tabel) dengan background semi-transparan, rata tengah."""
    st.markdown(f'<div class="subtitle-wrap"><span class="subtitle-box">{text}</span></div>',
                unsafe_allow_html=True)


def page_header(text, align="center"):
    st.markdown(
        f"""
        <h2 style="
            color:{BIRU_TUA};
            font-size:28px;
            font-weight:700;
            margin-top:20px;
            margin-bottom:3px;
            text-align:{align};
        ">
            {text}
        </h2>
        """,
        unsafe_allow_html=True
    )


def custom_metric(label, value, help_text=None):
    """Pengganti st.metric bawaan Streamlit — label & value dijamin rata
    tengah karena murni HTML/CSS kita sendiri, bukan mengandalkan struktur
    internal Streamlit yang bisa berubah antar versi. Jika help_text diisi,
    ikon "?" kecil ditampilkan menempel di sebelah label (tooltip muncul
    saat hover), mirip ikon bantuan bawaan st.metric."""
    help_html = ""
    if help_text:
        tooltip_text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", help_text)
        help_html = f'<span class="cm-help">?<span class="cm-tooltip">{tooltip_text}</span></span>'
    st.markdown(f"""
    <div class="custom-metric">
        <div class="cm-header"><span class="cm-label">{label}</span>{help_html}</div>
        <div class="cm-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Definisi/penjelasan istilah — ditampilkan lewat popover custom_metric
# ---------------------------------------------------------------------------
DEFINISI = {
    "lcl": "**LCL (Lifting Condensation Level)** — ketinggian/tekanan tempat parcel udara yang "
           "diangkat secara paksa mencapai titik jenuh dan mulai terkondensasi menjadi awan.",
    "ccl": "**CCL (Convective Condensation Level)** — ketinggian tempat kondensasi mulai terjadi "
           "akibat pemanasan permukaan (konveksi termal), tanpa pengangkatan paksa.",
    "lfc": "**LFC (Level of Free Convection)** — ketinggian tempat parcel udara menjadi lebih hangat "
           "dari lingkungan sekitarnya sehingga dapat naik bebas tanpa gaya dorong eksternal.",
    "el": "**EL (Equilibrium Level)** — ketinggian tempat parcel udara berhenti naik karena suhunya "
          "sudah sama dengan suhu lingkungan; umumnya menandai puncak awan konvektif.",
    "cape": "**CAPE (Convective Available Potential Energy)** — energi potensial yang tersedia untuk "
            "mendorong parcel udara naik. Semakin besar nilainya, semakin besar potensi konveksi/badai.",
    "cin": "**CIN (Convective Inhibition)** — energi yang menahan parcel udara agar tidak naik bebas. "
           "Nilai yang besar berarti atmosfer lebih tertahan/stabil dan menekan pertumbuhan awan.",
    "k_index": "**K Index** — indikator potensi badai petir berdasarkan gradien suhu vertikal dan "
               "kandungan kelembapan pada lapisan bawah atmosfer.",
    "li": "**LI (Lifted Index)** — selisih suhu lingkungan dengan suhu parcel yang diangkat ke 500 hPa. "
          "Nilai negatif menandakan atmosfer labil/berpotensi konvektif.",
    "tt": "**TT (Total Totals Index)** — gabungan Vertical Totals dan Cross Totals, dipakai untuk "
          "menilai potensi badai konvektif.",
    "si": "**SI (Showalter Index)** — mirip Lifted Index, mengukur stabilitas atmosfer pada lapisan "
          "menengah (dari 850 ke 500 hPa).",
    "sweat": "**SWEAT (Severe Weather Threat Index)** — menggabungkan parameter termodinamika dan "
             "angin untuk menilai potensi cuaca ekstrem/severe weather.",
    "dcape": "**DCAPE (Downdraft CAPE)** — energi potensial yang mendorong terjadinya downdraft, "
             "terkait potensi angin kencang atau downburst saat badai.",
    "shear": "**Wind Shear** — perubahan kecepatan dan/atau arah angin terhadap ketinggian; berperan "
             "penting dalam organisasi dan intensitas badai.",
    "windex": "**WindEx (Wind Index)** — estimasi potensi kecepatan downburst berdasarkan mixing ratio "
              "dan lapse rate lapisan bawah.",
    "tropopause": "**Tropopause** — batas atas troposfer, ditandai dengan perubahan tajam pada laju "
                  "penurunan suhu (lapse rate) terhadap ketinggian.",
    "mu": "**MU (Most Unstable)** — parcel udara diambil dari level pada 300 hPa terbawah yang memiliki "
          "nilai theta-e (suhu ekuivalen potensial) tertinggi, yaitu lapisan udara paling labil di dekat "
          "permukaan. Merepresentasikan skenario konveksi terburuk/terkuat yang mungkin terjadi.",
    "ml": "**ML (Mixed Layer)** — parcel udara dihitung dari rata-rata suhu dan kelembapan pada lapisan "
          "campuran dekat permukaan (umumnya ±500 m pertama). Merepresentasikan kondisi udara yang sudah "
          "tercampur akibat pemanasan/turbulensi permukaan.",
    "sb": "**SB (Surface Based)** — parcel udara diambil langsung dari kondisi suhu dan kelembapan di "
          "permukaan (level pertama data). Merepresentasikan potensi konveksi jika udara permukaan yang "
          "terangkat ke atas.",
    "lapse_rate": "**Lapse Rate** — laju penurunan suhu udara terhadap penambahan ketinggian (°C/km). "
              "Dibandingkan terhadap laju adiabatik kering (~9.8 °C/km) dan lembap rerata (~6.5 °C/km) "
              "untuk menentukan stabilitas suatu lapisan atmosfer.",
    "inversi": "**Inversi Suhu** — kondisi ketika suhu udara naik seiring bertambahnya ketinggian "
           "(berkebalikan dari kondisi normal). Lapisan inversi bersifat sangat stabil dan dapat "
           "menghambat pergerakan udara vertikal serta pencampuran polutan.",
    "stabilitas_lapisan": "**Stabilitas Lapisan** — klasifikasi kondisi suatu lapisan atmosfer (Stabil, "
                      "Netral/Labil Bersyarat, atau Labil) berdasarkan perbandingan lapse rate aktual "
                      "terhadap laju adiabatik kering dan lembap. Lapisan labil mendukung pergerakan "
                      "udara vertikal (konveksi), sedangkan lapisan stabil menahannya.",
    "dpd": "**Depresi Titik Embun (DPD - Dew Point Depression)** — selisih antara suhu udara dan titik "
       "embun (T - Td). Nilai yang kecil menandakan udara mendekati titik jenuh (lembap), sedangkan "
       "nilai besar menandakan udara kering. DPD kecil pada lapisan menengah-atas sering dikaitkan "
       "dengan potensi awan konvektif yang lebih besar.",
    "mixing_ratio": "**Mixing Ratio (Rasio Pencampuran)** — massa uap air per satuan massa udara kering "
        "(g/kg), dihitung dari tekanan, suhu, dan kelembapan relatif di permukaan. Menunjukkan "
        "kandungan uap air aktual yang tersedia di suatu titik, terlepas dari suhu udara saat itu.",
}

# ---------------------------------------------------------------------------
# HALAMAN 1-2: UPLOAD & INFORMASI PROFIL DATA
# ---------------------------------------------------------------------------

def render_upload_and_profile():
    st.title("Dashboard Analisis Kondisi Atmosfer Berbasis Data Radiosonde")

    page_header("Upload File .CRA", align="left")
    uploaded = st.file_uploader("Pilih file radiosonde .CRA", type=["CRA", "cra"])

    if uploaded is None:
        st.markdown('<div class="upload-hint">Silakan unggah file .CRA untuk memulai analisis.</div>',
                    unsafe_allow_html=True)
        return None

    raw = uploaded.read()
    rsdata = parse_cra_bytes(raw)
    analysis = run_full_analysis(rsdata)
    header = analysis["header"]

    page_header("Informasi dan Profil Data Radiosonde", align="left")

    c1, c2, c3 = st.columns([1, 1.3, 1])

    with c1:
        section_header("Informasi Observasi")
        st.markdown(f"""
        <div class="info-card">
            <table class="info-table">
                <tr><td><b>Tanggal</b></td><td>: {header['tanggal']}</td></tr>
                <tr><td><b>Waktu (UTC)</b></td><td>: {header['waktu_utc']}</td></tr>
                <tr><td><b>Stasiun</b></td><td>: {header['stasiun']}</td></tr>
                <tr><td><b>Indeks WMO</b></td><td>: {header['indeks_wmo']}</td></tr>
                <tr><td><b>Sonde ID</b></td><td>: {header['sonde_id']}</td></tr>
                <tr><td><b>Posisi</b></td><td>: {header['posisi_text']}</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        section_header("Informasi Penerbangan Balon")
        st.markdown(f"""
        <div class="info-card">
            <table class="info-table">
                <tr><td><b>Waktu Mulai</b></td><td>: {header['waktu_mulai']}</td></tr>
                <tr><td><b>Durasi</b></td><td>: {header['durasi_penerbangan']}</td></tr>
                <tr><td><b>Waktu Burst</b></td><td>: {header['waktu_burst']}</td></tr>
                <tr><td><b>Ketinggian Max</b></td><td>: {header['ketinggian_maksimum_m']} m</td></tr>
                <tr><td><b>Tekanan Min</b></td><td>: {header['tekanan_minimum_hpa']} hPa</td></tr>
                <tr><td><b>Alasan Terminasi</b></td><td>: {header['alasan_terminasi']}</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        section_header("Kondisi Permukaan")
        st.markdown(f"""
        <div class="info-card">
            <table class="info-table">
                <tr><td><b>Tekanan</b></td><td>: {header['tekanan_permukaan_hpa']} hPa</td></tr>
                <tr><td><b>Suhu</b></td><td>: {header['suhu_permukaan_c']} °C</td></tr>
                <tr><td><b>Kelembapan</b></td><td>: {header['kelembapan_relatif_permukaan']} %</td></tr>
                <tr><td><b>Kec. Angin</b></td><td>: {header['kecepatan_angin_permukaan_kt']} kt</td></tr>
                <tr><td><b>Arah Angin</b></td><td>: {header['arah_angin_permukaan_deg']}°</td></tr>
                <tr><td><b>PWAT</b></td><td>: {header['pwat_mm']} mm</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    page_header("Data Profil Vertikal", align="left")
    tabs = st.tabs(["Significant Points", "Standard Levels", "Particular Points",
                    "Additional, Regional and National Levels"])
    table_keys = ["significant_points", "standard_levels", "particular_points", "additional_levels"]
    rename_map = {
        "waktu_terbang": "Waktu Terbang (HHMMSS)", "ketinggian_m": "Ketinggian (m)",
        "tekanan_hpa": "Tekanan (hPa)", "suhu_c": "Suhu (°C)", "titik_embun_c": "Titik Embun (°C)",
        "kelembapan_rh": "Kelembapan Relatif (%)", "kecepatan_angin_kt": "Kecepatan Angin (kt)",
        "arah_angin_deg": "Arah Angin (°)", "indikator": "Indikator",
    }
    for tab, key in zip(tabs, table_keys):
        with tab:
            t = analysis["tables"].get(key, pd.DataFrame())
            st.dataframe(t.rename(columns=rename_map), width='stretch', height=300)

    # simpan ke database
    saved, msg = db.save_analysis(analysis)
    if saved:
        st.success(msg)
    else:
        st.warning(msg)

    return analysis

# ---------------------------------------------------------------------------
# HALAMAN 3: DASHBOARD ANALISIS RADIOSONDE
# ---------------------------------------------------------------------------

def render_dashboard(analysis):
    page_header("Analisis Radiosonde", align="left")

    df = analysis["profile_df"]
    stats = analysis["stats"]
    conv = analysis["convective_levels"]
    stab = analysis["stability_indices"]
    tropo = analysis["tropopause"]
    lapse_df = analysis["lapse_rate_table"]
    humid = analysis["humidity"]
    wind_table = analysis["wind_table"]
    shear = analysis["wind_shear_kt"]
    wdx = analysis["windex"]
    hodo = analysis["hodograph_df"]

    # ---- PROFIL VERTIKAL KONDISI ATMOSFER ----
    section_header("PROFIL VERTIKAL KONDISI ATMOSFER")
    st.pyplot(viz.fig_skewt(df), width='stretch')

    # ---- Profil vertikal seluruh parameter & arah angin — semua grafik
    # ditampilkan sekaligus (tanpa perlu dipilih satu-satu), grid 2 kolom
    # per baris mengikuti pola pada Dashboard Multi-Waktu ----
    subtitle("Profil Vertikal Parameter Meteorologi")
    parameter_list = ["Kecepatan Angin (kt)", "Kelembapan Relatif (%)", "Suhu (°C)",
                      "Tekanan (hPa)", "Titik Embun (°C)"]
    figs_profil_vertikal = [viz.fig_profil_vertikal_parameter(df, p) for p in parameter_list]
    figs_profil_vertikal.append(viz.fig_arah_angin_ketinggian(df))
    for i in range(0, len(figs_profil_vertikal), 2):
        grid_cols = st.columns(2, gap="medium")
        for col, f in zip(grid_cols, figs_profil_vertikal[i:i + 2]):
            with col:
                st.plotly_chart(f, width='stretch')

    # ---- Distribusi titik & Pilih Ketinggian — berdampingan ----
    dcol1, dcol2 = st.columns([1.3, 1], gap="medium")
    with dcol1:
        st.plotly_chart(viz.fig_distribusi_titik(analysis["tables"]["significant_points"]),
                        width='stretch')
    with dcol2:
        with st.container(border=True, key="kontrol_viz"):
            st.markdown('<div class="control-marker"></div>', unsafe_allow_html=True)
            subtitle("Pilih Ketinggian untuk Nilai Parameter")
            opsi_ketinggian = sorted(df["ketinggian_m"].dropna().unique().tolist())
            ketinggian_pilih = st.selectbox("Ketinggian (m)", opsi_ketinggian, index=0)

    baris = df.iloc[(df["ketinggian_m"] - ketinggian_pilih).abs().argsort()[:1]].iloc[0]
    subtitle("Nilai Parameter Pada Ketinggian Terpilih")
    v1, v2, v3, v4, v5 = st.columns(5)
    with v1:
        custom_metric("Kecepatan Angin (kt)", f"{baris['kecepatan_angin_kt']:.2f}")
    with v2:
        custom_metric("Kelembapan Relatif (%)", f"{baris['kelembapan_rh']:.2f}")
    with v3:
        custom_metric("Suhu (°C)", f"{baris['suhu_c']:.2f}")
    with v4:
        custom_metric("Tekanan (hPa)", f"{baris['tekanan_hpa']:.2f}")
    with v5:
        custom_metric("Titik Embun (°C)", f"{baris['titik_embun_c']:.2f}")
    note_box("Jika belum memilih ketinggian, nilai parameter yang ditampilkan merupakan nilai pada ketinggian minimum.")

    st.divider()

    # ---- STATISTIK DATA RADIOSONDE ----
    section_header("STATISTIK DATA RADIOSONDE")
    baris_stat = [
        ("Suhu Max (°C)", f"{stats['suhu_max']:.2f}"),
        ("Suhu Min (°C)", f"{stats['suhu_min']:.2f}"),
        ("Titik Embun Max (°C)", f"{stats['titik_embun_max']:.2f}"),
        ("Titik Embun Min (°C)", f"{stats['titik_embun_min']:.2f}"),
        ("Tekanan Max (hPa)", f"{stats['tekanan_max']:.2f}"),
        ("Tekanan Min (hPa)", f"{stats['tekanan_min']:.2f}"),
        ("Kelembapan Max (%)", f"{stats['rh_max']:.2f}"),
        ("Kelembapan Min (%)", f"{stats['rh_min']:.2f}"),
        ("Ketinggian Max (km)", f"{stats['ketinggian_max']/1000:.2f}"),
        ("Ketinggian Min (km)", f"{stats['ketinggian_min']/1000:.2f}"),
        ("Kec. Angin Max (kt)", f"{stats['kecepatan_angin_max']:.2f}"),
        ("Kec. Angin Min (kt)", f"{stats['kecepatan_angin_min']:.2f}"),
    ]
    for i in range(0, len(baris_stat), 4):
        grid = st.columns(4, gap="medium")
        for col, (label, value) in zip(grid, baris_stat[i:i + 4]):
            with col:
                custom_metric(label, value)
    ma1, ma2, ma3 = st.columns([1, 1, 1])
    with ma2:
        custom_metric("Arah Angin Dominan", stats["arah_angin_dominan"])

    st.divider()

    # ---- LEVEL KONVEKSI, TROPOPAUSE, STABILITAS ----
    section_header("LEVEL KONVEKSI ATMOSFER")
    l1, l2, l3, l4 = st.columns(4)
    with l1:
        custom_metric("LCL (hPa)", f"{conv['lcl_hpa']:.2f}" if conv["lcl_hpa"] else "--", DEFINISI["lcl"])
    with l2:
        custom_metric("CCL (hPa)", f"{conv['ccl_hpa']:.2f}" if conv["ccl_hpa"] else "--", DEFINISI["ccl"])
    with l3:
        custom_metric("LFC (hPa)", f"{conv['lfc_hpa']:.2f}" if conv["lfc_hpa"] else "--", DEFINISI["lfc"])
    with l4:
        custom_metric("EL (hPa)", f"{conv['el_hpa']:.2f}" if conv["el_hpa"] else "--", DEFINISI["el"])
    insight_box(itp.insight_konveksi(conv))

    st.divider()

    section_header("TROPOPAUSE")
    t1, t2, t3 = st.columns(3)
    with t1:
        custom_metric("Estimasi Tropopause Primer (km)",
             f"{tropo['estimasi_tropopause_primer_km']:.2f}" if tropo["estimasi_tropopause_primer_km"] else "--",
             DEFINISI["tropopause"])
    with t2:
        custom_metric("Tropopause Primer (km)",
             f"{tropo['tropopause_primer_km']:.2f}" if tropo["tropopause_primer_km"] else "--",
             DEFINISI["tropopause"])
    with t3:
        custom_metric("Tropopause Sekunder (km)",
             f"{tropo['tropopause_sekunder_km']:.2f}" if tropo["tropopause_sekunder_km"] else "--",
             DEFINISI["tropopause"])

    st.divider()

    section_header("PARAMETER STABILITAS ATMOSFER")
    fig_cape, fig_cin = viz.fig_cape_cin_bar(stab)
    cc1, cc2 = st.columns(2)
    cc1.plotly_chart(fig_cape, width='stretch')
    cc2.plotly_chart(fig_cin, width='stretch')
    cape_help, cin_help = st.columns(2)
    with cape_help.popover("❓ Apa itu CAPE?", width='stretch'):
        st.markdown(DEFINISI["cape"])
    with cin_help.popover("❓ Apa itu CIN?", width='stretch'):
        st.markdown(DEFINISI["cin"])
    mu_help, ml_help, sb_help = st.columns(3)
    with mu_help.popover("❓ Apa itu MU?", width='stretch'):
        st.markdown(DEFINISI["mu"])
    with ml_help.popover("❓ Apa itu ML?", width='stretch'):
        st.markdown(DEFINISI["ml"])
    with sb_help.popover("❓ Apa itu SB?", width='stretch'):
        st.markdown(DEFINISI["sb"])
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        custom_metric("K Index (°C)", f"{stab['k_index']:.2f}" if stab["k_index"] is not None else "--", DEFINISI["k_index"])
    with k2:
        custom_metric("LI (°C)", f"{stab['lifted_index']:.2f}" if stab["lifted_index"] is not None else "--", DEFINISI["li"])
    with k3:
        custom_metric("TT (°C)", f"{stab['total_totals']:.2f}" if stab["total_totals"] is not None else "--", DEFINISI["tt"])
    with k4:
        custom_metric("SI (°C)", f"{stab['showalter_index']:.2f}" if stab["showalter_index"] is not None else "--", DEFINISI["si"])
    insight_box(itp.insight_stabilitas(stab))

    st.divider()

    # ---- LAPSE RATE & INVERSI ----
    section_header("ANALISIS LAPSE RATE & INVERSI")
    lr_help, inv_help, stab_help = st.columns(3)
    with lr_help.popover("❓ Apa itu Lapse Rate?", width='stretch'):
        st.markdown(DEFINISI["lapse_rate"])
    with inv_help.popover("❓ Apa itu Inversi?", width='stretch'):
        st.markdown(DEFINISI["inversi"])
    with stab_help.popover("❓ Apa itu Stabilitas Lapisan?", width='stretch'):
        st.markdown(DEFINISI["stabilitas_lapisan"])

    # Kolom kiri: grafik lapse rate + catatannya di bawahnya.
    # Kolom kanan: donut stabilitas + bar status inversi di bawahnya —
    # jadi catatan (kiri) sejajar dengan bar status inversi (kanan).
    lc1, lc2 = st.columns([1.3, 1])
    with lc1:
        st.plotly_chart(viz.fig_lapse_rate(lapse_df), width='stretch')
        note_box(itp.insight_lapse_rate_note())
    with lc2:
        st.plotly_chart(viz.fig_donut_stabilitas(lapse_df), width='stretch')
        st.plotly_chart(viz.fig_bar_status_inversi(lapse_df), width='stretch')

    subtitle("Tabel Ketinggian, Suhu, Lapse Rate, Status Inversi, dan Stabilitas Lapisan")
    tabel_lapse = lapse_df.rename(columns={
        "ketinggian_km": "Ketinggian (km)", "suhu_c": "Suhu (°C)",
        "lapse_rate": "Lapse Rate (°C/km)", "status_inversi": "Status Inversi",
        "stabilitas_lapisan": "Stabilitas Lapisan"})
    st.dataframe(tabel_lapse, width='stretch', height=220)

    st.divider()

    # ---- KELEMBAPAN ----
    section_header("KARAKTERISTIK KELEMBAPAN ATMOSFER")
    dpd_help, mr_help = st.columns(2)
    with dpd_help.popover("❓ Apa itu Depresi Titik Embun (DPD)?", width='stretch'):
        st.markdown(DEFINISI["dpd"])
    with mr_help.popover("❓ Apa itu Mixing Ratio?", width='stretch'):
        st.markdown(DEFINISI["mixing_ratio"])

    fig_dpd, fig_rh, fig_mr = viz.fig_humidity_lines(df)
    st.plotly_chart(fig_dpd, width='stretch')
    st.plotly_chart(fig_rh, width='stretch')
    st.plotly_chart(fig_mr, width='stretch')
    h1, h2, h3, h4 = st.columns(4)
    with h1:
        custom_metric("RH Mean 1000-700 (%)", f"{humid['rh_mean_1000_700']:.2f}" if humid["rh_mean_1000_700"] == humid["rh_mean_1000_700"] else "--")
    with h2:
        custom_metric("Mean DPD 1000-700 (°C)", f"{humid['dpd_mean_1000_700']:.2f}" if humid["dpd_mean_1000_700"] == humid["dpd_mean_1000_700"] else "--")
    with h3:
        custom_metric("Surface Mixing Ratio (g/kg)", f"{humid['surface_mixing_ratio']:.2f}" if humid["surface_mixing_ratio"] else "--")
    with h4:
        custom_metric("PWAT (mm)", f"{humid['pwat_mm']:.2f}" if humid["pwat_mm"] else "--")
    insight_box(itp.insight_kelembapan(humid))

    st.divider()

    # ---- ANGIN ----
    section_header("KARAKTERISTIK ANGIN ATMOSFER")
    wc1, wc2 = st.columns([1.4, 1])
    with wc1:
        st.plotly_chart(viz.fig_kecepatan_angin_tekanan(df), width='stretch')
    with wc2:
        subtitle("Arah dan Kecepatan Angin")
        st.dataframe(wind_table.rename(columns={
            "kategori_ketinggian": "Kategori Ketinggian", "arah_angin_dominan": "Arah Angin Dominan",
            "kecepatan_angin_kt": "Kecepatan Angin (kt)"}), width='stretch', hide_index=True)

    bc1, bc2 = st.columns([1.4, 1])
    with bc1:
        with st.container(key="wind_metrics_box"):
            w1, w2 = st.columns(2)
            with w1:
                custom_metric("Wind Shear (kt) (0-6 km)", f"{shear:.2f}" if shear == shear else "--", DEFINISI["shear"])
            with w2:
                custom_metric("WindEx (kt)", f"{wdx:.2f}" if wdx == wdx else "--", DEFINISI["windex"])
    with bc2:
        note_box(itp.insight_wind_rose_note(), extra_class="matched-note-box")

    insight_box(itp.insight_angin(shear, wind_table))

    st.divider()

    # ---- HODOGRAPH ----
    section_header("HODOGRAF ANGIN")
    st.plotly_chart(viz.fig_hodograph(hodo), width='stretch')
    insight_box(itp.insight_hodograph(hodo, shear))

    st.divider()

    # ---- INDEKS POTENSI CUACA BURUK ----
    section_header("INDEKS POTENSI CUACA BURUK")
    e1, e2 = st.columns(2)
    with e1:
        custom_metric("SWEAT Index", f"{stab['sweat_index']:.2f}" if stab["sweat_index"] is not None else "--", DEFINISI["sweat"])
    with e2:
        custom_metric("DCAPE (J/kg)", f"{stab['dcape']:.2f}" if stab["dcape"] is not None else "--", DEFINISI["dcape"])
    insight_box(itp.insight_cuaca_buruk(stab.get("sweat_index"), stab.get("dcape")))

    st.divider()

    # ---- KESIMPULAN — kotak PUTIH, sengaja dibedakan dari insight ----
    section_header("KESIMPULAN")
    conclusion_box(itp.kesimpulan_umum(stab, humid, stab.get("sweat_index"), stab.get("dcape")))

    st.divider()

    # ---- REKOMENDASI ARAH KEBIJAKAN ----
    page_header("Rekomendasi Arah Kebijakan", align="left")
    rekomendasi = pol.build_policy_recommendations(analysis)
    baris1 = st.columns(3)
    baris2 = st.columns(3)
    for col, (sektor, teks) in zip(baris1 + baris2, rekomendasi.items()):
        with col:
            section_header(sektor)
            st.markdown(f'<div class="policy-card">{teks}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# HALAMAN: DATABASE PARAMETER ATMOSFER
# ---------------------------------------------------------------------------

def render_database_page():
    st.title("Database Parameter Atmosfer")
    data = db.load_database()
    if data.empty:
        st.info("Belum ada data tersimpan. Unggah file .CRA pada halaman Analisis Radiosonde.")
        return
    rename_map = {
        "tanggal": "Tanggal", "lcl_hpa": "LCL", "ccl_hpa": "CCL", "lfc_hpa": "LFC", "el_hpa": "EL",
        "cape_sb": "SBCAPE", "cape_ml": "MLCAPE", "cape_mu": "MUCAPE",
        "cin_sb": "SBCIN", "cin_ml": "MLCIN", "cin_mu": "MUCIN",
        "k_index": "K Index", "lifted_index": "LI", "showalter_index": "SI", "total_totals": "TT",
        "sweat_index": "SWEAT", "dcape": "DCAPE", "pwat_mm": "PWAT",
        "wind_shear_kt": "Wind Shear (kt)", "windex": "WindEx",
    }
    cols = list(rename_map.keys())
    st.dataframe(data[cols].rename(columns=rename_map), width='stretch', hide_index=True)

    st.download_button("Unduh Database (CSV)", data.to_csv(index=False).encode("utf-8"),
                       file_name="database_parameter_atmosfer.csv", mime="text/csv")

    with st.expander("Hapus data tanggal tertentu"):
        tanggal_hapus = st.selectbox("Pilih tanggal", data["tanggal"].tolist())
        if st.button("Hapus"):
            db.delete_date(tanggal_hapus)
            st.rerun()


# ---------------------------------------------------------------------------
# HALAMAN: DASHBOARD MULTI-WAKTU & REKOMENDASI KEBIJAKAN
# ---------------------------------------------------------------------------

def render_multiwaktu_page():
    st.title("Dashboard Analisis Radiosonde Multi-Waktu & Rekomendasi Arah Kebijakan")
    data = db.load_database()
    if data.empty or len(data) < 2:
        st.info("Minimal diperlukan 2 data (tanggal berbeda) untuk analisis multi-waktu. "
                "Silakan unggah lebih banyak file .CRA pada halaman Analisis Radiosonde.")
        return

    data = data.sort_values("tanggal")
    tanggal_range = st.multiselect("Pilih tanggal yang dibandingkan", data["tanggal"].tolist(),
                                    default=data["tanggal"].tolist())
    d = data[data["tanggal"].isin(tanggal_range)].sort_values("tanggal")
    if d.empty:
        st.warning("Pilih minimal satu tanggal.")
        return

    import plotly.graph_objects as go

    def _line_fig(y_col, label, color, yaxis_title, reversed_axis=False):
        """Satu grafik garis untuk satu parameter saja (bukan gabungan)."""
        f = go.Figure()
        f.add_trace(go.Scatter(x=d["tanggal"], y=d[y_col], mode="lines+markers",
                               name=label, line=dict(color=color)))
        f.update_layout(xaxis_title="Tanggal", yaxis_title=yaxis_title,
                        title=dict(text=label, x=0.5, xanchor="center"),
                        height=340, **viz.PLOTLY_LAYOUT)
        if reversed_axis:
            f.update_yaxes(autorange="reversed")
        return f

    def _bar_fig(y_col, label, color, yaxis_title):
        """Satu grafik batang untuk satu parameter saja."""
        f = go.Figure()
        f.add_trace(go.Bar(x=d["tanggal"], y=d[y_col], name=label, marker_color=color))
        f.update_layout(xaxis_title="Tanggal", yaxis_title=yaxis_title,
                        title=dict(text=label, x=0.5, xanchor="center"),
                        height=340, **viz.PLOTLY_LAYOUT)
        return f

    def _render_grid(figs):
        """Tata sejumlah grafik dalam grid 2 kolom (baris demi baris)."""
        for i in range(0, len(figs), 2):
            cols = st.columns(2)
            for col, f in zip(cols, figs[i:i + 2]):
                with col:
                    st.plotly_chart(f, width='stretch')

    section_header("TREN LEVEL KONVEKSI (LCL, CCL, LFC, EL)")
    figs_konveksi = [
        _line_fig("lcl_hpa", "Lifting Condensation Level (hPa)", viz.PINK_UTAMA, "Tekanan (hPa)", reversed_axis=True),
        _line_fig("ccl_hpa", "Convective Condensation Level (hPa)", viz.BIRU, "Tekanan (hPa)", reversed_axis=True),
        _line_fig("lfc_hpa", "Level of Free Convection (hPa)", viz.BIRU_MUDA, "Tekanan (hPa)", reversed_axis=True),
        _line_fig("el_hpa", "Equilibrium Level (hPa)", viz.PINK_GELAP, "Tekanan (hPa)", reversed_axis=True),
    ]
    _render_grid(figs_konveksi)

    st.divider()

    section_header("TREN CAPE & CIN (MOST UNSTABLE)")
    figs_cape_cin = [
        _bar_fig("cape_mu", "MUCAPE (J/kg)", viz.PINK_UTAMA, "MUCAPE (J/kg)"),
        _line_fig("cin_mu", "MUCIN (J/kg)", viz.BIRU_TUA, "MUCIN (J/kg)"),
    ]
    _render_grid(figs_cape_cin)

    st.divider()

    section_header("TREN INDEKS STABILITAS (K INDEX, LI, TT, SI, SWEAT)")
    figs_stabilitas = [
        _line_fig("k_index", "K Index", viz.PINK_UTAMA, "Nilai Indeks"),
        _line_fig("lifted_index", "Lifted Index", viz.BIRU, "Nilai Indeks"),
        _line_fig("total_totals", "Total Totals", viz.BIRU_MUDA, "Nilai Indeks"),
        _line_fig("showalter_index", "Showalter Index", viz.PINK_GELAP, "Nilai Indeks"),
        _line_fig("sweat_index", "SWEAT Index", viz.PINK_ROSE, "Nilai Indeks"),
    ]
    _render_grid(figs_stabilitas)

    st.divider()

    section_header("TREN KELEMBAPAN (PWAT & RH RATA-RATA 1000-700 hPa)")
    figs_kelembapan = [
        _bar_fig("pwat_mm", "PWAT (mm)", viz.PINK_UTAMA, "PWAT (mm)"),
        _line_fig("rh_mean_1000_700", "RH Mean 1000-700 (%)", viz.BIRU_TUA, "RH Mean 1000-700 (%)"),
    ]
    _render_grid(figs_kelembapan)

    st.divider()

    section_header("TREN WIND SHEAR & WINDEX")
    figs_angin = [
        _line_fig("wind_shear_kt", "Wind Shear (kt)", viz.PINK_UTAMA, "Kecepatan (kt)"),
        _line_fig("windex", "WindEx (kt)", viz.BIRU_TUA, "Kecepatan (kt)"),
    ]
    _render_grid(figs_angin)

    # ringkasan tren sederhana untuk kebijakan
    st.subheader("Rekomendasi Arah Kebijakan Berdasarkan Tren Multi-Waktu")
    tren_cape = d["cape_mu"].iloc[-1] - d["cape_mu"].iloc[0] if len(d) > 1 else 0
    tren_pwat = d["pwat_mm"].iloc[-1] - d["pwat_mm"].iloc[0] if len(d) > 1 else 0

    if tren_cape > 0 and tren_pwat > 0:
        narasi = ("Tren MUCAPE dan PWAT menunjukkan peningkatan dari periode observasi pertama hingga "
                  "terakhir, mengindikasikan potensi konveksi dan curah hujan yang cenderung meningkat.")
        arahan = ("Instansi terkait disarankan meningkatkan kesiapsiagaan menghadapi potensi cuaca buruk, "
                  "khususnya untuk sektor mitigasi bencana hidrometeorologi dan pengelolaan sumber daya air.")
    elif tren_cape < 0 and tren_pwat < 0:
        narasi = ("Tren MUCAPE dan PWAT menunjukkan penurunan dari periode observasi pertama hingga "
                  "terakhir, mengindikasikan kondisi atmosfer yang cenderung semakin stabil dan kering.")
        arahan = ("Sektor pertanian dan pengelolaan sumber daya air disarankan mengantisipasi periode "
                  "dengan curah hujan yang lebih terbatas.")
    else:
        narasi = "Tren parameter konvektif dan kelembapan menunjukkan variasi yang beragam antar periode observasi."
        arahan = "Pemantauan berkelanjutan tetap diperlukan untuk menangkap perubahan kondisi atmosfer secara lebih akurat."

    insight_box(narasi + " " + arahan)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    st.sidebar.markdown(
    '<div class="sidebar-title-box">Analisis Radiosonde</div>',
    unsafe_allow_html=True
)
    halaman = st.sidebar.radio("Navigasi", [
        "Analisis Radiosonde (Single Time)",
        "Database Parameter Atmosfer",
        "Dashboard Multi-Waktu",
    ], label_visibility="collapsed")

    if halaman == "Analisis Radiosonde (Single Time)":
        analysis = render_upload_and_profile()
        if analysis is not None:
            st.divider()
            render_dashboard(analysis)
    elif halaman == "Database Parameter Atmosfer":
        render_database_page()
    else:
        render_multiwaktu_page()


if __name__ == "__main__":
    main()