from tavily import TavilyClient
from dotenv import load_dotenv
import os
import json
from datetime import datetime

load_dotenv()
api_key = os.getenv("TAVILY_API_KEY")
client = TavilyClient(api_key=api_key)

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

print(f"Toplam {len(sorgular)} sorgu ile tarama başlıyor...\n")

bulunanlar = {}

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

with open("firsatlar.json", "w", encoding="utf-8") as f:
    json.dump(list(bulunanlar.values()), f, ensure_ascii=False, indent=2)

print(f"\nToplam {len(bulunanlar)} benzersiz fırsat bulundu ve firsatlar.json dosyasına kaydedildi.")
