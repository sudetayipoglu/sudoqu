import os
import json
import time
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel
from openai import OpenAI

load_dotenv()
API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = "https://integrate.api.nvidia.com/v1"

MIN_INTERVAL = 5
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

MODELS = [
    ("mistral_medium_3_5", "mistralai/mistral-medium-3.5-128b"),
    ("glm_5_2", "z-ai/glm-5.2"),
    ("step_3_7_flash", "stepfun-ai/step-3.7-flash"),
    ("deepseek_v4_pro", "deepseek-ai/deepseek-v4-pro"),
    ("llama_3_1_70b", "meta/llama-3.1-70b-instruct"),
]


def build_prompt(url, raw_content):
    return f"""Asagida bir web sayfasindan/PDF'ten Tavily ile cikarilmis ham metin var.
Bu metinden bir yarisma / hackathon / burs / fuar / program firsatina dair
yapilandirilmis bilgiyi asagidaki semaya gore cikar.

COK ONEMLI KURALLAR:
1. Bu bilgiyi metinde bulamiyorsan UYDURMA, null birak. ASLA UYDURMA, tahmin etme, varsayma. Sadece metinde gecen bilgiyi kullan.
2. Kaynak metin hangi dilde olursa olsun, TUM cikti alanlarini TURKCEYE CEVIREREK yaz.
3. Tarihleri HER ZAMAN YYYY-MM-DD formatina normalize et (tahmin edilebiliyorsa), yoksa null birak.

Kaynak URL: {url}

--- HAM METIN BASLANGICI ---
{raw_content[:20000]}
--- HAM METIN SONU ---

SADECE gecerli JSON dondur, baska hicbir aciklama/metin ekleme. JSON disinda tek bir karakter bile yazma. Alanlar: organizator, konu_kategori, son_basvuru_tarihi, onemli_tarihler, basvuru_asamalari, yer_mekan, konaklama_yol_destegi (bool), odul_miktari_turu, katilim_sartlari, takim_buyuklugu_limiti, basvuru_maliyeti, istenen_materyal, sponsor_kurumlar."""


def call_model(client, model_id, url, raw_content):
    prompt = build_prompt(url, raw_content)
    last_err = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            try:
                resp = client.chat.completions.create(
                    model=model_id,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0,
                )
            except Exception:
                resp = client.chat.completions.create(
                    model=model_id,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )
            content = resp.choices[0].message.content
            usage = resp.usage
            text = (content or "").strip()
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
            gecici = (
                ("429" in last_err)
                or ("503" in last_err)
                or ("rate" in last_err.lower())
                or ("resourceexhausted" in last_err.lower())
            )
            if gecici and attempt < MAX_RETRIES:
                wait_s = 20
                print(f"    -> gecici hata, {wait_s}sn beklenip tekrar denenecek: {last_err[:100]}")
                time.sleep(wait_s)
                continue
            break
    return {"success": False, "parsed": None, "raw_text": None, "input_tokens": 0, "output_tokens": 0, "error": last_err}


def run_model_test(client, model_slug, model_id, tavily_cache):
    print(f"\n=== MODEL: {model_id} ===")
    results = []
    total_in, total_out = 0, 0
    ok_count = 0
    start = time.time()
    for idx, item in enumerate(tavily_cache):
        tav = item["tavily"]
        print(f"[{idx+1}/{len(tavily_cache)}] {model_slug} {item['kategori']} {item['url'][:70]}")
        t0 = time.time()
        if not tav["success"] or tav["char_count"] == 0:
            r = {"success": False, "parsed": None, "error": "tavily basarisiz/bos", "input_tokens": 0, "output_tokens": 0}
        else:
            r = call_model(client, model_id, item["url"], tav["raw_content"])
        elapsed = time.time() - t0
        if r["success"]:
            ok_count += 1
            total_in += r["input_tokens"] or 0
            total_out += r["output_tokens"] or 0
        print(f"  success={r['success']} in={r.get('input_tokens')} out={r.get('output_tokens')} sure={elapsed:.1f}sn error={str(r.get('error'))[:100]}")
        results.append({"kategori": item["kategori"], "url": item["url"], "tavily_chars": tav["char_count"], "model_result": r, "sure_sn": elapsed})
        if idx < len(tavily_cache) - 1:
            time.sleep(MIN_INTERVAL)
    toplam_sure = time.time() - start
    print(f"\n{model_slug} OZET: basarili={ok_count}/{len(tavily_cache)} toplam_in={total_in} toplam_out={total_out} toplam_sure={toplam_sure:.0f}sn")
    with open(f"model_test_v2_{model_slug}_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return {
        "model_id": model_id,
        "ok_count": ok_count,
        "total": len(tavily_cache),
        "total_in": total_in,
        "total_out": total_out,
        "toplam_sure": toplam_sure,
    }


if __name__ == "__main__":
    with open("model_test_tavily_cache.json", "r", encoding="utf-8") as f:
        cache = json.load(f)

    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

    summary = {}
    if os.path.exists("model_test_v2_summary.json"):
        with open("model_test_v2_summary.json", "r", encoding="utf-8") as f:
            summary = json.load(f)

    for slug, model_id in MODELS:
        out_file = f"model_test_v2_{slug}_results.json"
        if slug in summary and os.path.exists(out_file):
            print(f"{slug} sonuclari zaten var, atlaniyor.")
            continue
        s = run_model_test(client, slug, model_id, cache)
        summary[slug] = {
            "model_id": s["model_id"],
            "ok_count": s["ok_count"],
            "total": s["total"],
            "total_in": s["total_in"],
            "total_out": s["total_out"],
            "toplam_sure": s["toplam_sure"],
        }
        with open("model_test_v2_summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        time.sleep(3)

    print("\nTUM MODEL TESTLERI TAMAMLANDI.")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
