# Ekosistem Yonetim Platformu - Urun Dokumantasyonu
**Calisma adi:** [Proje Adi Belirlenecek]
**Versiyon:** Dokuman v2 - Taslak
**Durum:** Fikir olgunlastirma tamamlandi, kademeli MVP plani netlesti, mimari saglamlastirma (derin analiz) asamasina gecilmedi

---

## 1. Proje Ozeti

3 kisilik muhendis bir ekip icin, ideathon/datathon/hackathon/teknoloji fuari/etkinlik/kongre/calistay/yarisma gibi firsatlari **otomatik kesfeden**, bu firsatlara gore **basvuru stratejisi ureten** ve ekibin **proje-gorev-takvim operasyonunu** tek catir altinda yoneten bir platform.

Iki ayri problemi tek sistemde birlestiriyor:
1. **Kesif problemi:** Firsatlari manuel arayip takip etmek zorlasmis durumda.
2. **Operasyon problemi:** Her firsat ayri bir "proje" aciyor, her projede 3 kisiye gorev dagitmak, takvim/dokuman tutmak gerekiyor.

## 2. Problem Tanimi

* Yarisma/hackathon/fuar duyurulari daginik kaynaklarda yayiliyor (kurum siteleri, sosyal medya, universite duyurulari) - merkezi bir kaynak yok.
* Ekip birden fazla projeyle ayni anda farkli programlara basvurabiliyor, bu da gorev dagilimini ve takibi karmasiklastiriyor.
* Hangi firsata hangi projeyle girilmesi gerektigi karari su an sezgisel - gecmis kazanan veriyle desteklenmiyor.

## 3. Hedef Kullanici

* **Kim:** 3 kisilik muhendis girisimci ekip, kendi urunlerini/projelerini gelistirip yarisma ve hackathon ekosistemi uzerinden gorunurluk, odul, yatirim ve fon arayan bir yapi.
* **Bugun nasil cozuyorlar:** Manuel arama + daginik takip (muhtemelen not defteri / mesajlasma grubu seviyesinde).
* **Neden simdi:** Katildiklari yarisma sayisi artikca manuel takip artik olceklenmiyor; bu darbogaz buyumelerini frenliyor.

## 4. Deger Onerisi

Rakiplerden ayiran asil fark: sistem sadece "firsat listesi" sunmuyor, **her firsat icin gecmis kazananlarla kiyaslanmis, projenizle uyum skorlanmis, somut bir basvuru stratejisi** uretiyor. Bu, klasik bir etkinlik takip sitesinde ya da genel bir proje yonetim araciнda (Notion/Trello) bulunmayan bir katman. Bu katman V1.5'te devreye girecek - sistem once temel iskeletiyle ayakta durup calistigini kanitlayacak, sonra bu farklilastirici katman eklenecek.

## 5. Kademeli Yapim Mantigi (Neden Bu Sirayla?)

Sifir teknik bilgiyle baslanan bir projede her seyi tek seferde kurmaya calismak sureci patlatir. Bu yuzden V1, olabildigince **ince bir dilim** olarak tanimlandi: yalnizca "firsati bul, goster, takip et, haber ver" dongusu calisir hale gelir. Her sey dogrulandiktan sonra sirayla ustune katman eklenir (V1.1 -> V1.5). Bu siralamanin mantigi basit: **her adim bir oncekinin ustune kurulur**, hicbiri digerini beklemeden baslamaz.

## 6. Surum Yol Haritasi (V1 -> V2)

### V1 - Cekirdek Iskelet (TAMAMLANDI)
* Firsat kesif motoru (radar.py): Tavily arama ile periyodik tarama, firsatlari yapilandirilmis JSON'a yazma.
* Firsatlar listeleme arayuzu: arama, filtreleme, siralama.
* Basvurularim sekmesi: takip edilen firsatlarin durumu.
* Zamanlanmis calisma (cron / systemd timer): haftalik otomatik tarama.

### V1.1 - Veri Alani Genisletme (TAMAMLANDI)
* Her firsat icin 13 alanlik detay paneli (baslik, link, kurum, tarih, konu, odul, katilim sekli, vb.) - kullaniciya firsat hakkinda tek bakista yeterli baglam vermek icin.

### V1.2 - Ekip Operasyon Katmani (TAMAMLANDI)
* Task & Takvim sekmesi: gorev listeleme, tamamlanma isaretleme.
* Ekip uyeleri (ekip.json) tanimlama.

### V1.3 - Coklama Onleme (TAMAMLANDI)
* Ayni firsatin birden fazla taramada tekrar tekrar listeye girmesini engelleyen link-bazli tekillestirme.

### V1.4 - Proje Modulu (TAMAMLANDI - item 8)
* Projelerimiz sekmesi: proje olusturma, duzenleme, not ve dosya ekleme.
* Her proje, ekibin hangi firsatlara hangi urunle basvurdugunu izlemesini saglar.

### V1.5 - sudola: Akilli Basvuru Asistani (TAMAMLANDI - item 9)
* Firsat bazinda sohbet arayuzu (sudola-panel.tsx): kullanici serbest metin soru sorabilir, Tavily ile zenginlestirilmis, Gemini ile uretilmis yanit alir.
* "Proje Uygunluk Onerisi": secili firsat ile ekibin projeleri arasindaki uyumu 0-100 skorla, guclu yonler ve riskler listesiyle degerlendiren yapilandirilmis LLM cikti.
* Bu katman, Bolum 4'te tanimlanan asil deger onerisini (rakiplerden ayiran fark) hayata gecirir.

