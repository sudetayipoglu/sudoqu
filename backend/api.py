from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import json
import os
import shutil
import re
import time
import uuid
import requests
from datetime import datetime

app = FastAPI(title="SudoQu API")

from db import init_schema as _init_schema

@app.on_event("startup")
def _on_startup():
    _init_schema()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FIRSATLAR_DOSYA = "firsatlar.json"
BASVURULAR_DOSYA = "basvurular.json"
TASKLAR_DOSYA = "tasklar.json"
EKIP_DOSYA = "ekip.json"
PROJELER_DOSYA = "projeler.json"
PROJE_DOSYALARI_DIR = "proje_dosyalari"
IZIN_VERILEN_UZANTILAR = {".pdf", ".docx", ".png", ".jpg", ".jpeg", ".zip"}
MAKS_DOSYA_BOYUTU = 10 * 1024 * 1024  # 10 MB
MAKS_METIN_UZUNLUGU = 5000
_github_cache = {}
_GITHUB_CACHE_TTL = 600  # 10 dakika - 60 istek/saat limitine karsi

import db as _db

_PG_OKU = {
    "firsatlar.json": _db.load_firsatlar,
    "basvurular.json": _db.load_basvurular,
    "tasklar.json": _db.load_tasklar,
    "ekip.json": _db.load_ekip,
    "projeler.json": _db.load_projeler,
}
_PG_YAZ = {
    "firsatlar.json": _db.save_firsatlar,
    "basvurular.json": _db.save_basvurular,
    "tasklar.json": _db.save_tasklar,
    "ekip.json": _db.save_ekip,
    "projeler.json": _db.save_projeler,
}


def dosya_oku(yol, varsayilan):
    if _db.DATABASE_URL:
        fn = _PG_OKU.get(os.path.basename(yol))
        if fn:
            return fn()
    if os.path.exists(yol):
        with open(yol, encoding="utf-8") as f:
            return json.load(f)
    return varsayilan

def dosya_yaz(yol, veri):
    if _db.DATABASE_URL:
        fn = _PG_YAZ.get(os.path.basename(yol))
        if fn:
            fn(veri)
            return
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)

@app.get("/")
def anasayfa():
    return {"durum": "SudoQu API calisiyor"}

TAVILY_DURUM_DOSYA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tavily_anahtar_durumu.json")

