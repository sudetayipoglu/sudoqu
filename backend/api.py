from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import json
import os
import re
import time
import uuid
import requests
from datetime import datetime

app = FastAPI(title="SudoQu API")

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

def dosya_oku(yol, varsayilan):
    if os.path.exists(yol):
        with open(yol, encoding="utf-8") as f:
            return json.load(f)
    return varsayilan

def dosya_yaz(yol, veri):
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)

@app.get("/")
def anasayfa():
    return {"durum": "SudoQu API calisiyor"}

@app.get("/firsatlar")
def firsatlari_getir():
    return dosya_oku(FIRSATLAR_DOSYA, [])

@app.get("/basvurular")
def basvurulari_getir():
    return dosya_oku(BASVURULAR_DOSYA, {})

@app.post("/basvurular/{link:path}")
def basvuru_ekle(link: str):
    firsatlar = dosya_oku(FIRSATLAR_DOSYA, [])
    basvurular = dosya_oku(BASVURULAR_DOSYA, {})
    secilen = next((f for f in firsatlar if f["link"] == link), None)
    if not secilen:
        return {"hata": "Fırsat bulunamadı"}
    basvurular[link] = {
        "baslik": secilen["baslik"],
        "link": link,
        "durum": "beklemede"
    }
    dosya_yaz(BASVURULAR_DOSYA, basvurular)
    return {"basari": True, "eklenen": basvurular[link]}

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
def task_ekle(baslik: str, atanan: str, tur: str = "task", deadline: str = None):
    tasklar = dosya_oku(TASKLAR_DOSYA, [])
    yeni = {
        "id": len(tasklar) + 1,
        "baslik": baslik,
        "atanan": atanan,
        "tur": tur,
        "deadline": deadline,
        "durum": "bekliyor",
        "olusturma_tarihi": datetime.now().strftime("%Y-%m-%d %H:%M")
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
