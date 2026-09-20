"""
interpretation.py
Menghasilkan narasi insight otomatis berbahasa Indonesia berdasarkan nilai
hasil analisis (calculation.py). Ambang batas (threshold) yang dipakai
mengacu pada kriteria operasional yang umum dipakai di analisis sinoptik
(George 1960 untuk K-Index, kriteria Total Totals & Showalter Index umum,
serta kriteria SWEAT Miller 1972). Karena beberapa ambang batas ini berbeda
tipis antar referensi, kategorisasi di bawah bersifat estimasi operasional,
bukan nilai baku tunggal.
"""

from __future__ import annotations


def _fmt(v, nd=2):
    if v is None:
        return "--"
    try:
        return f"{v:.{nd}f}"
    except (TypeError, ValueError):
        return str(v)


def insight_konveksi(conv: dict) -> str:
    lcl, ccl, lfc, el = conv.get("lcl_hpa"), conv.get("ccl_hpa"), conv.get("lfc_hpa"), conv.get("el_hpa")
    if lcl is None and ccl is None:
        return "Data tidak mencukupi untuk menentukan level kondensasi udara."
    if lfc is None and el is None:
        return ("Udara mulai berpotensi membentuk awan pada LCL dan CCL. Namun, karena LFC dan EL "
                "tidak tercapai, awan yang terbentuk cenderung tidak berkembang menjadi awan "
                "konvektif yang tinggi.")
    if lfc is not None and el is None:
        return ("Udara berpotensi membentuk awan pada LCL dan CCL, dan parsel udara mampu mencapai "
                "LFC sehingga konveksi dapat berkembang secara bebas. Karena EL belum teridentifikasi "
                "dengan jelas, tinggi maksimum perkembangan awan konvektif masih belum dapat dipastikan.")
    return ("Udara berpotensi membentuk awan pada LCL dan CCL, dan mampu berkembang bebas melewati "
            "LFC hingga mencapai EL. Kondisi ini mendukung perkembangan awan konvektif yang cukup tinggi.")


def insight_stabilitas(stab: dict) -> str:
    k = stab.get("k_index")
    li = stab.get("lifted_index")
    tt = stab.get("total_totals")
    si = stab.get("showalter_index")
    cape_mu = stab.get("cape_mu") or 0
    cin_sb = stab.get("cin_sb")

    skor_labil = 0
    if k is not None and k >= 30:
        skor_labil += 1
    if li is not None and li <= -2:
        skor_labil += 1
    if tt is not None and tt >= 50:
        skor_labil += 1
    if si is not None and si <= -1:
        skor_labil += 1

    if skor_labil >= 3:
        kondisi = "Atmosfer cenderung labil dengan potensi konveksi kuat."
    elif skor_labil >= 1:
        kondisi = "Atmosfer cenderung stabil hingga sedikit labil."
    else:
        kondisi = "Atmosfer cenderung stabil."

    tambahan = ""
    if cape_mu and cape_mu > 100:
        tambahan = " Meskipun terdapat energi konvektif pada lapisan paling tidak stabil,"
        if cin_sb is not None and cin_sb < -100:
            tambahan += " hambatan konveksi dari permukaan masih cukup besar sehingga potensi konveksi kuat relatif rendah."
        else:
            tambahan += " hambatan konveksi dari permukaan relatif kecil sehingga energi tersebut berpeluang lebih mudah terlepas."
    elif cin_sb is not None and cin_sb < -100:
        tambahan = " Hambatan konveksi (CIN) dari permukaan cukup besar sehingga inisiasi awan konvektif dari permukaan menjadi lebih sulit."

    return kondisi + tambahan


def insight_kelembapan(humid: dict) -> str:
    rh = humid.get("rh_mean_1000_700")
    pwat = humid.get("pwat_mm")

    if rh is None or pwat is None:
        return "Data kelembapan tidak mencukupi untuk dianalisis."

    if rh >= 80:
        rh_label = "tinggi"
    elif rh >= 50:
        rh_label = "sedang"
    else:
        rh_label = "rendah"

    if pwat >= 50:
        pwat_label = "tinggi"
    elif pwat >= 30:
        pwat_label = "cukup tinggi"
    else:
        pwat_label = "rendah"

    return (f"Kelembapan lapisan bawah atmosfer tergolong {rh_label}, sementara kandungan uap air di "
            f"kolom atmosfer {pwat_label}. Kondisi ini menunjukkan "
            f"{'ketersediaan uap air yang memadai' if pwat_label != 'rendah' else 'keterbatasan uap air'} "
            "untuk mendukung pembentukan awan apabila didukung oleh kondisi atmosfer dan mekanisme "
            "pengangkatan yang sesuai.")


def insight_angin(wind_shear_kt: float, wind_table) -> str:
    if wind_shear_kt != wind_shear_kt:  # NaN check
        shear_label = "tidak dapat ditentukan"
    elif wind_shear_kt < 20:
        shear_label = "relatif rendah"
    elif wind_shear_kt < 35:
        shear_label = "sedang"
    else:
        shear_label = "cukup tinggi"

    trend = ""
    try:
        speeds = wind_table["kecepatan_angin_kt"].tolist()
        if len(speeds) >= 2 and speeds[-1] > speeds[0]:
            trend = "Kecepatan angin cenderung meningkat seiring bertambahnya ketinggian, disertai perubahan arah angin pada setiap lapisan atmosfer. "
        elif len(speeds) >= 2:
            trend = "Kecepatan angin bervariasi antar lapisan ketinggian, disertai perubahan arah angin pada setiap lapisan atmosfer. "
    except Exception:
        pass

    penjelasan_shear = {
        "relatif rendah": "menunjukkan perubahan angin vertikal yang tidak terlalu signifikan.",
        "sedang": "menunjukkan perubahan angin vertikal yang cukup mendukung organisasi awan konvektif.",
        "cukup tinggi": "menunjukkan perubahan angin vertikal yang signifikan dan dapat mendukung organisasi sistem konvektif kuat.",
        "tidak dapat ditentukan": "namun tidak dapat dievaluasi lebih lanjut karena keterbatasan data.",
    }[shear_label]

    return f"{trend}Nilai wind shear yang {shear_label} {penjelasan_shear}"


