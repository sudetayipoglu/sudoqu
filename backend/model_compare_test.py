#!/usr/bin/env python3
"""
Model karsilastirma pilotu: ayni 12 link + ayni sema/prompt ile
Gemini 2.5 Flash-Lite ve (onaylaninca) DeepSeek karsilastirmasi.
BU SCRIPT PRODUCTION'A ENTEGRE DEGILDIR, radar.py'a dokunmaz.
"""
import os
import json
import time
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel
from tavily import TavilyClient
from google import genai
from google.genai import types

load_dotenv()

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

GEMINI_MODEL = "gemini-flash-lite-latest"
GEMINI_MIN_INTERVAL = 13
MAX_RETRIES = 2


class OpportunityExtract(BaseModel):
    organizator: Optional[str] = None
    konu_kategori: Optional[str] = None
    son_basvuru_tarihi: Optional[str] = None
    onemli_tarihler: Optional[str] = None
    basvuru_asamalari: Optional[str] = None
    yer_mekan: Optional[str] = None
    konaklama_yol_destegi: Optional[bool] = None
    odul_miktari_turu: Optional[str] = None
    katilim_sartlari: Optional[str] = None
    takim_buyuklugu_limiti: Optional[str] = None
    basvuru_maliyeti: Optional[str] = None
    istenen_materyal: Optional[str] = None
    sponsor_kurumlar: Optional[str] = None


EXTRACTION_FIELDS = list(OpportunityExtract.model_fields.keys())

LINKS = [
    {"kategori": "universite", "url": "https://ajanda.ibu.edu.tr/teknofest-2026-teknoloji-yarismalari-basvurulari-uzatildi"},
    {"kategori": "universite", "url": "https://www.karatay.edu.tr/tr/duyuru/2026/04/14/girisimcilik-maratonu-2026-basvurulari-basladi"},
    {"kategori": "universite", "url": "https://www.mehmetakif.edu.tr/content/12997/1/teknofest-girisim-programi-2026-basvurulari-basladi"},
    {"kategori": "devlet", "url": "https://bilimgenc.tubitak.gov.tr/makale/teknofest-2026-teknoloji-yarismalari-basvurulari-basladi"},
    {"kategori": "devlet", "url": "https://sgb.meb.gov.tr/www/2026-yili-ar-ge-bulusmalari-kapsaminda-quotgirisimcilik-ve-ogrenci-liderligi-calistayiquot-gerceklestirildi/icerik/821"},
    {"kategori": "instagram", "url": "https://www.instagram.com/p/DTTNZByCpou"},
    {"kategori": "instagram", "url": "https://www.instagram.com/reel/DWgbOHujXyI?hl=en"},
    {"kategori": "pdf_tr", "url": "https://www.atonet.org.tr/Yuklemeler/kurumsal_iletisim_ve_basin_yayin_mudurlugu/TEKNOFEST%202026%20Yar%C4%B1%C5%9Fmalar%20Ba%C5%9Fvuru%20K%C4%B1lavuzu.pdf"},
    {"kategori": "yabanci_dil_pdf_fr", "url": "https://www.ubacameroon.com/wp-content/uploads/sites/8/2026/01/LANCEMENT-DU-PROGRAMME-TEF-2026.pdf"},
    {"kategori": "yabanci_dil_zh", "url": "https://www.nsfc.gov.cn/p1/3381/2824/99667.html"},
    {"kategori": "yabanci_dil_ja", "url": "https://www.jetro.go.jp/services/j-starx/pre-startup.html"},
    {"kategori": "genel_org_sayfasi", "url": "https://www.teknofest.org"},
]


def call_tavily_extract(tavily_client, url):
    try:
        result = tavily_client.extract(urls=[url], extract_depth="advanced", chunks_per_source=3)
        results = result.get("results", [])
        failed = result.get("failed_results", [])
        if results:
            raw = results[0].get("raw_content") or ""
            return {"success": True, "raw_content": raw, "char_count": len(raw), "error": None}
        err = failed[0].get("error") if failed else "bilinmeyen hata (bos sonuc)"
        return {"success": False, "raw_content": "", "char_count": 0, "error": err}
    except Exception as e:
        return {"success": False, "raw_content": "", "char_count": 0, "error": str(e)}


