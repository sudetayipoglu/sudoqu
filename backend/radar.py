from tavily import TavilyClient
from dotenv import load_dotenv
import os
import json
from datetime import datetime

load_dotenv()
from secret_helper import get_secret_or_env
api_key = get_secret_or_env("tavily-api-key", "TAVILY_API_KEY")
client = TavilyClient(api_key=api_key)

# --- V1.3: Tavily Extract + Gemini yapisal veri cikarim pipeline'i (pilot testte dogrulandi) ---
import time as _time
from urllib.parse import urlparse
from typing import Optional
from pydantic import BaseModel
from google import genai
from google.genai import types

GEMINI_API_KEY = get_secret_or_env("gemini-api-key", "GEMINI_API_KEY")
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# TEKILLESTIRME (DEDUP) MANTIGI - kural bazli, LLM kullanilmaz
import re
import difflib as _difflib
from collections import defaultdict as _defaultdict
from datetime import datetime as _datetime

_DEDUP_ALANLAR = [
    "organizator", "konu_kategori", "son_basvuru_tarihi", "onemli_tarihler",
    "basvuru_asamalari", "yer_mekan", "konaklama_yol_destegi", "odul_miktari_turu",
    "katilim_sartlari", "takim_buyuklugu_limiti", "basvuru_maliyeti",
    "istenen_materyal", "sponsor_kurumlar",
]


def _normalize_organizator(s):
    if not s:
        return None
    return re.sub(r"\s+", " ", s.strip().lower())


_TR_AYLAR = {
    "ocak": 1, "subat": 2, "şubat": 2, "mart": 3, "nisan": 4,
    "mayis": 5, "mayıs": 5, "haziran": 6, "temmuz": 7, "agustos": 8,
    "ağustos": 8, "eylul": 9, "eylül": 9, "ekim": 10,
    "kasim": 11, "kasım": 11, "aralik": 12, "aralık": 12,
}


def _tarih_parse(s):
    if not s:
        return None
    s = s.strip()
    try:
        return _datetime.strptime(s, "%Y-%m-%d")
    except Exception:
        pass
    parcalar = s.lower().split()
    if len(parcalar) == 3:
        gun_s, ay_s, yil_s = parcalar
        ay = _TR_AYLAR.get(ay_s)
        if ay:
            try:
                gun = int(gun_s)
                yil = int(yil_s)
                return _datetime(yil, ay, gun)
            except Exception:
                return None
    return None


def _doluluk(r):
    return sum(1 for f in _DEDUP_ALANLAR if r.get(f) not in (None, "", "null"))


def tekillestir(veri_listesi):
    gruplar = _defaultdict(list)
    for r in veri_listesi:
        org = r.get("organizator")
        norm = _normalize_organizator(org)
        if not norm:
            continue
        gruplar[norm].append(r)

    dup_sayisi = 0
    dup_gruplari = []

    for org_norm, kayitlar in gruplar.items():
        n = len(kayitlar)
        if n < 2:
            continue
        used = set()
        for i in range(n):
            if i in used:
                continue
            grup_idx = [i]
            for j in range(i + 1, n):
                if j in used:
                    continue
                ri, rj = kayitlar[i], kayitlar[j]

                ti = _tarih_parse(ri.get("son_basvuru_tarihi"))
                tj = _tarih_parse(rj.get("son_basvuru_tarihi"))
                if ti is None or tj is None:
                    tarih_yakin = False
                else:
                    tarih_yakin = abs((ti - tj).days) <= 1

                konu_i = (ri.get("konu_kategori") or ri.get("baslik") or "").lower()
                konu_j = (rj.get("konu_kategori") or rj.get("baslik") or "").lower()
                if konu_i and konu_j:
                    benzerlik = _difflib.SequenceMatcher(None, konu_i, konu_j).ratio()
                else:
                    benzerlik = 0.0
                konu_benzer = benzerlik >= 0.6

                if tarih_yakin and konu_benzer:
                    grup_idx.append(j)

            if len(grup_idx) > 1:
                for idx in grup_idx:
                    used.add(idx)
                grup_kayitlar = [kayitlar[idx] for idx in grup_idx]
                grup_kayitlar.sort(key=_doluluk, reverse=True)
                birincil = grup_kayitlar[0]
                if "duplicate_of" in birincil:
                    del birincil["duplicate_of"]
                for ikincil in grup_kayitlar[1:]:
                    ikincil["duplicate_of"] = birincil.get("link")
                    dup_sayisi += 1
                dup_gruplari.append({
                    "organizator": org_norm,
                    "birincil": birincil.get("link"),
                    "ikincil_sayisi": len(grup_kayitlar) - 1,
                    "linkler": [k.get("link") for k in grup_kayitlar],
                })

    return dup_sayisi, dup_gruplari
