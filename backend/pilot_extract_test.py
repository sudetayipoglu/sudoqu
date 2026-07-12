#!/usr/bin/env python3
"""
V1.2 pilot testi: Tavily Extract + Gemini structured output.
BU SCRIPT PRODUCTION'A ENTEGRE DEGILDIR. Sadece bagimsiz bir deneme/rapor aracidir.
radar.py ve api.py'a hicbir sekilde dokunmaz, ayri calisir.
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
if not TAVILY_API_KEY or not GEMINI_API_KEY:
    raise SystemExit("TAVILY_API_KEY veya GEMINI_API_KEY .env icinde bulunamadi.")

GEMINI_MODEL = "gemini-flash-latest"
GEMINI_MIN_INTERVAL = 13  # free tier ~5 req/dk limitine gore guvenli araligi


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


def call_tavily(client, url):
    try:
        result = client.extract(urls=[url], extract_depth="advanced", chunks_per_source=3)
        results = result.get("results", [])
        failed = result.get("failed_results", [])
        if results:
            raw = results[0].get("raw_content") or ""
            return {"success": True, "raw_content": raw, "char_count": len(raw), "error": None}
        err = failed[0].get("error") if failed else "bilinmeyen hata (bos sonuc)"
        return {"success": False, "raw_content": "", "char_count": 0, "error": err}
    except Exception as e:
        return {"success": False, "raw_content": "", "char_count": 0, "error": str(e)}


def call_gemini(gclient, url, raw_content, max_retries=2):
    prompt = f"""Asagida bir web sayfasindan/PDF'ten Tavily ile cikarilmis ham metin var.
Bu metinden bir yarisma / hackathon / burs / fuar / program firsatina dair
yapilandirilmis bilgiyi asagidaki semaya gore cikar.

COK ONEMLI KURAL: Bu bilgiyi metinde acikca bulamiyorsan o alani null birak.
ASLA UYDURMA, tahmin etme, varsayma. Sadece metinde gecen bilgiyi kullan.

Kaynak URL: {url}

--- HAM METIN BASLANGICI ---
{raw_content[:20000]}
--- HAM METIN SONU ---
"""
    last_err = None
    for attempt in range(max_retries + 1):
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
                "input_tokens": usage.prompt_token_count if usage else None,
                "output_tokens": usage.candidates_token_count if usage else None,
                "error": None,
            }
        except Exception as e:
            last_err = str(e)
            if "429" in last_err and attempt < max_retries:
                wait_s = 25
                print(f"    -> 429 (rate limit), {wait_s}sn beklenip tekrar denenecek (deneme {attempt + 1}/{max_retries})")
                time.sleep(wait_s)
                continue
            break
    return {"success": False, "parsed": None, "input_tokens": 0, "output_tokens": 0, "error": last_err}


def build_markdown(all_results, tavily_ok, tavily_fail, total_in, total_out, gemini_ok, gemini_fail):
    L = []
    L.append("# Pilot Test Sonuclari: Tavily Extract + Gemini Yapisal Veri Cikarimi\n\n")
    L.append(f"Tarih: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}\n\n")
    L.append(f"Model: {GEMINI_MODEL}\n\n")
    L.append("## Ozet\n\n")
    L.append(f"- Toplam link: {len(all_results)}\n")
    L.append(f"- Tavily basarili: {tavily_ok}\n")
    L.append(f"- Tavily basarisiz: {tavily_fail}\n")
    L.append(f"- Gemini basarili: {gemini_ok}\n")
    L.append(f"- Gemini basarisiz: {gemini_fail}\n")
    L.append(f"- Toplam Gemini input token: {total_in}\n")
    L.append(f"- Toplam Gemini output token: {total_out}\n\n")
    L.append("## Link Bazinda Detaylar\n")
    for r in all_results:
        L.append(f"\n### [{r['kategori']}] {r['url']}\n\n")
        tav = r["tavily"]
        L.append(f"**Tavily:** basarili={tav['success']}, karakter_sayisi={tav['char_count']}")
        if tav["error"]:
            L.append(f", hata={tav['error']}")
        L.append("\n\n")
        gem = r["gemini"]
        if gem is None:
            L.append("**Gemini:** calistirilmadi (Tavily basarisiz ya da icerik bos)\n")
        elif not gem["success"]:
            L.append(f"**Gemini:** basarisiz, hata={gem['error']}\n")
        else:
            L.append(f"**Gemini:** input_token={gem['input_tokens']}, output_token={gem['output_tokens']}\n\n")
            L.append("```json\n")
            L.append(json.dumps(gem["parsed"], ensure_ascii=False, indent=2))
            L.append("\n```\n")
        L.append("\n**Kalite degerlendirmesi:** _(elle doldurulacak)_\n")
    return "".join(L)


def main():
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    gclient = genai.Client(api_key=GEMINI_API_KEY)

    all_results = []
    total_in, total_out = 0, 0
    tavily_ok, tavily_fail = 0, 0
    gemini_ok, gemini_fail = 0, 0

    for idx, item in enumerate(LINKS):
        url, kategori = item["url"], item["kategori"]
        print(f"[{kategori}] {url}")
        tav = call_tavily(tavily, url)
        tavily_ok += 1 if tav["success"] else 0
        tavily_fail += 0 if tav["success"] else 1
        print(f"  tavily: success={tav['success']} chars={tav['char_count']} error={tav['error']}")

        gem = None
        if tav["success"] and tav["char_count"] > 0:
            gem = call_gemini(gclient, url, tav["raw_content"])
            if gem["success"]:
                gemini_ok += 1
                total_in += gem["input_tokens"] or 0
                total_out += gem["output_tokens"] or 0
            else:
                gemini_fail += 1
            print(f"  gemini: success={gem['success']} in={gem.get('input_tokens')} out={gem.get('output_tokens')} error={gem['error']}")
            if idx < len(LINKS) - 1:
                print(f"  ...{GEMINI_MIN_INTERVAL}sn bekleniyor (rate limit icin)...")
                time.sleep(GEMINI_MIN_INTERVAL)
        else:
            print("  gemini: atlandi")

        all_results.append({"kategori": kategori, "url": url, "tavily": tav, "gemini": gem})

    with open("pilot_raw_results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    md = build_markdown(all_results, tavily_ok, tavily_fail, total_in, total_out, gemini_ok, gemini_fail)
    with open("pilot_sonuclari.md", "w", encoding="utf-8") as f:
        f.write(md)

    print("\n=== OZET ===", flush=True)
    print(f"Tavily basarili: {tavily_ok}/{len(LINKS)}")
    print(f"Tavily basarisiz: {tavily_fail}/{len(LINKS)}")
    print(f"Gemini basarili: {gemini_ok}")
    print(f"Gemini basarisiz: {gemini_fail}")
    print(f"Toplam Gemini input token: {total_in}")
    print(f"Toplam Gemini output token: {total_out}")
    print("pilot_sonuclari.md ve pilot_raw_results.json yazildi.")


if __name__ == "__main__":
    main()
