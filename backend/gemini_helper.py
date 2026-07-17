# Merkezi Gemini API anahtar rotasyonu.
# TUM Gemini cagrilari (radar.py extraction, api.py sudola soru-cevap, api.py proje onerisi)
# bu modulu (call_gemini) kullanmali - ayri ayri client olusturulmamali.
# UYARI: Tavily'de tam bu noktada hata yapilmisti (extract fonksiyonu ayri, sabit bir
# client kullaniyordu, rotasyona hic girmiyordu) - AYNI HATA BURADA TEKRARLANMAMALI.
import os
import json
from secret_helper import get_secret_or_env
from google import genai

GEMINI_ANAHTARLARI = []
for _i in range(1, 5):
    _val = get_secret_or_env(f"gemini-api-key-{_i}", f"GEMINI_API_KEY_{_i}")
    if _val:
        GEMINI_ANAHTARLARI.append(_val)

print(f"[gemini] {len(GEMINI_ANAHTARLARI)} adet API key yuklendi (rotasyonlu).\n")

_GEMINI_DURUM_DOSYA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gemini_anahtar_durumu.json")


def _anahtar_idx_oku():
    if os.path.exists(_GEMINI_DURUM_DOSYA):
        try:
            with open(_GEMINI_DURUM_DOSYA, "r", encoding="utf-8") as f:
                return int(json.load(f).get("idx", 0))
        except Exception:
            return 0
    return 0


def _anahtar_idx_yaz(idx):
    try:
        with open(_GEMINI_DURUM_DOSYA, "w", encoding="utf-8") as f:
            json.dump({"idx": idx}, f)
    except Exception:
        pass


_gemini_idx = _anahtar_idx_oku()


def call_gemini(model, contents, _anahtar_listesi=None, **kwargs):
    # Gemini'yi N anahtar rotasyonuyla cagirir. Bir anahtar HERHANGI bir hata verirse
    # (kota/429, rate-limit, gecersiz anahtar, vb.) otomatik siradaki anahtara gecer.
    # Hepsi tukenirse, en son hatayi (429/quota bilgisini kaybetmeden) tasiyan acik bir
    # hata firlatir - extract_tek_kayit'teki mevcut kota_doldu tespiti bu metne gore calisir.
    # _anahtar_listesi: sadece test/dogrulama amacli, gercek listeyi override etmek icin.
    global _gemini_idx
    anahtarlar = _anahtar_listesi if _anahtar_listesi is not None else GEMINI_ANAHTARLARI
    n = len(anahtarlar)
    if n == 0:
        raise RuntimeError("Hicbir Gemini API anahtari yuklenemedi (gemini-api-key-1..4 kontrol edin).")
    denenen = 0
    son_hata = None
    idx = _gemini_idx % n
    while denenen < n:
        try:
            client = genai.Client(api_key=anahtarlar[idx])
            response = client.models.generate_content(model=model, contents=contents, **kwargs)
            if _anahtar_listesi is None:
                _gemini_idx = idx
                _anahtar_idx_yaz(_gemini_idx)
            return response
        except Exception as e:
            son_hata = e
            hata_metni = str(e).lower()
            kota_mu = ("429" in hata_metni) or ("quota" in hata_metni) or ("resource_exhausted" in hata_metni) or ("rate" in hata_metni and "limit" in hata_metni)
            etiket = "kota/rate-limit" if kota_mu else "hata"
            print(f"    [gemini] key #{idx + 1}/{n} {etiket}, siradaki key deneniyor... ({str(e)[:100]})")
            idx = (idx + 1) % n
            denenen += 1
            continue
    raise RuntimeError(f"Tum {n} Gemini key de basarisiz oldu (429/kota dahil olabilir). Son hata: {son_hata}")