@app.get("/tavily-anahtar-durumu")
def tavily_anahtar_durumu_getir():
    varsayilan = {"aktif_key_index": 0, "ardisik_tam_tur_basarisiz": 0, "alarm_aktif": False, "alarm_mesaji": None, "alarm_tarihi": None}
    if not os.path.exists(TAVILY_DURUM_DOSYA):
        return varsayilan
    try:
        with open(TAVILY_DURUM_DOSYA, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return varsayilan


@app.get("/firsatlar")
def firsatlari_getir():
    tumu = dosya_oku(FIRSATLAR_DOSYA, [])
    return [f for f in tumu if f.get("extraction_durumu") != "atlandi_genel_sayfa"]

@app.get("/genel-sayfalar")
def genel_sayfalari_getir():
    tumu = dosya_oku(FIRSATLAR_DOSYA, [])
    return [f for f in tumu if f.get("extraction_durumu") == "atlandi_genel_sayfa"]

@app.post("/firsatlar/manuel")
def firsat_manuel_ekle(
    baslik: str,
    organizator: str = None,
    konu_kategori: str = None,
    son_basvuru_tarihi: str = None,
    yer_mekan: str = None,
    odul_miktari_turu: str = None,
    katilim_sartlari: str = None,
    link: str = None,
):
    baslik = (baslik or "").strip()
    if not baslik:
        raise HTTPException(status_code=400, detail="Baslik bos olamaz")
    firsatlar = dosya_oku(FIRSATLAR_DOSYA, [])
    link = (link or "").strip() or f"manuel://{uuid.uuid4().hex}"
    if any(f.get("link") == link for f in firsatlar):
        raise HTTPException(status_code=400, detail="Bu link zaten kayitli")
    simdi = datetime.now().strftime("%Y-%m-%d %H:%M")
    yeni = {
        "link": link,
        "baslik": baslik[:300],
        "kaynak_sorgu": None,
        "bulunma_tarihi": simdi,
        "organizator": organizator,
        "konu_kategori": konu_kategori,
        "son_basvuru_tarihi": son_basvuru_tarihi,
        "onemli_tarihler": None,
        "basvuru_asamalari": None,
        "yer_mekan": yer_mekan,
        "konaklama_yol_destegi": None,
        "odul_miktari_turu": odul_miktari_turu,
        "katilim_sartlari": katilim_sartlari,
        "takim_buyuklugu_limiti": None,
        "basvuru_maliyeti": None,
        "istenen_materyal": None,
        "sponsor_kurumlar": None,
        "extraction_durumu": "manuel",
        "extraction_tarihi": simdi,
        "efor_kazanc_seviyesi": None,
        "kaynak": "manuel",
    }
    firsatlar.append(yeni)
    dosya_yaz(FIRSATLAR_DOSYA, firsatlar)
    return {"basari": True, "eklenen": yeni}


@app.get("/basvurular")
def basvurulari_getir():
    return list(dosya_oku(BASVURULAR_DOSYA, {}).values())

@app.post("/basvurular/{link:path}")
def basvuru_ekle(link: str, proje_id: str = None):
    firsatlar = dosya_oku(FIRSATLAR_DOSYA, [])
    basvurular = dosya_oku(BASVURULAR_DOSYA, {})
    secilen = next((f for f in firsatlar if f["link"] == link), None)
    if not secilen:
        return {"hata": "Fırsat bulunamadı"}
    if proje_id:
        projeler = dosya_oku(PROJELER_DOSYA, [])
        if not any(p.get("id") == proje_id for p in projeler):
            proje_id = None
    basvurular[link] = {
        "baslik": secilen["baslik"],
        "link": link,
        "durum": "beklemede",
        "proje_id": proje_id,
    }
    dosya_yaz(BASVURULAR_DOSYA, basvurular)
    return {"basari": True, "eklenen": basvurular[link]}

@app.put("/basvurular/{link:path}")
def basvuru_durum_guncelle(link: str, durum: str):
    gecerli_durumlar = {"beklemede", "kazandi", "kaybetti"}
    if durum not in gecerli_durumlar:
        raise HTTPException(status_code=400, detail=f"Gecersiz durum, izin verilenler: {sorted(gecerli_durumlar)}")
    basvurular = dosya_oku(BASVURULAR_DOSYA, {})
    if link not in basvurular:
        raise HTTPException(status_code=404, detail="Basvuru bulunamadi")
    basvurular[link]["durum"] = durum
    dosya_yaz(BASVURULAR_DOSYA, basvurular)
    return basvurular[link]


@app.get("/ekip")
def ekibi_getir():
    return dosya_oku(EKIP_DOSYA, [])

@app.post("/ekip/{isim}")
def ekibe_ekle(isim: str):
    ekip = dosya_oku(EKIP_DOSYA, [])
    if isim not in ekip:
        ekip.append(isim)
        dosya_yaz(EKIP_DOSYA, ekip)
    return ekip

@app.get("/tasklar")
def taskları_getir():
    return dosya_oku(TASKLAR_DOSYA, [])

@app.post("/tasklar")
def task_ekle(baslik: str, atanan: str, tur: str = "task", deadline: str = None, proje_id: str = None, firsat_id: str = None):
    tasklar = dosya_oku(TASKLAR_DOSYA, [])
    if proje_id:
        projeler = dosya_oku(PROJELER_DOSYA, [])
        if not any(p.get("id") == proje_id for p in projeler):
            proje_id = None
    resolved_firsat_id = None
    if firsat_id and _db.DATABASE_URL:
        resolved_firsat_id = _db.get_firsat_id_by_link(firsat_id)
    yeni = {
        "id": len(tasklar) + 1,
        "baslik": baslik,
        "atanan": atanan,
        "tur": tur,
        "deadline": deadline,
        "durum": "bekliyor",
        "olusturma_tarihi": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "proje_id": proje_id,
        "firsat_id": resolved_firsat_id,
    }
    tasklar.append(yeni)
    dosya_yaz(TASKLAR_DOSYA, tasklar)
    return yeni

@app.put("/tasklar/{task_id}/tamamla")
def task_tamamla(task_id: int):
    tasklar = dosya_oku(TASKLAR_DOSYA, [])
    for t in tasklar:
        if t["id"] == task_id:
            t["durum"] = "tamamlandı"
            dosya_yaz(TASKLAR_DOSYA, tasklar)
            return t
    return {"hata": "Task bulunamadı"}


@app.put("/tasklar/{task_id}")
def task_guncelle(task_id: int, baslik: str = None, atanan: str = None, tur: str = None, deadline: str = None, proje_id: str = None, firsat_id: str = None):
    tasklar = dosya_oku(TASKLAR_DOSYA, [])
    for t in tasklar:
        if t["id"] == task_id:
            if baslik is not None:
                baslik = baslik.strip()
                if not baslik:
                    raise HTTPException(status_code=400, detail="Baslik bos olamaz")
                t["baslik"] = baslik[:200]
            if atanan is not None:
                t["atanan"] = atanan.strip() or "belirsiz"
            if tur is not None:
                t["tur"] = tur
            if deadline is not None:
                t["deadline"] = deadline or None
            if proje_id is not None:
                if proje_id == "":
                    t["proje_id"] = None
                else:
                    projeler = dosya_oku(PROJELER_DOSYA, [])
                    t["proje_id"] = proje_id if any(p.get("id") == proje_id for p in projeler) else None
            if firsat_id is not None:
                if firsat_id == "":
                    t["firsat_id"] = None
                else:
                    t["firsat_id"] = _db.get_firsat_id_by_link(firsat_id) if _db.DATABASE_URL else None
            dosya_yaz(TASKLAR_DOSYA, tasklar)
            return t
    raise HTTPException(status_code=404, detail="Task bulunamadi")


@app.delete("/tasklar/{task_id}")
def task_sil(task_id: int):
    tasklar = dosya_oku(TASKLAR_DOSYA, [])
    yeni_liste = [t for t in tasklar if t["id"] != task_id]
    if len(yeni_liste) == len(tasklar):
        raise HTTPException(status_code=404, detail="Task bulunamadi")
    dosya_yaz(TASKLAR_DOSYA, yeni_liste)
    return {"basari": True, "silinen_id": task_id}


def _github_repo_bilgisi(github_link: str):
    """GitHub public REST API'den repo bilgisi ceker (aciklama, son commit, yildiz sayisi).
    Kimliksiz istekler icin 60 istek/saat limiti var; asilmamasi icin 10 dakikalik
    bellek-ici cache kullanilir (repo basina)."""
    if not github_link:
        return None
    simdi = time.time()
    if github_link in _github_cache:
        veri, zaman = _github_cache[github_link]
        if simdi - zaman < _GITHUB_CACHE_TTL:
            return veri

    m = re.search(r"github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", github_link.strip())
    if not m:
        return {"hata": "Gecerli bir GitHub linki degil"}
    owner, repo = m.group(1), m.group(2)

    try:
        repo_resp = requests.get(f"https://api.github.com/repos/{owner}/{repo}", timeout=8)
        if repo_resp.status_code != 200:
            veri = {"hata": f"GitHub API hatasi: {repo_resp.status_code}"}
            _github_cache[github_link] = (veri, simdi)
            return veri
        repo_json = repo_resp.json()

        commit_resp = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/commits",
            params={"per_page": 1}, timeout=8,
        )
        son_commit = None
        if commit_resp.status_code == 200 and commit_resp.json():
            c = commit_resp.json()[0]
            son_commit = {
                "mesaj": (c.get("commit", {}).get("message") or "")[:200],
                "tarih": c.get("commit", {}).get("author", {}).get("date"),
                "yazar": c.get("commit", {}).get("author", {}).get("name"),
            }

        veri = {
            "aciklama": repo_json.get("description"),
            "yildiz_sayisi": repo_json.get("stargazers_count"),
            "son_commit": son_commit,
            "dil": repo_json.get("language"),
        }
    except Exception as e:
        veri = {"hata": f"GitHub bilgisi alinamadi: {type(e).__name__}"}

    _github_cache[github_link] = (veri, simdi)
    return veri