def build_prompt(url, raw_content):
    return f"""Asagida bir web sayfasindan/PDF'ten Tavily ile cikarilmis ham metin var.
Bu metinden bir yarisma / hackathon / burs / fuar / program firsatina dair
yapilandirilmis bilgiyi asagidaki semaya gore cikar.

COK ONEMLI KURAL: Bu bilgiyi metinde bulamiyorsan uydurma, null birak.
ASLA UYDURMA, tahmin etme, varsayma. Sadece metinde gecen bilgiyi kullan.

Kaynak URL: {url}

--- HAM METIN BASLANGICI ---
{raw_content[:20000]}
--- HAM METIN SONU ---
"""


def fetch_all_tavily(links):
    """Tum linkler icin Tavily extract'i BIR KEZ calistirir, sonuclari her iki
    model testinde de yeniden kullanmak icin diske kaydeder (Tavily kredisi tasarrufu)."""
    cache_path = "model_test_tavily_cache.json"
    if os.path.exists(cache_path):
        print("Tavily cache bulundu, yeniden kullaniliyor.")
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)

    tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
    cache = []
    for item in links:
        print(f"[tavily] {item['kategori']} {item['url']}")
        tav = call_tavily_extract(tavily_client, item["url"])
        cache.append({"kategori": item["kategori"], "url": item["url"], "tavily": tav})
        print(f"  success={tav['success']} chars={tav['char_count']} error={tav['error']}")
        time.sleep(1)

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    return cache


def call_gemini_lite(gclient, url, raw_content):
    prompt = build_prompt(url, raw_content)
    last_err = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = gclient.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=OpportunityExtract,
                ),
            )
            usage = response.usage_metadata
            return {
                "success": True,
                "parsed": response.parsed.model_dump() if response.parsed else None,
                "raw_text": response.text,
                "input_tokens": usage.prompt_token_count if usage else 0,
                "output_tokens": usage.candidates_token_count if usage else 0,
                "error": None,
            }
        except Exception as e:
            last_err = str(e)
            gecici = ("429" in last_err) or ("503" in last_err) or ("UNAVAILABLE" in last_err)
            if gecici and attempt < MAX_RETRIES:
                wait_s = 60 if "429" in last_err else 20
                print(f"    -> gecici hata, {wait_s}sn beklenip tekrar denenecek: {last_err[:80]}")
                time.sleep(wait_s)
                continue
            break
    return {"success": False, "parsed": None, "raw_text": None, "input_tokens": 0, "output_tokens": 0, "error": last_err}


