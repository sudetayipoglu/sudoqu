from tavily import TavilyClient
from dotenv import load_dotenv
import os
import json
from datetime import datetime

load_dotenv()
from secret_helper import get_secret_or_env
import db as _db
api_key = get_secret_or_env("tavily-api-key", "TAVILY_API_KEY")
client = TavilyClient(api_key=api_key)

# --- Coklu Tavily API key rotasyonu (kredi tukenince siradaki key'e gecer, dairesel) ---
from tavily.errors import UsageLimitExceededError
from ulke_dil_sorgulari import ULKE_BILGI, DIL_SORGULARI

TAVILY_ANAHTAR_TANIMLARI = [
    ("tavily-api-key", "TAVILY_API_KEY"), ("tavily-api-key-2", "TAVILY_API_KEY_2"),
    ("tavily-api-key-3", "TAVILY_API_KEY_3"), ("tavily-api-key-4", "TAVILY_API_KEY_4"),
    ("tavily-api-key-5", "TAVILY_API_KEY_5"), ("tavily-api-key-6", "TAVILY_API_KEY_6"),
    ("tavily-api-key-7", "TAVILY_API_KEY_7"), ("tavily-api-key-8", "TAVILY_API_KEY_8"),
    ("tavily-api-key-9", "TAVILY_API_KEY_9"),
]
TAVILY_ANAHTARLARI = []
for _secret_id, _env_var in TAVILY_ANAHTAR_TANIMLARI:
    try:
        _val = get_secret_or_env(_secret_id, _env_var)
    except Exception:
        _val = None
    if _val:
        TAVILY_ANAHTARLARI.append(_val)
if not TAVILY_ANAHTARLARI:
    TAVILY_ANAHTARLARI = [api_key]
print(f"[tavily] {len(TAVILY_ANAHTARLARI)} adet API key yuklendi (rotasyonlu).\n")

_ANAHTAR_DURUM_DOSYA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tavily_anahtar_durumu.json")

def _anahtar_durumu_oku():
    if os.path.exists(_ANAHTAR_DURUM_DOSYA):
        try:
            with open(_ANAHTAR_DURUM_DOSYA, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"aktif_key_index": 0, "ardisik_tam_tur_basarisiz": 0, "alarm_aktif": False, "alarm_mesaji": None, "alarm_tarihi": None}

def _anahtar_durumu_yaz(durum):
    with open(_ANAHTAR_DURUM_DOSYA, "w", encoding="utf-8") as f:
        json.dump(durum, f, ensure_ascii=False, indent=2)

_tavily_durum = _anahtar_durumu_oku()

