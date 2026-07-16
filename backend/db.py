import os
import json
import psycopg2
import psycopg2.extras

DATABASE_URL = os.getenv("DATABASE_URL")


def get_conn():
    return psycopg2.connect(DATABASE_URL)


def init_schema():
    if not DATABASE_URL:
        return
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, encoding="utf-8") as f:
        sql = f.read()
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    finally:
        conn.close()


def _row_to_dict(cur, row):
    cols = [d[0] for d in cur.description]
    return dict(zip(cols, row))


def _serialize(v):
    import datetime
    if isinstance(v, (datetime.datetime, datetime.date)):
        return v.isoformat()
    return v


def fetch_all(query, params=None):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            return [{c: _serialize(v) for c, v in zip(cols, r)} for r in rows]
    finally:
        conn.close()


def execute(query, params=None):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
        conn.commit()
    finally:
        conn.close()


def execute_returning(query, params=None):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            row = cur.fetchone()
            conn.commit()
            if row is None:
                return None
            cols = [d[0] for d in cur.description]
            return {c: _serialize(v) for c, v in zip(cols, row)}
    finally:
        conn.close()


# ============================================================
# JSON-uyumlu tablo bazli yukle/kaydet fonksiyonlari.
# Bunlar api.py / radar.py'deki dosya_oku/dosya_yaz cagrilarinin
# ayni sekli (list[dict] veya dict) donmesini/kabul etmesini saglar,
# boylece endpoint govdelerinde degisiklik gerekmez.
# ============================================================

_FIRSATLAR_COLS = [
    "link", "baslik", "kaynak_sorgu", "bulunma_tarihi", "organizator", "konu_kategori",
    "son_basvuru_tarihi", "onemli_tarihler", "basvuru_asamalari", "yer_mekan",
    "konaklama_yol_destegi", "odul_miktari_turu", "katilim_sartlari",
    "takim_buyuklugu_limiti", "basvuru_maliyeti", "istenen_materyal",
    "sponsor_kurumlar", "extraction_durumu", "extraction_tarihi", "efor_seviyesi", "kaynak",
    "etkinlik_turu", "format_turu", "ulke",
]


def load_firsatlar():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, link, duplicate_of_id, " + ", ".join(
                c for c in _FIRSATLAR_COLS if c != "link") + " FROM firsatlar ORDER BY id")
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        conn.close()
    id_to_link = {r["id"]: r["link"] for r in rows}
    out = []
    for r in rows:
        d = {c: _serialize(r.get(c)) for c in _FIRSATLAR_COLS}
        d["efor_kazanc_seviyesi"] = d.pop("efor_seviyesi")
        if r.get("duplicate_of_id"):
            d["duplicate_of"] = id_to_link.get(r["duplicate_of_id"])
        out.append(d)
    return out


def save_firsatlar(items):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            for f in items:
                vals = (
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
                    f.get("etkinlik_turu"), f.get("format_turu"), f.get("ulke"),
                )
                cur.execute(
                    """INSERT INTO firsatlar
                    (link, baslik, kaynak_sorgu, bulunma_tarihi, organizator, konu_kategori,
                     son_basvuru_tarihi, onemli_tarihler, basvuru_asamalari, yer_mekan,
                     konaklama_yol_destegi, odul_miktari_turu, katilim_sartlari,
                     takim_buyuklugu_limiti, basvuru_maliyeti, istenen_materyal,
                     sponsor_kurumlar, extraction_durumu, extraction_tarihi, efor_seviyesi, kaynak,
                     etkinlik_turu, format_turu, ulke)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (link) DO UPDATE SET
                      baslik=EXCLUDED.baslik, kaynak_sorgu=EXCLUDED.kaynak_sorgu,
                      bulunma_tarihi=EXCLUDED.bulunma_tarihi, organizator=EXCLUDED.organizator,
                      konu_kategori=EXCLUDED.konu_kategori, son_basvuru_tarihi=EXCLUDED.son_basvuru_tarihi,
                      onemli_tarihler=EXCLUDED.onemli_tarihler, basvuru_asamalari=EXCLUDED.basvuru_asamalari,
                      yer_mekan=EXCLUDED.yer_mekan, konaklama_yol_destegi=EXCLUDED.konaklama_yol_destegi,
                      odul_miktari_turu=EXCLUDED.odul_miktari_turu, katilim_sartlari=EXCLUDED.katilim_sartlari,
                      takim_buyuklugu_limiti=EXCLUDED.takim_buyuklugu_limiti,
                      basvuru_maliyeti=EXCLUDED.basvuru_maliyeti, istenen_materyal=EXCLUDED.istenen_materyal,
                      sponsor_kurumlar=EXCLUDED.sponsor_kurumlar, extraction_durumu=EXCLUDED.extraction_durumu,
                      extraction_tarihi=EXCLUDED.extraction_tarihi, efor_seviyesi=EXCLUDED.efor_seviyesi,
                      kaynak=EXCLUDED.kaynak,
                      etkinlik_turu=EXCLUDED.etkinlik_turu, format_turu=EXCLUDED.format_turu, ulke=EXCLUDED.ulke""",
                    vals,
                )
            cur.execute("SELECT id, link FROM firsatlar")
            link_to_id = {link: fid for fid, link in cur.fetchall()}
            for f in items:
                dup = f.get("duplicate_of")
                if dup and dup in link_to_id:
                    cur.execute(
                        "UPDATE firsatlar SET duplicate_of_id=%s WHERE link=%s",
                        (link_to_id[dup], f.get("link")),
                    )
        conn.commit()
    finally:
        conn.close()


