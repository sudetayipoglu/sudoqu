from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import os
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