GEMINI_MODEL = "gemini-flash-lite-latest"  # gemini-2.5-flash-lite artik 404 (deprecated); bu alias canli test edildi, su an gemini-3.1-flash-lite'e cozuluyor
GEMINI_MIN_INTERVAL = 13
GEMINI_429_WAIT = 60
GEMINI_MAX_RETRIES = 2

# DIKKAT: Bu deger islenecek 'henuz_islenmedi' kayit sayisini sinirlar.
# Test amacli kucuk tutulmali; tum birikmis kayitlara karsi calistirmadan once
# KULLANICI ONAYI alinmalidir. Onaydan sonra bu degeri artirin ya da None yapin.
TEST_LIMIT = None


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


def is_root_page(url):
    try:
        path = urlparse(url).path.strip("/")
        return path == ""
    except Exception:
        return False


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


def call_gemini_extract(url, raw_content):
    prompt = f"""Asagida bir web sayfasindan/PDF'ten Tavily ile cikarilmis ham metin var.
Bu metinden bir yarisma / hackathon / burs / fuar / program firsatina dair
yapilandirilmis bilgiyi asagidaki semaya gore cikar.

COK ONEMLI KURALLAR:
1. Bu bilgiyi metinde acikca bulamiyorsan o alani null birak. ASLA UYDURMA, tahmin etme, varsayma. Sadece metinde gecen bilgiyi kullan.
2. Kaynak metin hangi dilde olursa olsun, TUM cikti alanlarini TURKCEYE CEVIREREK yaz.
3. Tarihleri HER ZAMAN YYYY-MM-DD formatina normalize et (tahmin edilebiliyorsa), yoksa null birak.
4. onemli_tarihler alanina birden fazla tarih varsa (basvuru baslangici, on eleme, final gibi), hepsini TEK BIR serbest metin string'i icinde, virgul veya noktayla ayirarak yaz - ASLA liste/array dondurme, her zaman tek bir string olmali.

Kaynak URL: {url}

--- HAM METIN BASLANGICI ---
{raw_content[:20000]}
--- HAM METIN SONU ---
"""
    last_err = None
    for attempt in range(GEMINI_MAX_RETRIES + 1):
        try:
            response = gemini_client.models.generate_content(
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
                "input_tokens": usage.prompt_token_count if usage else 0,
                "output_tokens": usage.candidates_token_count if usage else 0,
                "error": None,
            }
        except Exception as e:
            last_err = str(e)
            gecici_hata = ("429" in last_err) or ("503" in last_err) or ("UNAVAILABLE" in last_err)
            if gecici_hata and attempt < GEMINI_MAX_RETRIES:
                wait_s = GEMINI_429_WAIT if "429" in last_err else 20
                print(f"    -> gecici hata, {wait_s}sn beklenip tekrar denenecek (deneme {attempt + 1}/{GEMINI_MAX_RETRIES}): {last_err[:80]}")
                _time.sleep(wait_s)
                continue
            break
    return {"success": False, "parsed": None, "input_tokens": 0, "output_tokens": 0, "error": last_err}


def bos_extraction_alanlari():
    return {alan: None for alan in EXTRACTION_FIELDS}


def extract_tek_kayit(tavily_client, kayit):
    """Tek bir firsat kaydi icin extraction calistirir, kaydi yerinde gunceller."""
    url = kayit.get("link", "")
    simdi = datetime.now().isoformat(timespec="seconds")

    if is_root_page(url):
        kayit.update(bos_extraction_alanlari())
        kayit["extraction_durumu"] = "atlandi_genel_sayfa"
        kayit["extraction_tarihi"] = simdi
        print(f"  [atlandi_genel_sayfa] {url}")
        return None

    tav = call_tavily_extract(tavily_client, url)
    if not tav["success"]:
        kayit.update(bos_extraction_alanlari())
        kayit["extraction_durumu"] = "basarisiz"
        kayit["extraction_tarihi"] = simdi
        print(f"  [basarisiz] tavily hatasi: {tav['error']} - {url}")
        return None

    if tav["char_count"] == 0:
        kayit.update(bos_extraction_alanlari())
        kayit["extraction_durumu"] = "basarili"
        kayit["extraction_tarihi"] = simdi
        print(f"  [basarili] icerik bos, alanlar null - {url}")
        return None

    if gemini_client is None:
        kayit["extraction_durumu"] = "basarisiz"
        kayit["extraction_tarihi"] = simdi
        print(f"  [basarisiz] GEMINI_API_KEY yok - {url}")
        return None

    gem = call_gemini_extract(url, tav["raw_content"])
    if gem["success"]:
        for alan in EXTRACTION_FIELDS:
            kayit[alan] = gem["parsed"].get(alan) if gem["parsed"] else None
        kayit["extraction_durumu"] = "basarili"
        kayit["extraction_tarihi"] = simdi
        print(f"  [basarili] in={gem['input_tokens']} out={gem['output_tokens']} - {url}")
        return {"input_tokens": gem["input_tokens"] or 0, "output_tokens": gem["output_tokens"] or 0}

    kayit.update(bos_extraction_alanlari())
    kayit["extraction_durumu"] = "basarisiz"
    kayit["extraction_tarihi"] = simdi
    print(f"  [basarisiz] gemini hatasi: {gem['error']} - {url}")
    return None