@app.get("/projeler")
def projeleri_getir():
    projeler = dosya_oku(PROJELER_DOSYA, [])
    for p in projeler:
        if p.get("github_link"):
            p["github_bilgi"] = _github_repo_bilgisi(p["github_link"])
    return projeler


@app.post("/projeler")
def proje_ekle(ad: str, aciklama: str = "", github_link: str = None, durum: str = "aktif"):
    ad = (ad or "").strip()
    if not ad:
        raise HTTPException(status_code=400, detail="Proje adi bos olamaz")
    ad = ad[:200]
    aciklama = (aciklama or "")[:MAKS_METIN_UZUNLUGU]

    projeler = dosya_oku(PROJELER_DOSYA, [])
    yeni = {
        "id": uuid.uuid4().hex[:12],
        "ad": ad,
        "aciklama": aciklama,
        "github_link": (github_link or "").strip() or None,
        "durum": durum or "aktif",
        "notlar": [],
        "dosyalar": [],
        "olusturma_tarihi": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    projeler.append(yeni)
    dosya_yaz(PROJELER_DOSYA, projeler)
    return yeni


@app.put("/projeler/{proje_id}")
def proje_guncelle(proje_id: str, ad: str = None, aciklama: str = None, github_link: str = None, durum: str = None):
    projeler = dosya_oku(PROJELER_DOSYA, [])
    for p in projeler:
        if p["id"] == proje_id:
            if ad is not None:
                ad = ad.strip()
                if not ad:
                    raise HTTPException(status_code=400, detail="Proje adi bos olamaz")
                p["ad"] = ad[:200]
            if aciklama is not None:
                p["aciklama"] = aciklama[:MAKS_METIN_UZUNLUGU]
            if github_link is not None:
                p["github_link"] = github_link.strip() or None
            if durum is not None:
                p["durum"] = durum
            dosya_yaz(PROJELER_DOSYA, projeler)
            return p
    raise HTTPException(status_code=404, detail="Proje bulunamadi")


@app.post("/projeler/{proje_id}/not")
def proje_not_ekle(proje_id: str, metin: str):
    metin = (metin or "").strip()
    if not metin:
        raise HTTPException(status_code=400, detail="Not metni bos olamaz")
    metin = metin[:MAKS_METIN_UZUNLUGU]

    projeler = dosya_oku(PROJELER_DOSYA, [])
    for p in projeler:
        if p["id"] == proje_id:
            p.setdefault("notlar", []).append({
                "tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "metin": metin,
            })
            dosya_yaz(PROJELER_DOSYA, projeler)
            return p
    raise HTTPException(status_code=404, detail="Proje bulunamadi")


@app.post("/projeler/{proje_id}/dosya")
async def proje_dosya_yukle(proje_id: str, file: UploadFile = File(...)):
    projeler = dosya_oku(PROJELER_DOSYA, [])
    proje = next((p for p in projeler if p["id"] == proje_id), None)
    if not proje:
        raise HTTPException(status_code=404, detail="Proje bulunamadi")

    ad = file.filename or "dosya"
    uzanti = os.path.splitext(ad)[1].lower()
    if uzanti not in IZIN_VERILEN_UZANTILAR:
        raise HTTPException(
            status_code=400,
            detail=f"Desteklenmeyen dosya turu: {uzanti}. Izin verilenler: {', '.join(sorted(IZIN_VERILEN_UZANTILAR))}",
        )

    icerik = await file.read()
    if len(icerik) > MAKS_DOSYA_BOYUTU:
        raise HTTPException(status_code=400, detail="Dosya boyutu 10MB sinirini asiyor")

    hedef_dizin = os.path.join(PROJE_DOSYALARI_DIR, proje_id)
    os.makedirs(hedef_dizin, exist_ok=True)

    guvenli_ad = re.sub(r"[^\w.\-]", "_", ad)
    hedef_yol = os.path.join(hedef_dizin, guvenli_ad)
    with open(hedef_yol, "wb") as f:
        f.write(icerik)

    proje.setdefault("dosyalar", []).append({
        "ad": guvenli_ad,
        "tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "boyut": len(icerik),
    })
    dosya_yaz(PROJELER_DOSYA, projeler)
    return proje


@app.get("/projeler/{proje_id}/dosya/{dosya_adi}")
def proje_dosya_indir(proje_id: str, dosya_adi: str):
    guvenli_ad = re.sub(r"[^\w.\-]", "_", dosya_adi)
    yol = os.path.join(PROJE_DOSYALARI_DIR, proje_id, guvenli_ad)
    if not os.path.exists(yol):
        raise HTTPException(status_code=404, detail="Dosya bulunamadi")
    return FileResponse(yol, filename=guvenli_ad)


@app.delete("/projeler/{proje_id}")
def proje_sil(proje_id: str):
    """Bir projeyi siler. Iliskili gorevler (tasklar) ve basvurular SILINMEZ -
    sadece bu projeye olan baglantilari kaldirilir (proje_id = None). Boylece bir
    basvuruya bagli projeyi sildiginizde basvurunun kendisi kaybolmaz, sadece
    'hangi projeyle iliskili' bilgisi temizlenir. Proje notlari ve yuklenen
    dosyalarin veritabani kayitlari (DB modunda ON DELETE CASCADE ile) otomatik
    silinir; fiziksel dosyalar asagida ayrica temizlenir."""
    if _db.DATABASE_URL:
        silindi = _db.delete_proje(proje_id)
    else:
        projeler = dosya_oku(PROJELER_DOSYA, [])
        yeni_liste = [p for p in projeler if p.get("id") != proje_id]
        silindi = len(yeni_liste) != len(projeler)
        if silindi:
            dosya_yaz(PROJELER_DOSYA, yeni_liste)
            tasklar = dosya_oku(TASKLAR_DOSYA, [])
            degisti = False
            for t in tasklar:
                if t.get("proje_id") == proje_id:
                    t["proje_id"] = None
                    degisti = True
            if degisti:
                dosya_yaz(TASKLAR_DOSYA, tasklar)
            basvurular = dosya_oku(BASVURULAR_DOSYA, {})
            degisti = False
            for _link, b in basvurular.items():
                if b.get("proje_id") == proje_id:
                    b["proje_id"] = None
                    degisti = True
            if degisti:
                dosya_yaz(BASVURULAR_DOSYA, basvurular)

    if not silindi:
        raise HTTPException(status_code=404, detail="Proje bulunamadı")

    dizin = os.path.join(PROJE_DOSYALARI_DIR, proje_id)
    if os.path.isdir(dizin):
        shutil.rmtree(dizin, ignore_errors=True)

    return {"basari": True, "silinen_id": proje_id}


# --- V1.5: sudola chatbot (Tavily arastirma + Gemini soru-cevap / oneri) ---
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
load_dotenv()
from secret_helper import get_secret_or_env
from tavily import TavilyClient
from google import genai
from google.genai import types

SUDOLA_TAVILY_API_KEY = get_secret_or_env("tavily-api-key", "TAVILY_API_KEY")
SUDOLA_GEMINI_API_KEY = get_secret_or_env("gemini-api-key", "GEMINI_API_KEY")
sudola_tavily_client = TavilyClient(api_key=SUDOLA_TAVILY_API_KEY) if SUDOLA_TAVILY_API_KEY else None
sudola_gemini_client = genai.Client(api_key=SUDOLA_GEMINI_API_KEY) if SUDOLA_GEMINI_API_KEY else None
SUDOLA_GEMINI_MODEL = "gemini-flash-lite-latest"

_sudola_arastirma_cache = {}
_SUDOLA_ARASTIRMA_TTL = 3600


class SudolaOneriSonuc(BaseModel):
    skor: int
    aciklama: str
    guclu_yonler: list[str]
    riskler: list[str]
    onerilen_proje_id: Optional[str] = None
    onerilen_proje_adi: Optional[str] = None


def _firsat_bul(link: str):
    firsatlar = dosya_oku(FIRSATLAR_DOSYA, [])
    return next((f for f in firsatlar if f.get("link") == link), None)


_SUDOLA_ALAN_ETIKETLERI = {
    "organizator": "Organizator",
    "konu_kategori": "Konu/Kategori",
    "son_basvuru_tarihi": "Son Basvuru Tarihi",
    "onemli_tarihler": "Onemli Tarihler",
    "basvuru_asamalari": "Basvuru Asamalari",
    "yer_mekan": "Yer/Mekan",
    "konaklama_yol_destegi": "Konaklama/Yol Destegi",
    "odul_miktari_turu": "Odul Miktari/Turu",
    "katilim_sartlari": "Katilim Sartlari",
    "takim_buyuklugu_limiti": "Takim Buyuklugu Limiti",
    "basvuru_maliyeti": "Basvuru Maliyeti",
    "istenen_materyal": "Istenen Materyal",
    "sponsor_kurumlar": "Sponsor Kurumlar",
}


def _firsat_baglam_metni(firsat: dict) -> str:
    satirlar = [f"Baslik: {firsat.get('baslik', '')}", f"Link: {firsat.get('link', '')}"]
    for alan, etiket in _SUDOLA_ALAN_ETIKETLERI.items():
        deger = firsat.get(alan)
        satirlar.append(f"{etiket}: {deger if deger not in (None, '') else 'Bilgi yok'}")
    return "\n".join(satirlar)


def _sudola_arastirma_yap(firsat: dict) -> str:
    link = firsat.get("link", "")
    now = time.time()
    if link in _sudola_arastirma_cache:
        deger, ts = _sudola_arastirma_cache[link]
        if now - ts < _SUDOLA_ARASTIRMA_TTL:
            return deger

    if sudola_tavily_client is None:
        sonuc = "(Tavily API anahtari yapilandirilmamis - arastirma yapilamadi)"
        _sudola_arastirma_cache[link] = (sonuc, now)
        return sonuc

    organizator = firsat.get("organizator") or ""
    baslik = firsat.get("baslik") or ""
    sorgu = f"{organizator} {baslik} gecmis yillar kazananlari kazanma nedenleri".strip()

    try:
        arama = sudola_tavily_client.search(query=sorgu, max_results=5, search_depth="basic")
        parcalar = []
        for r in arama.get("results", []):
            baslik_r = r.get("title", "")
            icerik_r = (r.get("content", "") or "")[:500]
            parcalar.append(f"- {baslik_r}: {icerik_r}")
        sonuc = "\n".join(parcalar) if parcalar else "(Bu firsatla ilgili arama sonucu bulunamadi)"
    except Exception as e:
        sonuc = f"(Tavily arama hatasi: {type(e).__name__})"

    _sudola_arastirma_cache[link] = (sonuc, now)
    return sonuc


@app.post("/sudola/soru")
def sudola_soru(link: str, soru: str):
    soru = (soru or "").strip()
    if not soru:
        raise HTTPException(status_code=400, detail="Soru bos olamaz")
    if len(soru) > 1000:
        raise HTTPException(status_code=400, detail="Soru 1000 karakteri asamaz")

    firsat = _firsat_bul(link)
    if not firsat:
        raise HTTPException(status_code=404, detail="Firsat bulunamadi")

    if sudola_gemini_client is None:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY yapilandirilmamis")

    baglam = _firsat_baglam_metni(firsat)
    arastirma = _sudola_arastirma_yap(firsat)

    _TR_AY_ADLARI = ['', 'Ocak', 'Subat', 'Mart', 'Nisan', 'Mayis', 'Haziran',
                     'Temmuz', 'Agustos', 'Eylul', 'Ekim', 'Kasim', 'Aralik']
    _simdi = datetime.now()
    bugun_str = f"{_simdi.day} {_TR_AY_ADLARI[_simdi.month]} {_simdi.year} (YYYY-MM-DD: {_simdi.strftime('%Y-%m-%d')})"

    prompt = (
        'Sen "Sudo" adinda bir firsat asistanisin. Asagida bir yarisma/etkinlik '
        'firsatiyla ilgili elimizdeki bilgiler ve internet arastirmasindan gecmis kazananlar hakkinda bulunan bilgiler var. '
        'Sadece bu bilgilere dayanarak kullanicinin sorusunu Turkce, net ve kisa cevapla. Eger cevap '
        'bu bilgilerde yoksa, uydurma - "Bu konuda elimde bilgi yok" gibi durustce belirt. '
        'Tarihle ilgili sorularda (kac gun kaldi, suresi gecti mi, ne zaman gibi) SADECE asagida verilen '
        'BUGUNUN TARIHI bilgisini gercek referans olarak kullan - kendi bilgine veya varsayimina ASLA guvenme.\n\n'
        '--- BUGUNUN TARIHI ---\n' + bugun_str + '\n\n'
        '--- FIRSAT BILGILERI ---\n' + baglam + '\n\n'
        '--- GECMIS KAZANANLAR ARASTIRMASI (internetten) ---\n' + arastirma + '\n\n'
        '--- KULLANICI SORUSU ---\n' + soru + '\n\nCevap:'
    )

    try:
        response = sudola_gemini_client.models.generate_content(model=SUDOLA_GEMINI_MODEL, contents=prompt)
        cevap = (response.text or "").strip()
    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            raise HTTPException(status_code=429, detail="Gemini gunluk kota sinirina ulasildi, lutfen daha sonra tekrar deneyin")
        raise HTTPException(status_code=502, detail=f"Gemini hatasi: {type(e).__name__}")

    return {"cevap": cevap, "arastirma_kullanildi": sudola_tavily_client is not None}


def _projeler_baglam_metni(projeler: list) -> str:
    if not projeler:
        return "(ekibin henuz kayitli bir projesi yok)"
    satirlar = []
    for p in projeler:
        satirlar.append(
            "- id: " + str(p.get("id")) + " | ad: " + str(p.get("ad", "")) +
            " | durum: " + str(p.get("durum", "")) + " | aciklama: " + str(p.get("aciklama", ""))
        )
    return "\n".join(satirlar)


@app.get("/sudola/oneri/{link:path}")
def sudola_oneri(link: str):
    firsat = _firsat_bul(link)
    if not firsat:
        raise HTTPException(status_code=404, detail="Firsat bulunamadi")

    if sudola_gemini_client is None:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY yapilandirilmamis")

    baglam = _firsat_baglam_metni(firsat)
    arastirma = _sudola_arastirma_yap(firsat)
    projeler = dosya_oku(PROJELER_DOSYA, [])
    proje_baglam = _projeler_baglam_metni(projeler)

    prompt = (
        'Sen "Sudo" adinda bir firsat degerlendirme asistanisin. Asagidaki bilgilere dayanarak '
        'bir ogrenci/takimin bu firsata basvurup basvurmamasi konusunda 0-100 arasi bir uygunluk skoru '
        've kisa bir aciklama uret. Skor, firsatin somut nitelikleriyle (odul, gereksinimler, gecmis '
        'kazananlarin basvuru profili gibi) ilgili olmalidir. ORGANIZATORUN siyasi veya sosyal '
        'egilimini ASLA degerlendirmeye katma - sadece firsatin objektif nitelikleri ve gecmis kazanma '
        'orunekleri onemli.\n\n'
        'Ayrica asagida ekibin mevcut projelerinin bir listesi var. Eger bu firsat, listedeki '
        'projelerden biriyle ACIK ve OBJEKTIF bir sekilde iliskiliyse (ayni konu, teknoloji, hedef '
        'kitle ya da amac ortakligi), o projenin id degerini onerilen_proje_id alaninda, adini '
        'onerilen_proje_adi alaninda don. Eger listede net bicimde uyan bir proje YOKSA, '
        'onerilen_proje_id ve onerilen_proje_adi alanlarini null birak - ASLA zorlama veya belirsiz '
        'bir eslesme uydurma.\n\n'
        '--- FIRSAT BILGILERI ---\n' + baglam + '\n\n'
        '--- EKIP PROJELERI ---\n' + proje_baglam + '\n\n'
        '--- GECMIS KAZANANLAR ARASTIRMASI (internetten) ---\n' + arastirma
    )

    try:
        response = sudola_gemini_client.models.generate_content(
            model=SUDOLA_GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=SudolaOneriSonuc,
            ),
        )
        if not response.parsed:
            raise ValueError("bos parsed")
        sonuc = response.parsed.model_dump()

        gecerli_id_ler = {p.get("id") for p in projeler}
        if sonuc.get("onerilen_proje_id") not in gecerli_id_ler:
            sonuc["onerilen_proje_id"] = None
            sonuc["onerilen_proje_adi"] = None

        if _db.DATABASE_URL:
            firsat_id = _db.get_firsat_id_by_link(link)
            if firsat_id:
                _db.save_sudola_onerisi(
                    firsat_id=firsat_id,
                    onerilen_proje_id=sonuc.get("onerilen_proje_id"),
                    skor=sonuc.get("skor"),
                    aciklama=sonuc.get("aciklama"),
                    guclu_yonler=sonuc.get("guclu_yonler", []),
                    riskler=sonuc.get("riskler", []),
                )

        return sonuc
    except HTTPException:
        raise
    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            raise HTTPException(status_code=429, detail="Gemini gunluk kota sinirina ulasildi, lutfen daha sonra tekrar deneyin")
        raise HTTPException(status_code=502, detail=f"Gemini hatasi: {type(e).__name__}")


@app.get("/sudola/oneri-son")
def sudola_oneri_son(link: str):
    """C2: Onceden persist edilmis sudola onerisini Gemini'yi tekrar
    cagirmadan dondurur. Proje secici varsayilanini doldurmak icin kullanilir."""
    bos = {"onerilen_proje_id": None, "onerilen_proje_adi": None, "skor": None}
    if not _db.DATABASE_URL:
        return bos
    firsat_id = _db.get_firsat_id_by_link(link)
    if not firsat_id:
        return bos
    son = _db.get_son_sudola_onerisi(firsat_id)
    if not son:
        return bos
    onerilen_proje_id = son.get("onerilen_proje_id")
    onerilen_proje_adi = None
    if onerilen_proje_id:
        projeler = dosya_oku(PROJELER_DOSYA, [])
        eslesen = next((p for p in projeler if p.get("id") == onerilen_proje_id), None)
        if eslesen:
            onerilen_proje_adi = eslesen.get("ad")
        else:
            onerilen_proje_id = None
    return {
        "onerilen_proje_id": onerilen_proje_id,
        "onerilen_proje_adi": onerilen_proje_adi,
        "skor": son.get("skor"),
    }