def load_projeler():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, ad, aciklama, github_link, durum, olusturma_tarihi FROM projeler ORDER BY olusturma_tarihi")
            cols = [d[0] for d in cur.description]
            projeler = [dict(zip(cols, r)) for r in cur.fetchall()]
            cur.execute("SELECT proje_id, tarih, metin FROM proje_notlar ORDER BY id")
            notlar_by_proje = {}
            for pid, tarih, metin in cur.fetchall():
                notlar_by_proje.setdefault(pid, []).append({"tarih": _serialize(tarih), "metin": metin})
            cur.execute("SELECT proje_id, dosya_adi, yuklenme_tarihi, boyut FROM proje_dosyalar ORDER BY id")
            dosyalar_by_proje = {}
            for pid, ad, tarih, boyut in cur.fetchall():
                dosyalar_by_proje.setdefault(pid, []).append({"ad": ad, "tarih": _serialize(tarih), "boyut": boyut})
    finally:
        conn.close()
    out = []
    for p in projeler:
        out.append({
            "id": p["id"],
            "ad": p["ad"],
            "aciklama": p["aciklama"],
            "github_link": p["github_link"],
            "durum": p["durum"],
            "notlar": notlar_by_proje.get(p["id"], []),
            "dosyalar": dosyalar_by_proje.get(p["id"], []),
            "olusturma_tarihi": _serialize(p["olusturma_tarihi"]),
        })
    return out


def save_projeler(items):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            verilen_idler = [p.get("id") for p in items if p.get("id")]
            if verilen_idler:
                cur.execute("DELETE FROM projeler WHERE id != ALL(%s)", (verilen_idler,))
            else:
                cur.execute("DELETE FROM projeler")
            for p in items:
                pid = p.get("id")
                cur.execute(
                    """INSERT INTO projeler (id, ad, aciklama, github_link, durum, olusturma_tarihi)
                    VALUES (%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (id) DO UPDATE SET
                      ad=EXCLUDED.ad, aciklama=EXCLUDED.aciklama, github_link=EXCLUDED.github_link,
                      durum=EXCLUDED.durum""",
                    (pid, p.get("ad"), p.get("aciklama"), p.get("github_link"), p.get("durum"),
                     p.get("olusturma_tarihi") or None),
                )
                cur.execute("DELETE FROM proje_notlar WHERE proje_id=%s", (pid,))
                for n in p.get("notlar", []):
                    cur.execute(
                        "INSERT INTO proje_notlar (proje_id, tarih, metin) VALUES (%s,%s,%s)",
                        (pid, n.get("tarih") or None, n.get("metin")),
                    )
                cur.execute("DELETE FROM proje_dosyalar WHERE proje_id=%s", (pid,))
                for d in p.get("dosyalar", []):
                    cur.execute(
                        "INSERT INTO proje_dosyalar (proje_id, dosya_adi, yuklenme_tarihi, boyut) VALUES (%s,%s,%s,%s)",
                        (pid, d.get("ad"), d.get("tarih") or None, d.get("boyut")),
                    )
        conn.commit()
    finally:
        conn.close()



