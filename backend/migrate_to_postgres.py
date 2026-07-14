"""
JSON dosyalarindaki mevcut veriyi PostgreSQL'e aktarir.
Tum islem TEK bir transaction icinde yapilir: satir sayilari orijinal JSON
kayit sayilariyla eslesmezse ROLLBACK yapilir, hicbir sey commit edilmez.

Calistirma (docker compose network icinden, backend imaji ile):
    docker compose run --rm backend python migrate_to_postgres.py
"""
import json
import os
import sys

import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")
BASE = os.path.dirname(__file__)


def load_json(name, default):
    path = os.path.join(BASE, name)
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    if not DATABASE_URL:
        print("HATA: DATABASE_URL tanimli degil, migration calistirilamiyor.")
        sys.exit(1)

    ekip_json = load_json("ekip.json", [])
    firsatlar_json = load_json("firsatlar.json", [])
    projeler_json = load_json("projeler.json", [])
    tasklar_json = load_json("tasklar.json", [])
    basvurular_json = load_json("basvurular.json", {})

    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        # sema garanti olsun
        schema_path = os.path.join(BASE, "schema.sql")
        with open(schema_path, encoding="utf-8") as f:
            cur.execute(f.read())

        # mevcut veriyi temizle (idempotent yeniden calistirma icin)
        cur.execute("TRUNCATE sudola_onerileri, basvurular, tasklar, proje_dosyalar, proje_notlar, projeler, firsatlar, ekip RESTART IDENTITY CASCADE")

        # ---- EKIP ----
        isimler = set(ekip_json)
        for t in tasklar_json:
            atanan = t.get("atanan")
            if atanan:
                isimler.add(atanan)
        isim_to_id = {}
        for isim in sorted(isimler):
            cur.execute("INSERT INTO ekip (isim) VALUES (%s) RETURNING id", (isim,))
            isim_to_id[isim] = cur.fetchone()[0]

        # ---- FIRSATLAR ----
        link_to_id = {}
        for f in firsatlar_json:
            cur.execute(
                """INSERT INTO firsatlar
                (link, baslik, kaynak_sorgu, bulunma_tarihi, organizator, konu_kategori,
                 son_basvuru_tarihi, onemli_tarihler, basvuru_asamalari, yer_mekan,
                 konaklama_yol_destegi, odul_miktari_turu, katilim_sartlari,
                 takim_buyuklugu_limiti, basvuru_maliyeti, istenen_materyal,
                 sponsor_kurumlar, extraction_durumu, extraction_tarihi, efor_seviyesi, kaynak)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING id""",
                (
                    f.get("link"), f.get("baslik"), f.get("kaynak_sorgu"),
                    f.get("bulunma_tarihi") or None, f.get("organizator"), f.get("konu_kategori"),
                    f.get("son_basvuru_tarihi") or None, f.get("onemli_tarihler"),
                    f.get("basvuru_asamalari"), f.get("yer_mekan"),
                    f.get("konaklama_yol_destegi"), f.get("odul_miktari_turu"),
                    f.get("katilim_sartlari"), f.get("takim_buyuklugu_limiti"),
                    f.get("basvuru_maliyeti"), f.get("istenen_materyal"),
                    f.get("sponsor_kurumlar"), f.get("extraction_durumu"),
                    f.get("extraction_tarihi") or None,
                    f.get("efor_kazanc_seviyesi") or f.get("efor_seviyesi"),
                    f.get("kaynak") or "radar",
                ),
            )
        cur.execute("SELECT id, link FROM firsatlar")
        link_to_id = {link: fid for fid, link in cur.fetchall()}

        # ikinci gecis: duplicate_of (link) -> duplicate_of_id
        for f in firsatlar_json:
            dup_link = f.get("duplicate_of")
            if dup_link and dup_link in link_to_id:
                cur.execute(
                    "UPDATE firsatlar SET duplicate_of_id=%s WHERE link=%s",
                    (link_to_id[dup_link], f.get("link")),
                )

        # ---- PROJELER (+ notlar + dosyalar) ----
        for p in projeler_json:
            import uuid as _uuid
            proje_id = p.get("id") or _uuid.uuid4().hex[:12]
            cur.execute(
                """INSERT INTO projeler (id, ad, aciklama, github_link, durum, olusturma_tarihi)
                VALUES (%s,%s,%s,%s,%s,%s)""",
                (proje_id, p.get("ad"), p.get("aciklama"), p.get("github_link"), p.get("durum"),
                 p.get("olusturma_tarihi") or None),
            )
            for n in p.get("notlar", []):
                cur.execute(
                    "INSERT INTO proje_notlar (proje_id, tarih, metin) VALUES (%s,%s,%s)",
                    (proje_id, n.get("tarih") or None, n.get("metin")),
                )
            for d in p.get("dosyalar", []):
                cur.execute(
                    "INSERT INTO proje_dosyalar (proje_id, dosya_adi, yuklenme_tarihi, boyut) VALUES (%s,%s,%s,%s)",
                    (proje_id, d.get("ad"), d.get("tarih") or None, d.get("boyut")),
                )

        # ---- TASKLAR ----
        for t in tasklar_json:
            atanan_id = isim_to_id.get(t.get("atanan"))
            cur.execute(
                """INSERT INTO tasklar (baslik, atanan_id, tur, deadline, durum, olusturma_tarihi)
                VALUES (%s,%s,%s,%s,%s,%s)""",
                (t.get("baslik"), atanan_id, t.get("tur"), t.get("deadline") or None,
                 t.get("durum"), t.get("olusturma_tarihi") or None),
            )

        # ---- BASVURULAR ----
        for link, b in basvurular_json.items():
            firsat_id = link_to_id.get(link)
            if firsat_id is None:
                raise RuntimeError(f"basvuru icin firsat bulunamadi: {link}")
            cur.execute(
                "INSERT INTO basvurular (firsat_id, durum) VALUES (%s,%s)",
                (firsat_id, b.get("durum")),
            )

        # ---- DOGRULAMA ----
        checks = []

        cur.execute("SELECT count(*) FROM ekip")
        checks.append(("ekip", cur.fetchone()[0], len(isimler)))

        cur.execute("SELECT count(*) FROM firsatlar")
        checks.append(("firsatlar", cur.fetchone()[0], len(firsatlar_json)))

        cur.execute("SELECT count(*) FROM projeler")
        checks.append(("projeler", cur.fetchone()[0], len(projeler_json)))

        cur.execute("SELECT count(*) FROM tasklar")
        checks.append(("tasklar", cur.fetchone()[0], len(tasklar_json)))

        cur.execute("SELECT count(*) FROM basvurular")
        checks.append(("basvurular", cur.fetchone()[0], len(basvurular_json)))

        print("--- MIGRATION SONUCLARI ---")
        hata_var = False
        for tablo, gercek, beklenen in checks:
            durum = "OK" if gercek == beklenen else "HATA"
            if gercek != beklenen:
                hata_var = True
            print(f"{tablo}: db={gercek} json={beklenen} [{durum}]")

        if hata_var:
            conn.rollback()
            print("MIGRATION BASARISIZ - satir sayilari eslesmiyor, ROLLBACK yapildi.")
            sys.exit(1)
        else:
            conn.commit()
            print("MIGRATION BASARILI - commit edildi.")
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