# --- V1.3 pipeline sonu ---

yil = datetime.now().year

# Genel kategoriler artık bir bağlam kelimesiyle ("teknoloji" / "girişimcilik") eşleniyor — gürültüyü azaltmak için
genel_kategoriler = {
    "tr": ["teknoloji yarışması", "teknoloji fuarı", "teknoloji kongresi", "girişimcilik çalıştayı", "teknoloji etkinliği"],
    "en": ["technology competition", "technology fair", "technology congress", "entrepreneurship workshop", "technology event"],
    "de": ["Technologiewettbewerb", "Technologiemesse", "Technologiekongress", "Gründer-Workshop", "Technologieveranstaltung"],
    "fr": ["concours technologique", "salon technologique", "congrès technologique", "atelier d'entrepreneuriat", "événement technologique"],
    "nl": ["technologiewedstrijd", "technologiebeurs", "technologiecongres", "ondernemerschapsworkshop", "technologie-evenement"],
    "sv": ["teknik­tävling", "teknikmässa", "teknikkongress", "entreprenörskapsworkshop", "teknikevenemang"],
    "ja": ["技術コンテスト", "技術展示会", "技術会議", "起業ワークショップ", "技術イベント"],
    "ko": ["기술 대회", "기술 박람회", "기술 학회", "창업 워크숍", "기술 이벤트"],
    "zh": ["技术比赛", "技术展会", "技术大会", "创业工作坊", "科技活动"],
}

loanword_latin = ["hackathon", "datathon", "ideathon"]
loanword_ja = ["ハッカソン", "データソン", "アイデアソン"]
loanword_ko = ["해커톤", "데이터톤", "아이디어톤"]
loanword_zh = ["黑客马拉松", "数据松"]

programlar_tr = ["hızlandırma programı", "girişimcilik programı", "hibe programı", "yatırım programı"]
programlar_en = ["accelerator program", "entrepreneurship program", "grant program", "investment program"]
programlar_de = ["Beschleunigerprogramm", "Gründerprogramm", "Förderprogramm", "Investitionsprogramm"]
programlar_fr = ["programme d'accélération", "programme d'entrepreneuriat", "programme de subvention", "programme d'investissement"]
programlar_nl = ["acceleratieprogramma", "ondernemerschapsprogramma", "subsidieprogramma", "investeringsprogramma"]
programlar_sv = ["acceleratorprogram", "entreprenörskapsprogram", "bidragsprogram", "investeringsprogram"]
programlar_ja = ["アクセラレータープログラム", "起業家プログラム", "助成金プログラム", "投資プログラム"]
programlar_ko = ["액셀러레이터 프로그램", "창업 프로그램", "보조금 프로그램", "투자 프로그램"]
programlar_zh = ["加速器项目", "创业项目", "资助项目", "投资项目"]

sorgular = []

for kelime in genel_kategoriler["tr"] + loanword_latin + programlar_tr:
    sorgular.append(f"{kelime} {yil} Türkiye başvuru")

for kelime in genel_kategoriler["en"] + loanword_latin + programlar_en:
    sorgular.append(f"{kelime} {yil} application")
for kelime in genel_kategoriler["de"] + loanword_latin + programlar_de:
    sorgular.append(f"{kelime} {yil}")
for kelime in genel_kategoriler["fr"] + loanword_latin + programlar_fr:
    sorgular.append(f"{kelime} {yil}")
for kelime in genel_kategoriler["nl"] + loanword_latin + programlar_nl:
    sorgular.append(f"{kelime} {yil}")
for kelime in genel_kategoriler["sv"] + loanword_latin + programlar_sv:
    sorgular.append(f"{kelime} {yil}")

