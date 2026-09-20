"""
policy.py
Menghasilkan rekomendasi arah kebijakan lintas sektor berdasarkan hasil
analisis kondisi atmosfer. Enam sektor mengikuti kebutuhan dashboard:
Mitigasi Bencana Hidrometeorologi, Pengelolaan Sumber Daya Air, Penerbangan,
Pertanian, Tata Ruang, dan Penguatan Sistem Observasi.
"""

from __future__ import annotations


def _labil_score(stab: dict) -> int:
    k = stab.get("k_index")
    tt = stab.get("total_totals")
    li = stab.get("lifted_index")
    cape_mu = stab.get("cape_mu") or 0
    return sum([
        1 if (k is not None and k >= 30) else 0,
        1 if (tt is not None and tt >= 50) else 0,
        1 if (li is not None and li <= -2) else 0,
        1 if cape_mu > 500 else 0,
    ])


def build_policy_recommendations(analysis: dict) -> dict:
    stab = analysis["stability_indices"]
    humid = analysis["humidity"]
    shear = analysis.get("wind_shear_kt")
    score = _labil_score(stab)
    pwat = humid.get("pwat_mm") or 0
    tinggi_shear = shear == shear and shear >= 25

    rekomendasi = {}

    if score >= 3:
        rekomendasi["Mitigasi Bencana Hidrometeorologi"] = (
            "Tingkatkan kesiapsiagaan terhadap potensi hujan lebat, petir, dan angin kencang. "
            "Koordinasikan peringatan dini dengan BPBD setempat dan siapkan jalur evakuasi di "
            "wilayah rawan banjir atau longsor.")
    elif score >= 1:
        rekomendasi["Mitigasi Bencana Hidrometeorologi"] = (
            "Pertahankan pemantauan rutin kondisi atmosfer karena masih terdapat energi konvektif "
            "meskipun potensi cuaca ekstrem tergolong rendah. Perbarui informasi prakiraan cuaca secara berkala.")
    else:
        rekomendasi["Mitigasi Bencana Hidrometeorologi"] = (
            "Kondisi atmosfer relatif stabil sehingga risiko cuaca ekstrem rendah. Pemantauan rutin "
            "tetap perlu dilakukan sebagai langkah antisipasi dini.")

    if pwat >= 40:
        rekomendasi["Pengelolaan Sumber Daya Air"] = (
            "Kandungan uap air kolom atmosfer cukup tinggi sehingga berpotensi mendukung curah hujan. "
            "Manfaatkan periode ini untuk optimalisasi tampungan air dan pemeliharaan infrastruktur drainase.")
    else:
        rekomendasi["Pengelolaan Sumber Daya Air"] = (
            "Kandungan uap air kolom atmosfer relatif terbatas. Disarankan melakukan efisiensi "
            "penggunaan air dan pemantauan ketersediaan sumber air baku secara berkala.")

    if tinggi_shear or score >= 3:
        rekomendasi["Penerbangan"] = (
            "Waspadai potensi turbulensi dan wind shear pada lapisan tertentu yang dapat memengaruhi "
            "fase lepas landas dan pendaratan. Informasikan kondisi ini kepada otoritas bandar udara terkait.")
    else:
        rekomendasi["Penerbangan"] = (
            "Kondisi angin dan turbulensi vertikal relatif terkendali, namun pembaruan informasi cuaca "
            "penerbangan (METAR/TAF) tetap perlu dipantau menjelang operasional penerbangan.")

    if score >= 1 and pwat >= 30:
        rekomendasi["Pertanian"] = (
            "Potensi hujan yang cukup dapat dimanfaatkan untuk aktivitas tanam. Petani disarankan "
            "menyesuaikan jadwal tanam dan mewaspadai risiko genangan pada lahan rendah.")
    else:
        rekomendasi["Pertanian"] = (
            "Potensi hujan relatif terbatas dalam waktu dekat. Disarankan mengoptimalkan sistem irigasi "
            "dan memilih komoditas yang lebih tahan terhadap kondisi kering.")

    rekomendasi["Tata Ruang"] = (
        "Data profil atmosfer ini dapat menjadi salah satu masukan dalam evaluasi risiko iklim mikro "
        "wilayah, khususnya terkait perencanaan kawasan yang rentan terhadap cuaca ekstrem atau genangan.")

    rekomendasi["Penguatan Sistem Observasi"] = (
        "Lanjutkan pengamatan radiosonde secara berkala untuk membangun basis data profil atmosfer yang "
        "lebih panjang, guna meningkatkan akurasi analisis tren dan validasi model cuaca numerik di wilayah ini.")

    return rekomendasi