def delete_proje(proje_id):
    """Bir projeyi siler. Iliskili kayitlari koruyup sadece proje baglantisini
    kaldirir (unlink): tasklar.proje_id, basvurular.proje_id, sudola_onerileri.onerilen_proje_id
    NULL yapilir - gorevler ve basvurular SILINMEZ, sadece projeyle iliskisi kesilir.
    proje_notlar ve proje_dosyalar tablolari ON DELETE CASCADE ile otomatik silinir.
    Fiziksel dosyalar (proje_dosyalari/{proje_id}/ dizini) burada silinmez - cagiran
    (api.py) tarafta ayrica silinmelidir.
    Return: True eger proje bulunup silindiyse, False eger boyle bir proje yoksa.
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE tasklar SET proje_id = NULL WHERE proje_id = %s", (proje_id,))
            cur.execute("UPDATE basvurular SET proje_id = NULL WHERE proje_id = %s", (proje_id,))
            cur.execute(
                "UPDATE sudola_onerileri SET onerilen_proje_id = NULL WHERE onerilen_proje_id = %s",
                (proje_id,),
            )
            cur.execute("DELETE FROM projeler WHERE id = %s", (proje_id,))
            silindi = cur.rowcount > 0
        conn.commit()
        return silindi
    finally:
        conn.close()

def load_ekip():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT isim FROM ekip ORDER BY id")
            return [r[0] for r in cur.fetchall()]
    finally:
        conn.close()


def save_ekip(isimler):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT isim FROM ekip")
            mevcut = {r[0] for r in cur.fetchall()}
            for isim in isimler:
                if isim not in mevcut:
                    cur.execute("INSERT INTO ekip (isim) VALUES (%s) ON CONFLICT (isim) DO NOTHING", (isim,))
        conn.commit()
    finally:
        conn.close()


def load_tasklar():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT t.id, t.baslik, e.isim, t.tur, t.deadline, t.durum, t.olusturma_tarihi,
                       t.firsat_id, t.proje_id, f.baslik, p.ad, f.link
                FROM tasklar t
                LEFT JOIN ekip e ON t.atanan_id = e.id
                LEFT JOIN firsatlar f ON t.firsat_id = f.id
                LEFT JOIN projeler p ON t.proje_id = p.id
                ORDER BY t.id
            """)
            rows = cur.fetchall()
            cur.execute("""
                SELECT ta.task_id, e2.isim
                FROM task_atananlar ta
                JOIN ekip e2 ON ta.ekip_id = e2.id
                ORDER BY ta.task_id, e2.isim
            """)
            coklu_atanan = {}
            for tid2, isim2 in cur.fetchall():
                coklu_atanan.setdefault(tid2, []).append(isim2)
    finally:
        conn.close()
    out = []
    for tid, baslik, isim, tur, deadline, durum, olusturma, firsat_id, proje_id, firsat_baslik, proje_adi, firsat_link in rows:
        isimler = coklu_atanan.get(tid) or ([isim] if isim else [])
        out.append({
            "id": tid, "baslik": baslik, "atanan": (", ".join(isimler) if isimler else "belirsiz"), "tur": tur,
            "deadline": deadline, "durum": durum, "olusturma_tarihi": _serialize(olusturma),
            "firsat_id": firsat_id, "proje_id": proje_id,
            "firsat_baslik": firsat_baslik, "proje_adi": proje_adi,
            "firsat_link": firsat_link,
        })
    return out