for kelime in genel_kategoriler["ja"] + loanword_ja + programlar_ja:
    sorgular.append(f"{kelime} {yil}")
for kelime in genel_kategoriler["ko"] + loanword_ko + programlar_ko:
    sorgular.append(f"{kelime} {yil}")
for kelime in genel_kategoriler["zh"] + loanword_zh + programlar_zh:
    sorgular.append(f"{kelime} {yil}")

bulunanlar = {}

SKIP_SEARCH = os.getenv("RADAR_SKIP_SEARCH", "0") == "1"
if SKIP_SEARCH:
    print("RADAR_SKIP_SEARCH=1: yeni arama atlaniyor, sadece mevcut henuz_islenmedi kayitlar icin extraction calisacak.\n")
else:
    print(f"Toplam {len(sorgular)} sorgu ile tarama başlıyor...\n")
    for i, sorgu in enumerate(sorgular, 1):
        print(f"[{i}/{len(sorgular)}] Aranıyor: {sorgu}")
        try:
            response = client.search(query=sorgu)
            for result in response["results"]:
                url = result["url"]
                if url not in bulunanlar:
                    bulunanlar[url] = {
                        "baslik": result["title"],
                        "link": url,
                        "kaynak_sorgu": sorgu,
                        "bulunma_tarihi": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
        except Exception as e:
            print(f"  Hata: {e}")

try:
    with open("firsatlar.json", "r", encoding="utf-8") as f:
        mevcut_liste = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    mevcut_liste = []

mevcut_dict = {}
for kayit in mevcut_liste:
    link = kayit.get("link")
    if not link:
        continue
    for alan in EXTRACTION_FIELDS:
        kayit.setdefault(alan, None)
    kayit.setdefault("extraction_durumu", "henuz_islenmedi")
    kayit.setdefault("extraction_tarihi", None)
    mevcut_dict[link] = kayit

yeni_sayisi = 0
for link, kayit in bulunanlar.items():
    if link not in mevcut_dict:
        for alan in EXTRACTION_FIELDS:
            kayit.setdefault(alan, None)
        kayit["extraction_durumu"] = "henuz_islenmedi"
        kayit["extraction_tarihi"] = None
        mevcut_dict[link] = kayit
        yeni_sayisi += 1

print(f"\nBu turda {len(bulunanlar)} link tarandi, {yeni_sayisi} tanesi yeni. Toplam kayit sayisi (birikmis): {len(mevcut_dict)}")

islenecekler = [k for k in mevcut_dict.values() if k.get("extraction_durumu") == "henuz_islenmedi"]
if TEST_LIMIT is not None:
    islenecekler = islenecekler[:TEST_LIMIT]

print(f"Extraction calistirilacak kayit sayisi: {len(islenecekler)} (TEST_LIMIT={TEST_LIMIT})\n")

toplam_in_token, toplam_out_token = 0, 0
basarili_sayisi, basarisiz_sayisi, atlandi_sayisi = 0, 0, 0

for idx, kayit in enumerate(islenecekler):
    print(f"[{idx + 1}/{len(islenecekler)}] {kayit.get('baslik', '')[:70]}")
    sonuc = extract_tek_kayit(client, kayit)
    durum = kayit.get("extraction_durumu")
    if durum == "basarili":
        basarili_sayisi += 1
    elif durum == "basarisiz":
        basarisiz_sayisi += 1
    elif durum == "atlandi_genel_sayfa":
        atlandi_sayisi += 1
    if sonuc:
        toplam_in_token += sonuc["input_tokens"]
        toplam_out_token += sonuc["output_tokens"]
    json.dump(list(mevcut_dict.values()), open("firsatlar.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    if durum != "atlandi_genel_sayfa" and idx < len(islenecekler) - 1:
        _time.sleep(GEMINI_MIN_INTERVAL)

_dup_sayisi, _dup_gruplari = tekillestir(list(mevcut_dict.values()))
if _dup_sayisi:
    print(f"\nTekillestirme: {len(_dup_gruplari)} grup, toplam {_dup_sayisi} kayit duplicate olarak isaretlendi.")

with open("firsatlar.json", "w", encoding="utf-8") as f:
    json.dump(list(mevcut_dict.values()), f, ensure_ascii=False, indent=2)

print(f"\nToplam {len(mevcut_dict)} benzersiz firsat firsatlar.json dosyasina kaydedildi.")
print(f"Extraction ozeti: basarili={basarili_sayisi}, basarisiz={basarisiz_sayisi}, atlandi_genel_sayfa={atlandi_sayisi}")
print(f"Toplam Gemini token: input={toplam_in_token}, output={toplam_out_token}")