def insight_cuaca_buruk(sweat, dcape) -> str:
    if sweat is None:
        sweat_label = None
    elif sweat < 250:
        sweat_label = "rendah"
    elif sweat < 300:
        sweat_label = "sedang"
    elif sweat < 400:
        sweat_label = "tinggi"
    else:
        sweat_label = "sangat tinggi"

    if dcape is None:
        dcape_label = None
    elif dcape < 800:
        dcape_label = "rendah"
    elif dcape < 1500:
        dcape_label = "cukup"
    else:
        dcape_label = "tinggi"

    if sweat_label is None and dcape_label is None:
        return "Data indeks potensi cuaca buruk tidak mencukupi untuk dianalisis."

    if sweat_label in (None, "rendah", "sedang"):
        kesimpulan = "Potensi cuaca buruk masih relatif rendah."
    else:
        kesimpulan = "Potensi cuaca buruk cenderung meningkat dan perlu diwaspadai."

    tambahan = ""
    if dcape_label in ("cukup", "tinggi"):
        tambahan = (" Meskipun terdapat potensi arus turun di atmosfer, kondisi konveksi secara "
                    "keseluruhan belum cukup mendukung terbentuknya cuaca ekstrem." if kesimpulan.startswith("Potensi cuaca buruk masih")
                    else " Potensi arus turun (downdraft) yang kuat turut mendukung risiko angin kencang saat konveksi terjadi.")

    return kesimpulan + tambahan


def kesimpulan_umum(stab: dict, humid: dict, sweat, dcape) -> str:
    """Ringkasan akhir + rekomendasi paragraf kedua, gaya bahasa mengikuti
    contoh yang diberikan pengguna."""
    k = stab.get("k_index")
    tt = stab.get("total_totals")
    li = stab.get("lifted_index")
    cape_mu = stab.get("cape_mu") or 0
    pwat = humid.get("pwat_mm") or 0

    labil_score = sum([
        1 if (k is not None and k >= 30) else 0,
        1 if (tt is not None and tt >= 50) else 0,
        1 if (li is not None and li <= -2) else 0,
        1 if cape_mu > 500 else 0,
    ])
    lembap = pwat >= 40

    if labil_score >= 3:
        kalimat1 = "Kondisi atmosfer secara umum cenderung labil dengan potensi konveksi kuat dan mendukung pertumbuhan awan hujan yang signifikan."
        saran = ("Masyarakat dan instansi terkait disarankan untuk mewaspadai potensi hujan lebat disertai "
                 "petir dan angin kencang, serta memantau perkembangan cuaca secara berkala.")
    elif labil_score >= 1 or lembap:
        kalimat1 = ("Kondisi atmosfer secara umum cenderung stabil dengan kelembapan yang "
                    f"{'cukup' if lembap else 'terbatas'} untuk pembentukan awan. Namun, perkembangan "
                    "konveksi masih terbatas sehingga potensi cuaca buruk relatif rendah.")
        saran = ("Masyarakat dapat beraktivitas seperti biasa, namun tetap disarankan memantau informasi "
                 "prakiraan cuaca terkini sebagai langkah antisipasi terhadap perubahan kondisi atmosfer.")
    else:
        kalimat1 = "Kondisi atmosfer secara umum stabil dan kering, sehingga potensi pertumbuhan awan hujan signifikan relatif kecil."
        saran = ("Masyarakat dapat beraktivitas seperti biasa. Untuk sektor yang bergantung pada curah hujan, "
                 "kondisi ini perlu diantisipasi dengan pengelolaan sumber daya air yang lebih hati-hati.")

    return kalimat1 + " " + saran


def insight_lapse_rate_note() -> str:
    return ("Beberapa lonjakan tajam pada grafik di atas bisa terjadi karena jarak antar data pengukuran "
            "yang tidak sama rata, bukan berarti selalu ada perubahan suhu ekstrem di ketinggian tersebut.")


def insight_wind_rose_note() -> str:
    return ("Arah angin dominan ditentukan melalui analisis wind rose berdasarkan distribusi frekuensi "
            "arah angin pada setiap sektor mata angin.")


def insight_hodograph(hodo_df, shear_kt: float) -> str:
    try:
        u0, v0 = hodo_df.iloc[0][["u_kt", "v_kt"]]
        u1, v1 = hodo_df.iloc[-1][["u_kt", "v_kt"]]
        belok = "searah jarum jam (mendukung adveksi udara hangat / veering)"
    except Exception:
        belok = "bervariasi"
    if shear_kt == shear_kt and shear_kt >= 20:
        organisasi = "cukup mendukung organisasi sel konvektif multisel hingga superseluler."
    else:
        organisasi = "kurang mendukung organisasi sel konvektif yang terorganisasi kuat."
    return (f"Pola hodograf menunjukkan perubahan arah dan kecepatan angin terhadap ketinggian yang {belok}. "
            f"Nilai wind shear yang teramati {organisasi}")