def save_tasklar(items):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT isim, id FROM ekip")
            isim_to_id = dict(cur.fetchall())
            verilen_idler = [t.get("id") for t in items if t.get("id") is not None]
            if verilen_idler:
                cur.execute("DELETE FROM tasklar WHERE id != ALL(%s)", (verilen_idler,))
            else:
                cur.execute("DELETE FROM tasklar")
            for t in items:
                atanan_raw = t.get("atanan") or ""
                isimler = [x.strip() for x in atanan_raw.split(",") if x.strip()]
                for isim_tek in isimler:
                    if isim_tek not in isim_to_id:
                        cur.execute("INSERT INTO ekip (isim) VALUES (%s) RETURNING id", (isim_tek,))
                        isim_to_id[isim_tek] = cur.fetchone()[0]
                atanan_ids = [isim_to_id[x] for x in isimler]
                atanan_id = atanan_ids[0] if atanan_ids else None
                cur.execute(
                    """INSERT INTO tasklar (id, baslik, atanan_id, tur, deadline, durum, olusturma_tarihi, firsat_id, proje_id)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT (id) DO UPDATE SET
                         baslik=EXCLUDED.baslik, atanan_id=EXCLUDED.atanan_id, tur=EXCLUDED.tur,
                         deadline=EXCLUDED.deadline, durum=EXCLUDED.durum,
                         firsat_id=EXCLUDED.firsat_id, proje_id=EXCLUDED.proje_id""",
                    (t.get("id"), t.get("baslik"), atanan_id, t.get("tur"), t.get("deadline") or None,
                     t.get("durum"), t.get("olusturma_tarihi") or None,
                     t.get("firsat_id"), t.get("proje_id")),
                )
                gorev_id = t.get("id")
                cur.execute("DELETE FROM task_atananlar WHERE task_id = %s", (gorev_id,))
                for eid in atanan_ids:
                    cur.execute(
                        "INSERT INTO task_atananlar (task_id, ekip_id) VALUES (%s,%s) ON CONFLICT DO NOTHING",
                        (gorev_id, eid),
                    )
            cur.execute("SELECT setval(pg_get_serial_sequence('tasklar','id'), COALESCE((SELECT MAX(id) FROM tasklar), 1))")
        conn.commit()
    finally:
        conn.close()


def load_basvurular():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT f.link, f.baslik, b.durum, b.proje_id
                FROM basvurular b JOIN firsatlar f ON b.firsat_id = f.id
            """)
            rows = cur.fetchall()
    finally:
        conn.close()
    out = {}
    for link, baslik, durum, proje_id in rows:
        out[link] = {"baslik": baslik, "link": link, "durum": durum, "proje_id": proje_id}
    return out


def save_basvurular(veri):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, link FROM firsatlar")
            link_to_fid = dict((link, fid) for fid, link in cur.fetchall())
            verilen_linkler = list(veri.keys())
            if verilen_linkler:
                fid_list = [link_to_fid[l] for l in verilen_linkler if l in link_to_fid]
                if fid_list:
                    cur.execute("DELETE FROM basvurular WHERE firsat_id != ALL(%s)", (fid_list,))
                else:
                    cur.execute("DELETE FROM basvurular")
            else:
                cur.execute("DELETE FROM basvurular")
            for link, b in veri.items():
                fid = link_to_fid.get(link)
                if fid is None:
                    continue
                cur.execute("SELECT id FROM basvurular WHERE firsat_id=%s", (fid,))
                mevcut = cur.fetchone()
                if mevcut:
                    cur.execute(
                        "UPDATE basvurular SET durum=%s, proje_id=%s WHERE firsat_id=%s",
                        (b.get("durum"), b.get("proje_id"), fid),
                    )
                else:
                    cur.execute(
                        "INSERT INTO basvurular (firsat_id, proje_id, durum, basvuru_tarihi) VALUES (%s,%s,%s,%s)",
                        (fid, b.get("proje_id"), b.get("durum"), None),
                    )
        conn.commit()
    finally:
        conn.close()


# ============================================================
# FAZ C1: sudola proje onerisi persist fonksiyonlari
# ============================================================

def get_firsat_id_by_link(link):
    rows = fetch_all("SELECT id FROM firsatlar WHERE link = %s", (link,))
    return rows[0]["id"] if rows else None


def save_sudola_onerisi(firsat_id, onerilen_proje_id, skor, aciklama, guclu_yonler, riskler):
    execute(
        """
        INSERT INTO sudola_onerileri
            (firsat_id, onerilen_proje_id, skor, aciklama, guclu_yonler, riskler, olusturma_tarihi)
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """,
        (
            firsat_id,
            onerilen_proje_id,
            skor,
            aciklama,
            json.dumps(guclu_yonler or [], ensure_ascii=False),
            json.dumps(riskler or [], ensure_ascii=False),
        ),
    )


def get_son_sudola_onerisi(firsat_id):
    rows = fetch_all(
        """
        SELECT onerilen_proje_id, skor, aciklama, guclu_yonler, riskler, olusturma_tarihi
        FROM sudola_onerileri
        WHERE firsat_id = %s
        ORDER BY olusturma_tarihi DESC, id DESC
        LIMIT 1
        """,
        (firsat_id,),
    )
    return rows[0] if rows else None