### V2 Kapsami (PLANLANMADI - fikir asamasinda)
* Gecmis kazananlarla otomatik kiyaslama: sadece mevcut firsati degil, gecmis yillarin kazanan projelerini de tarayip skorlamaya dahil etme.
* Sosyal medya bazli kesif (iki asamali plan - bkz. Bolum 8, Acik Sorular).
* Cok kullanicili / rol bazli erisim (su an ekip.json duz liste, yetkilendirme yok).
* PostgreSQL migrasyonu (bkz. Bolum 8 - en yuksek oncelikli teknik borc).
* Bildirim sistemi (e-posta / push - yeni firsat bulundugunda ekibe otomatik haber verme).

## 7. Teknik Karar Kayitlari

| Karar | Gerekce |
|---|---|
| Next.js 14.2.35'e sabitlenmesi | Surum atlamalarinin (ozellikle App Router / Pages Router gecisleri) build kararliligini bozma riski nedeniyle bilincli olarak sabitlendi; ilerleyen bir asamada kontrollu bir surum yukseltmesi ayri bir gorev olarak degerlendirilebilir. |
| LLM model secimi: gemini-flash-lite-latest (gemini-3.1-flash-lite) | Ucretsiz katmanda gunluk 500 istek kotasi, sudola'nin sohbet + oneri kullanim hacmine yeterli; maliyetsiz baslangic icin uygun. Kota asimi acik biciminde ele alinip kullaniciya 429 olarak yansitiliyor. |
| Tavily arastirma + Gemini yapilandirilmis cikti kombinasyonu | Tavily guncel web baglami saglar, Gemini bu baglami yapilandirilmis (response_schema) bir JSON'a donusturur - halusinasyon riski dusurulur, cikti dogrudan arayuzde render edilebilir hale gelir. |
| radar.py veri kalicilik duzeltmesi | Erken surumde tarama sonuclari bazi durumlarda kalici JSON dosyasina yazilmadan kayboluyordu; dosya_oku/dosya_yaz yardimcilariyla standartlastirilarak duzeltildi. |
| JSON dosya tabanli veri katmani (PostgreSQL DEGIL) | V1 hizli baslangic icin bilincli olarak secildi - dogrulama asamasinda veritabani kurulum yukune girmeden urunun calisip calismadigi test edildi. Veri hacmi ve concurrent yazma ihtiyaci arttikca bu secim risk haline geliyor (bkz. Bolum 8). |
| Secret yonetimi: Google Secret Manager + .env fallback (secret_helper.py) | Prod ortaminda Secret Manager tercih edilir; VM'nin IAM kisitlari nedeniyle su an fiilen .env'e dusuyor, ama kod hem bulut-native hem yerel gelistirme senaryosunu tek noktadan destekliyor. |

## 8. Acik Sorular / Riskler

* **[KRITIK - EN YUKSEK ONCELIK] JSON -> PostgreSQL migrasyonu:** Su anki veri katmani duz JSON dosyalari (firsatlar.json, basvurular.json, projeler.json, ekip.json, tasklar.json). Bu, dogrulama asamasi icin dogru bir secimdi ama concurrent yazma (ayni anda birden fazla istek ayni dosyaya yazmaya calisirsa veri kaybi/bozulma riski), olceklenebilirlik ve sorgu performansi acisindan bir sonraki oturumun en yuksek oncelikli teknik gorevi olarak isaretlendi.
* **Icerik bazli coklama tespiti eksigi:** Su anki tekillestirme sadece link esitligine dayaniyor (V1.3). Ayni firsat farkli URL'lerle (ör. kisaltilmis link, mobil versiyon, izleme parametreli link) tekrar girerse yakalanamiyor. Icerik/baslik benzerligine dayali daha guclu bir coklama tespiti gelecekte degerlendirilmeli.
* **Sosyal medya bazli kesif - iki asamali plan (fikir, uygulanmadi):**
  1. Asama: Hedef kurum/organizasyon hesaplarinin (Instagram, X/Twitter, LinkedIn) genel/herkese acik gonderilerini periyodik tarama.
  2. Asama: Bu gonderilerden yapilandirilmis firsat verisi (tarih, konu, son basvuru) cikarmak icin bir LLM ayristirma katmani.
  Bu plan henuz hicbir kod calismasi baslatilmadi; API erisim kisitlari (rate limit, ToS) onceden arastirilmali.
* **Frontend production-build gecisi notu:** Gelistirme sirasinda frontend `next dev` modunda calistirilabiliyor ama production'da `next start` icin ONCESINDE eksiksiz bir `next build` sarttir (build dizininde app/ yaninda pages/ altindaki _app.js/_document.js/_error.js gibi yerlesik shim dosyalarinin da olusmus olmasi gerekiyor). Bu adimin atlanmasi veya yarim kalmasi dogrudan urun-disi (0 kayit, sonsuz yukleniyor, stilsiz sayfa) bir cokme senaryosuna yol aciyor - bu tam olarak Asama -1'de yasanan ve duzeltilen sorundur.
* **Gemini gunluk kota siniri:** 500 istek/gun (ucretsiz katman), yaklasik ABD Pasifik gece yarisinda sifirlaniyor. Ekip buyudukce veya kullanim arttikca ucretli katmana gecis degerlendirilmeli.

## 9. Sonraki Adim

Bir sonraki oturumda oncelik sirasi: (1) PostgreSQL migrasyonu, (2) icerik-bazli coklama tespiti iyilestirmesi, (3) sosyal medya kesif planinin arastirma/fizibilite asamasi. Bu dokuman ve ORTAM_REHBERI.md, her yeni oturumun baslangicinda referans alinmasi gereken canonical kaynaklardir.