def _rotasyonlu_arama(sorgu, **kwargs):
    global _tavily_durum
    n = len(TAVILY_ANAHTARLARI)
    baslangic = _tavily_durum.get("aktif_key_index", 0) % n
    for deneme in range(n):
        idx = (baslangic + deneme) % n
        try:
            gecici_client = TavilyClient(api_key=TAVILY_ANAHTARLARI[idx])
            sonuc = gecici_client.search(query=sorgu, **kwargs)
            if _tavily_durum.get("aktif_key_index") != idx or _tavily_durum.get("ardisik_tam_tur_basarisiz", 0) != 0 or _tavily_durum.get("alarm_aktif"):
                _tavily_durum["aktif_key_index"] = idx
                _tavily_durum["ardisik_tam_tur_basarisiz"] = 0
                _tavily_durum["alarm_aktif"] = False
                _tavily_durum["alarm_mesaji"] = None
                _anahtar_durumu_yaz(_tavily_durum)
            return sonuc
        except UsageLimitExceededError:
            print(f"   [tavily] key #{idx+1}/{n} kota/limit doldu, siradaki key deneniyor...")
            continue
    _tavily_durum["aktif_key_index"] = baslangic
    _tavily_durum["ardisik_tam_tur_basarisiz"] = _tavily_durum.get("ardisik_tam_tur_basarisiz", 0) + 1
    if _tavily_durum["ardisik_tam_tur_basarisiz"] >= 2 and not _tavily_durum.get("alarm_aktif"):
        _tavily_durum["alarm_aktif"] = True
        _tavily_durum["alarm_mesaji"] = f"Tum Tavily API key'leri ({n} adet) art arda {_tavily_durum['ardisik_tam_tur_basarisiz']} tam tur boyunca kota/limit asimina ugradi."
        _tavily_durum["alarm_tarihi"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    _anahtar_durumu_yaz(_tavily_durum)
    raise UsageLimitExceededError(f"Tum {n} Tavily key de kota/limit asimina ugradi (sorgu: {sorgu})")


# --- V1.3: Tavily Extract + Gemini yapisal veri cikarim pipeline'i (pilot testte dogrulandi) ---
import time as _time
from urllib.parse import urlparse
from typing import Optional, Literal
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


# ============================================================
# EFOR/KAZANC ORANI - kural bazli, LLM kullanilmaz
# istenen_materyal alanindaki anahtar kelimelere gore dusuk/orta/yuksek
# etiketi hesaplar. Bilgi yoksa None doner (frontend'de "Bilgi yok").
# ============================================================
_EFOR_YUKSEK_KELIMELER = [
    "video", "prototip", "prototype", "demo", "poster", "maket",
    "bildiri", "tam metin", "sunum", "portfoy", "portföy", "portfolyo",
    "ornek proje", "örnek proje", "numune", "is plani", "iş planı", "fizibilite",
]
_EFOR_ORTA_KELIMELER = [
    "form", "ozgecmis", "özgeçmiş", "cv", "motivasyon mektubu",
    "referans mektubu", "proje ozeti", "proje özeti", "oneri", "öneri",
    "plan", "basvuru formu", "başvuru formu",
]


def efor_kazanc_hesapla(istenen_materyal):
    if not istenen_materyal:
        return None
    s = istenen_materyal.lower()
    if any(k in s for k in _EFOR_YUKSEK_KELIMELER):
        return "yuksek"
    if any(k in s for k in _EFOR_ORTA_KELIMELER):
        return "orta"
    return "dusuk"
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
    konu_kategori: Optional[Literal["sağlık", "finans", "sürdürülebilirlik", "yeşil teknoloji", "afet", "emlak", "eğitim", "yapay zeka", "diğer"]] = None
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
    etkinlik_turu: Optional[Literal["hackathon", "datathon", "ideathon", "hibe"]] = None
    format_turu: Optional[Literal["yüzyüze", "online", "hibrit"]] = None
    ulke: Optional[str] = None
    cok_programli_liste_sayfasi: Optional[bool] = None


EXTRACTION_FIELDS = list(OpportunityExtract.model_fields.keys())


def is_root_page(url):
    try:
        path = urlparse(url).path.strip("/")
        return path == ""
    except Exception:
        return False


def call_tavily_extract(tavily_client, url):
    # NOT: tavily_client parametresi geriye-donuk uyumluluk icin duruyor ama
    # kullanilmiyor - asagida TAVILY_ANAHTARLARI uzerinden gercek rotasyon yapiliyor
    # (eskiden burada tek/sabit client kullaniliyordu, kota dolunca diger 6 key'e hic gecilmiyordu).
    global _tavily_durum
    n = len(TAVILY_ANAHTARLARI)
    baslangic = _tavily_durum.get("aktif_key_index", 0) % n
    for deneme in range(n):
        idx = (baslangic + deneme) % n
        try:
            gecici_client = TavilyClient(api_key=TAVILY_ANAHTARLARI[idx])
            result = gecici_client.extract(urls=[url], extract_depth="advanced", chunks_per_source=3)
            results = result.get("results", [])
            failed = result.get("failed_results", [])
            if _tavily_durum.get("aktif_key_index") != idx:
                _tavily_durum["aktif_key_index"] = idx
                _anahtar_durumu_yaz(_tavily_durum)
            if results:
                raw = results[0].get("raw_content") or ""
                return {"success": True, "raw_content": raw, "char_count": len(raw), "error": None, "kota_hatasi": False}
            err = failed[0].get("error") if failed else "bilinmeyen hata (bos sonuc)"
            return {"success": False, "raw_content": "", "char_count": 0, "error": err, "kota_hatasi": False}
        except UsageLimitExceededError:
            print(f"  [tavily-extract] key #{idx+1}/{n} kota/limit doldu, siradaki key deneniyor...")
            continue
        except Exception as e:
            return {"success": False, "raw_content": "", "char_count": 0, "error": str(e), "kota_hatasi": False}
    return {"success": False, "raw_content": "", "char_count": 0, "error": f"Tum {n} Tavily key de kota/limit asimina ugradi", "kota_hatasi": True}


def call_gemini_extract(url, raw_content):
    prompt = f"""Asagida bir web sayfasindan/PDF'ten Tavily ile cikarilmis ham metin var.
Bu metinden bir yarisma / hackathon / burs / fuar / program firsatina dair
yapilandirilmis bilgiyi asagidaki semaya gore cikar.

COK ONEMLI KURALLAR:
1. Bu bilgiyi metinde acikca bulamiyorsan o alani null birak. ASLA UYDURMA, tahmin etme, varsayma. Sadece metinde gecen bilgiyi kullan.
2. Kaynak metin hangi dilde olursa olsun, TUM cikti alanlarini TURKCEYE CEVIREREK yaz.
3. Tarihleri HER ZAMAN YYYY-MM-DD formatina normalize et (tahmin edilebiliyorsa), yoksa null birak.
4. onemli_tarihler alanina birden fazla tarih varsa (basvuru baslangici, on eleme, final gibi), hepsini TEK BIR serbest metin string'i icinde, virgul veya noktayla ayirarak yaz - ASLA liste/array dondurme, her zaman tek bir string olmali.
5. Bu sayfa TEK BIR spesifik firsati (yarisma/hackathon/burs/fuar/hibe/program) degil de, BIRDEN FAZLA farkli firsati/programi bir arada listeleyen bir GENEL LISTE/INDEX/PORTAL/HABER sayfasiysa (ornek: bir etkinlik takvimi, cok sayida farkli hibe/burs/yarismayi tek sayfada siralayan bir portal, bir haber/blog anasayfasi), cok_programli_liste_sayfasi alanini true yap. Sayfa TEK bir spesifik firsati anlatiyorsa - kendi ozel alan adinda (domain) barindirilan, o firsata ozel bir mikro-site/tanitim sayfasi olsa bile - bu alani false yap. Karar SADECE sayfanin URL yapisina degil, icerdigi METNE bakarak verilmeli.
6. konu_kategori alanini SADECE su sabit listeden sec (baska deger UYDURMA): saglik, finans, surdurulebilirlik, yesil teknoloji, afet, emlak, egitim, yapay zeka, diger. Hicbiri tam uymuyorsa "diger" yaz. Bu alan bir KONU/ALAN sinifidir, etkinlik formatini degil icerigin ait oldugu alani belirtir.
7. etkinlik_turu alanini SADECE firsat acikca su turlerden biriyse doldur: hackathon, datathon, ideathon, hibe. Bunlarin disinda bir sey ise (ornek: burs, yarisma, konferans, sertifika programi, staj) bu alani null birak - zorla bu 4 secenekten birini secme.
8. format_turu alanini metinde acikca belirtilen bilgiye gore doldur: "yuzyuze" (fiziksel/yerinde katilim), "online" (tamamen internet uzerinden), "hibrit" (hem yuzyuze hem online secenek var). Metinde net bilgi yoksa null birak, tahmin/uydurma yapma.
9. ulke alanini MUTLAKA doldur: firsatin hangi ulke/ulkelere yonelik oldugunu Turkce ulke adiyla yaz (orn: "Turkiye", "Almanya"). Firsat belirli bir ulkeyle sinirli degilse, uluslararasi/global ise "Global" yaz. Metinden anlasilamiyorsa bile en olasi degeri tahmin etmek yerine "Global" yaz - bu alan asla bos kalmamali.

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
    return {"success": False, "parsed": None, "input_tokens": 0, "output_tokens": 0, "error": last_err, "kota_doldu": gecici_hata}


def bos_extraction_alanlari():
    return {alan: None for alan in EXTRACTION_FIELDS}


def extract_tek_kayit(tavily_client, kayit):
    """Tek bir firsat kaydi icin extraction calistirir, kaydi yerinde gunceller."""
    url = kayit.get("link", "")
    simdi = datetime.now().isoformat(timespec="seconds")

    tav = call_tavily_extract(tavily_client, url)
    if not tav["success"]:
        if tav.get("kota_hatasi"):
            # Tum Tavily key'leri o an icin kota/limit asimina ugradi. Bu GERCEK bir
            # extraction basarisizligi degil (Gemini kota_doldu mantigiyla ayni prensip).
            # Kaydi "basarisiz" olarak damgalamiyoruz; "henuz_islenmedi" durumunda
            # birakiyoruz ki kota acilinca/bir sonraki calismada tekrar densin.
            print(f"  [tavily kota/gecici hata - henuz_islenmedi olarak birakildi] {tav['error'][:100]} - {url}")
            return {"input_tokens": 0, "output_tokens": 0, "kota_doldu": True}
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
        parsed = gem["parsed"] or {}
        for alan in EXTRACTION_FIELDS:
            kayit[alan] = parsed.get(alan)
        if parsed.get("cok_programli_liste_sayfasi"):
            kayit.update(bos_extraction_alanlari())
            kayit["extraction_durumu"] = "atlandi_genel_sayfa"
            kayit["extraction_tarihi"] = simdi
            print(f"   [atlandi_genel_sayfa - icerik analizi] in={gem['input_tokens']} out={gem['output_tokens']} - {url}")
        else:
            kayit["extraction_durumu"] = "basarili"
            kayit["extraction_tarihi"] = simdi
            print(f"   [basarili] in={gem['input_tokens']} out={gem['output_tokens']} - {url}")
        return {"input_tokens": gem["input_tokens"] or 0, "output_tokens": gem["output_tokens"] or 0}

    if gem.get("kota_doldu"):
        # Kalici/gecici kota hatasi (429/503) - retry'lar tukendi ama bu GERCEK bir
        # extraction basarisizligi degil. Kaydi "basarisiz" olarak damgalamiyoruz,
        # "henuz_islenmedi" durumunda birakiyoruz ki bir sonraki calisma tekrar denesin.
        print(f"   [kota/gecici hata - henuz_islenmedi olarak birakildi] {gem['error'][:100]} - {url}")
        return {"input_tokens": 0, "output_tokens": 0, "kota_doldu": True}
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

kurum_tipi_en = [
    "government innovation challenge", "university student challenge",
    "defense ministry technology challenge", "space agency challenge",
    "corporate sponsored hackathon", "public sector innovation grant",
    "research institute open call", "EU funded innovation call",
]
for kelime in kurum_tipi_en:
    sorgular.append(f"{kelime} {yil} application")

EN_TEMEL_SORGULAR = [f"{k} {yil} application" for k in (genel_kategoriler["en"] + loanword_latin + programlar_en + kurum_tipi_en)]

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


if __name__ == "__main__":
    SKIP_SEARCH = os.getenv("RADAR_SKIP_SEARCH", "0") == "1"
    if SKIP_SEARCH:
        print("RADAR_SKIP_SEARCH=1: yeni arama atlaniyor, sadece mevcut henuz_islenmedi kayitlar icin extraction calisacak.\n")
    else:
        print(f"Toplam {len(sorgular)} sorgu ile tarama başlıyor...\n")
        son_arama_dosyasi = os.path.join(os.path.dirname(os.path.abspath(__file__)), "son_arama_durumu.json")
        son_arama_tarihi = None
        if os.path.exists(son_arama_dosyasi):
            try:
                with open(son_arama_dosyasi, "r", encoding="utf-8") as _sf:
                    son_arama_tarihi = json.load(_sf).get("son_arama_tarihi")
            except Exception:
                son_arama_tarihi = None
        if son_arama_tarihi:
            print(f"Onceki basarili arama tarihi: {son_arama_tarihi} - Tavily aramalari bu tarihten itibaren filtrelenecek (start_date).\n")
        else:
            print("Onceki arama tarihi kaydi bulunamadi (ilk calisma) - tam kapsamli arama yapiliyor.\n")
        for i, sorgu in enumerate(sorgular, 1):
            print(f"[{i}/{len(sorgular)}] Aranıyor: {sorgu}")
            try:
                if son_arama_tarihi:
                    response = _rotasyonlu_arama(sorgu, start_date=son_arama_tarihi, max_results=20)
                else:
                    response = _rotasyonlu_arama(sorgu, max_results=20)
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

    if not SKIP_SEARCH:
        _son_arama_dosyasi = os.path.join(os.path.dirname(os.path.abspath(__file__)), "son_arama_durumu.json")
        _yeni_tarih = datetime.now().strftime("%Y-%m-%d")
        with open(_son_arama_dosyasi, "w", encoding="utf-8") as _sf:
            json.dump({"son_arama_tarihi": _yeni_tarih}, _sf)

    if not SKIP_SEARCH:
        _ULKE_DURUM_DOSYA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ulke_taramasi_durumu.json")
        _ulke_son_tarih = None
        if os.path.exists(_ULKE_DURUM_DOSYA):
            try:
                with open(_ULKE_DURUM_DOSYA, "r", encoding="utf-8") as _uf:
                    _ulke_son_tarih = json.load(_uf).get("son_tarama_tarihi")
            except Exception:
                _ulke_son_tarih = None

        _ulke_taramasi_gerekli = True
        if _ulke_son_tarih:
            try:
                _gecen_gun = (datetime.now() - datetime.strptime(_ulke_son_tarih, "%Y-%m-%d")).days
                _ulke_taramasi_gerekli = _gecen_gun >= 10
            except Exception:
                _ulke_taramasi_gerekli = True

        if _ulke_taramasi_gerekli:
            _ulke_sorgu_listesi = []
            for _ulke_adi, (_dil, _country_param) in ULKE_BILGI.items():
                if _ulke_adi == "turkiye":
                    continue
                for _q in EN_TEMEL_SORGULAR:
                    _ulke_sorgu_listesi.append((_q, _country_param))
                if _dil != "en" and _dil in DIL_SORGULARI:
                    for _q in DIL_SORGULARI[_dil]:
                        _ulke_sorgu_listesi.append((_q, _country_param))

            print(f"\nUlke taramasi basliyor ({len(_ulke_sorgu_listesi)} sorgu, ~10 gunde bir calisir)...\n")
            for _ui, (_usorgu, _ucountry) in enumerate(_ulke_sorgu_listesi, 1):
                print(f"[ulke {_ui}/{len(_ulke_sorgu_listesi)}] ({_ucountry}) Araniyor: {_usorgu}")
                try:
                    _ukwargs = {"max_results": 20, "country": _ucountry}
                    if son_arama_tarihi:
                        _ukwargs["start_date"] = son_arama_tarihi
                    _uresponse = _rotasyonlu_arama(_usorgu, **_ukwargs)
                    for _uresult in _uresponse["results"]:
                        _uurl = _uresult["url"]
                        if _uurl not in bulunanlar:
                            bulunanlar[_uurl] = {
                                "baslik": _uresult["title"],
                                "link": _uurl,
                                "kaynak_sorgu": f"{_usorgu} [country={_ucountry}]",
                                "bulunma_tarihi": datetime.now().strftime("%Y-%m-%d %H:%M")
                            }
                except Exception as _ue:
                    print(f"   Hata: {_ue}")

            with open(_ULKE_DURUM_DOSYA, "w", encoding="utf-8") as _uf:
                json.dump({"son_tarama_tarihi": datetime.now().strftime("%Y-%m-%d")}, _uf)
            print(f"Ulke taramasi tamamlandi, sonraki tarama ~10 gun sonra.\n")

            if _db.DATABASE_URL:
                _db.save_firsatlar(list(bulunanlar.values()))
            else:
                json.dump(list(bulunanlar.values()), open("firsatlar.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        else:
            print(f"Ulke taramasi atlandi - son tarama {_ulke_son_tarih}, henuz 10 gun gecmedi.\n")

        print(f"Son basarili arama tarihi guncellendi: {_yeni_tarih}\n")

    if _db.DATABASE_URL:
        mevcut_liste = _db.load_firsatlar()
    else:
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
        if _db.DATABASE_URL:
            _db.save_firsatlar(list(mevcut_dict.values()))
        else:
            json.dump(list(mevcut_dict.values()), open("firsatlar.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        if sonuc and sonuc.get("kota_doldu"):
            kalan = len(islenecekler) - idx - 1
            print(f"\nGunluk Gemini kotasi ya da Tavily kredisi dolmus gorunuyor - kalan {kalan} kayit henuz_islenmedi olarak birakilip bir sonraki calismaya birakiliyor.")
            break
        if durum != "atlandi_genel_sayfa" and idx < len(islenecekler) - 1:
            _time.sleep(GEMINI_MIN_INTERVAL)

    for _kayit in mevcut_dict.values():
        _kayit["efor_kazanc_seviyesi"] = efor_kazanc_hesapla(_kayit.get("istenen_materyal"))

    _dup_sayisi, _dup_gruplari = tekillestir(list(mevcut_dict.values()))
    if _dup_sayisi:
        print(f"\nTekillestirme: {len(_dup_gruplari)} grup, toplam {_dup_sayisi} kayit duplicate olarak isaretlendi.")

    if _db.DATABASE_URL:
        _db.save_firsatlar(list(mevcut_dict.values()))
    else:
        with open("firsatlar.json", "w", encoding="utf-8") as f:
            json.dump(list(mevcut_dict.values()), f, ensure_ascii=False, indent=2)

    print(f"\nToplam {len(mevcut_dict)} benzersiz firsat firsatlar.json dosyasina kaydedildi.")
    print(f"Extraction ozeti: basarili={basarili_sayisi}, basarisiz={basarisiz_sayisi}, atlandi_genel_sayfa={atlandi_sayisi}")
    print(f"Toplam Gemini token: input={toplam_in_token}, output={toplam_out_token}")