def run_gemini_lite_test(tavily_cache):
    gclient = genai.Client(api_key=GEMINI_API_KEY)
    results = []
    total_in, total_out = 0, 0
    ok_count = 0
    start = time.time()
    for idx, item in enumerate(tavily_cache):
        tav = item["tavily"]
        print(f"[{idx+1}/{len(tavily_cache)}] gemini-lite {item['kategori']} {item['url']}")
        t0 = time.time()
        if not tav["success"] or tav["char_count"] == 0:
            gem = {"success": False, "parsed": None, "error": "tavily basarisiz/bos", "input_tokens": 0, "output_tokens": 0}
        else:
            gem = call_gemini_lite(gclient, item["url"], tav["raw_content"])
        elapsed = time.time() - t0
        if gem["success"]:
            ok_count += 1
            total_in += gem["input_tokens"] or 0
            total_out += gem["output_tokens"] or 0
        print(f"  success={gem['success']} in={gem.get('input_tokens')} out={gem.get('output_tokens')} sure={elapsed:.1f}sn error={gem.get('error')}")
        results.append({"kategori": item["kategori"], "url": item["url"], "tavily_chars": tav["char_count"], "gemini_lite": gem, "sure_sn": elapsed})
        if idx < len(tavily_cache) - 1:
            time.sleep(GEMINI_MIN_INTERVAL)
    toplam_sure = time.time() - start
    print(f"\nGEMINI-LITE OZET: basarili={ok_count}/{len(tavily_cache)} toplam_in={total_in} toplam_out={total_out} toplam_sure={toplam_sure:.0f}sn")
    with open("model_test_gemini_lite_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return results


# --- DeepSeek V4 Flash (NVIDIA NIM uzerinden, OpenAI-uyumlu) ---
from openai import OpenAI

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEEPSEEK_MODEL = "deepseek-ai/deepseek-v4-flash"
DEEPSEEK_MIN_INTERVAL = 5


def call_deepseek(ds_client, url, raw_content):
    prompt = build_prompt(url, raw_content) + "\n\nSADECE gecerli JSON dondur, baska hicbir aciklama/metin ekleme. JSON disinda tek bir karakter bile yazma."
    last_err = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            try:
                resp = ds_client.chat.completions.create(
                    model=DEEPSEEK_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0,
                )
            except Exception:
                resp = ds_client.chat.completions.create(
                    model=DEEPSEEK_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )
            content = resp.choices[0].message.content
            usage = resp.usage
            text = content.strip()
            if text.startswith("```"):
                text = text.strip("`")
                if text.lower().startswith("json"):
                    text = text[4:]
            parsed_raw = json.loads(text)
            parsed = OpportunityExtract(**{k: parsed_raw.get(k) for k in EXTRACTION_FIELDS}).model_dump()
            return {
                "success": True,
                "parsed": parsed,
                "raw_text": content,
                "input_tokens": usage.prompt_tokens if usage else 0,
                "output_tokens": usage.completion_tokens if usage else 0,
                "error": None,
            }
        except Exception as e:
            last_err = str(e)
            gecici = ("429" in last_err) or ("503" in last_err) or ("rate" in last_err.lower())
            if gecici and attempt < MAX_RETRIES:
                wait_s = 20
                print(f"    -> gecici hata, {wait_s}sn beklenip tekrar denenecek: {last_err[:80]}")
                time.sleep(wait_s)
                continue
            break
    return {"success": False, "parsed": None, "raw_text": None, "input_tokens": 0, "output_tokens": 0, "error": last_err}


def run_deepseek_test(tavily_cache):
    ds_client = OpenAI(base_url=DEEPSEEK_BASE_URL, api_key=DEEPSEEK_API_KEY)
    results = []
    total_in, total_out = 0, 0
    ok_count = 0
    start = time.time()
    for idx, item in enumerate(tavily_cache):
        tav = item["tavily"]
        print(f"[{idx+1}/{len(tavily_cache)}] deepseek {item['kategori']} {item['url']}")
        t0 = time.time()
        if not tav["success"] or tav["char_count"] == 0:
            ds = {"success": False, "parsed": None, "error": "tavily basarisiz/bos", "input_tokens": 0, "output_tokens": 0}
        else:
            ds = call_deepseek(ds_client, item["url"], tav["raw_content"])
        elapsed = time.time() - t0
        if ds["success"]:
            ok_count += 1
            total_in += ds["input_tokens"] or 0
            total_out += ds["output_tokens"] or 0
        print(f"  success={ds['success']} in={ds.get('input_tokens')} out={ds.get('output_tokens')} sure={elapsed:.1f}sn error={ds.get('error')}")
        results.append({"kategori": item["kategori"], "url": item["url"], "tavily_chars": tav["char_count"], "deepseek": ds, "sure_sn": elapsed})
        if idx < len(tavily_cache) - 1:
            time.sleep(DEEPSEEK_MIN_INTERVAL)
    toplam_sure = time.time() - start
    print(f"\nDEEPSEEK OZET: basarili={ok_count}/{len(tavily_cache)} toplam_in={total_in} toplam_out={total_out} toplam_sure={toplam_sure:.0f}sn")
    with open("model_test_deepseek_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return results


if __name__ == "__main__":
    cache = fetch_all_tavily(LINKS)

    if os.path.exists("model_test_gemini_lite_results.json"):
        print("Gemini-lite sonuclari zaten var, tekrar calistirilmiyor.")
        with open("model_test_gemini_lite_results.json", "r", encoding="utf-8") as f:
            gemini_lite_results = json.load(f)
    else:
        gemini_lite_results = run_gemini_lite_test(cache)

    deepseek_results = run_deepseek_test(cache)

    print("\nTUM TESTLER TAMAMLANDI.")
