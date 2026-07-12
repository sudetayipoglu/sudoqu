# Pilot Test Sonuclari: Tavily Extract + Gemini Yapisal Veri Cikarimi

Tarih: 2026-07-12 15:47 UTC

Model: gemini-flash-latest

## Ozet

- Toplam link: 12
- Tavily basarili: 11
- Tavily basarisiz: 1
- Gemini basarili: 11
- Gemini basarisiz: 0
- Toplam Gemini input token: 45419
- Toplam Gemini output token: 3442


## Genel Degerlendirme

Not: Ilk denemede script'te "gemini-2.5-flash" modeli kullanilmisti, bu model artik yeni kullanicilara kapali oldugu icin (404 NOT_FOUND) API'den canli model listesi cekilip "gemini-flash-latest" olarak guncellendi ve script o modelle basariyla calisti.

Sonuclara gore:

- Universite ve devlet kurumu duyurulari (5/5) en yuksek kalitede sonuc verdi: tarihler, odul tutarlari, katilim sartlari net ve tutarli sekilde cikarildi, uydurma (halusinasyon) belirtisi gorulmedi.
- Yabanci dil kaynaklar (Cince, Japonca, Fransizca - 3/3) beklenenden cok daha iyi performans gosterdi; Gemini kaynak dilden bagimsiz olarak Turkce alanlar uretebildi, hatta ince detaylari (AI kullanim beyani, saat dilimi, coklu ulke sartlari) yakaladi.
- Instagram linkleri (2/2) calisti ama Tavily'nin cektigi icerik çok kisa oldugundan (post basina ~800-1300 karakter) sadece temel alanlar dolduruldu; bu kaynak turunden zengin veri beklenmemeli.
- PDF: Fransizca PDF (yabanci_dil_pdf_fr) mukemmel calisti; ancak secilen Turkce PDF linki (atonet.org.tr) 404 verdi - bu link rot'un gercek bir risk oldugunu gosteriyor, production pipeline'da basarisiz extract'lerin ele alinmasi (atlama/tekrar deneme/isaretleme) gerekecek.
- Genel organizasyon ana sayfasi (teknofest.org) sema ile en az uyumlu kaynak turu oldu: sayfa tek bir firsati degil onlarca yarismayi temsil ettigi icin bazi alanlar (istenen_materyal gibi) farkli etkinliklerden karisik bilgi icerdi. Bu tur genel/sirket ana sayfalarinin ozel bir mantikla (ornegin extraction'a hic sokulmamasi ya da ayri bir "genel sayfa" sema tipiyle isaretlenmesi) ele alinmasi onerilir.

### Maliyet

Bu pilotta 11 basarili Gemini cagrisinda toplam 45.419 input token + 3.442 output token harcandi (link basina ortalama ~4.129 input / ~313 output token). 442 linkli tam bir firsatlar.json seti icin orantili olarak kabaca 1.8 milyon input token ve ~140 bin output token beklenir (gemini-flash-latest ile). Kesin TL/USD maliyeti, hesabinizdaki guncel Gemini fiyatlandirma katmanina (ucretsiz/odemeli) bagli oldugundan Google AI Studio / Cloud Console faturalandirma sayfasindan teyit edilmesini oneririm - ucretsiz katmanda dakikada 5 istek siniri oldugu bu pilotta da gorulmustu (ilk denemede 429 hatasi), bu yuzden 442 link icin production'da ya odemeli katmana gecilmeli ya da istekler arasi bekleme suresi (bu pilotta 13sn kullanildi) ile yavaslatilmali.

Tavily tarafinda 12 istekten 11'i basarili oldu (1 tanesi kaynak sayfa 404 verdigi icin basarisiz, kredi harcamamis olmasi beklenir). "advanced" extract derinligi Tavily'nin kendi fiyatlandirmasina gore standart extract'ten daha fazla kredi tuketir; tam kredi tuketimini Tavily hesap panelinizden (Usage/Billing) teyit etmenizi oneririm.

## Link Bazinda Detaylar

### [universite] https://ajanda.ibu.edu.tr/teknofest-2026-teknoloji-yarismalari-basvurulari-uzatildi

**Tavily:** basarili=True, karakter_sayisi=65749

**Gemini:** input_token=8263, output_token=228

```json
{
  "organizator": "TEKNOFEST",
  "konu_kategori": "Havacılık, uzay, savunma, yapay zek, robotik, enerji, çevre",
  "son_basvuru_tarihi": "28 Şubat 2026",
  "onemli_tarihler": "Son başvuru tarihi: 28 Şubat 2026 (Önceki son başvuru tarihi: 20 Şubat)",
  "basvuru_asamalari": null,
  "yer_mekan": null,
  "konaklama_yol_destegi": null,
  "odul_miktari_turu": null,
  "katilim_sartlari": null,
  "takim_buyuklugu_limiti": null,
  "basvuru_maliyeti": null,
  "istenen_materyal": null,
  "sponsor_kurumlar": null
}
```

**Kalite degerlendirmesi:** Iyi sonuc. Organizator, kategori ve son basvuru tarihi (onceki tarihten guncellemeyle birlikte) dogru ve net bicimde cikarildi. Sayfada yer/odul/sart bilgisi yoktu, model bunlari uydurmadan null birakti - halusinasyon riski acisindan olumlu.

### [universite] https://www.karatay.edu.tr/tr/duyuru/2026/04/14/girisimcilik-maratonu-2026-basvurulari-basladi

**Tavily:** basarili=True, karakter_sayisi=5629

**Gemini:** input_token=2159, output_token=295

```json
{
  "organizator": "Düzce Üniversitesi ve Düzce Teknopark",
  "konu_kategori": "Girişimcilik",
  "son_basvuru_tarihi": "24 Nisan 2026",
  "onemli_tarihler": "Son İş Fikri Başvuru Tarihi: 24 Nisan 2026, Takımlara Katılmak için Son Başvuru Tarihi: 8 Mayıs 2026, Saat 16:00",
  "basvuru_asamalari": null,
  "yer_mekan": null,
  "konaklama_yol_destegi": null,
  "odul_miktari_turu": "Mentorluk desteği",
  "katilim_sartlari": "Yalnızca yeni iş fikri olan girişimci adayları katılabilir. MVP veya daha ileri aşamadaki projeler, başlangıç seviyesindeki girişimciler için fırsat eşitsizliği oluşturduğundan dolayı başvuru kapsamı dışındadır.",
  "takim_buyuklugu_limiti": null,
  "basvuru_maliyeti": null,
  "istenen_materyal": null,
  "sponsor_kurumlar": null
}
```

**Kalite degerlendirmesi:** Dikkat cekici bir durum: kaynak site KTO Karatay Universitesi olmasina ragmen model organizatoru dogru sekilde 'Duzce Universitesi ve Duzce Teknopark' olarak ayirt etti (domain adina degil, metindeki gercek bilgiye guvendi). Universite siteleri baska kurumlarin etkinliklerini duyurdugunda bu onemli bir dogru davranis.

### [universite] https://www.mehmetakif.edu.tr/content/12997/1/teknofest-girisim-programi-2026-basvurulari-basladi

**Tavily:** basarili=True, karakter_sayisi=12073

**Gemini:** input_token=5074, output_token=339

```json
{
  "organizator": "Türkiye Teknoloji Takımı Vakfı",
  "konu_kategori": "Girişimcilik, Teknoloji",
  "son_basvuru_tarihi": "27 Nisan 2026",
  "onemli_tarihler": "Son Başvuru Tarihi: 27 Nisan 2026, Final: 30 Eylül - 4 Ekim 2026",
  "basvuru_asamalari": null,
  "yer_mekan": "Şanlıurfa GAP Havalimanı (Final), İstanbul T3 Girişim Merkezleri (Ofis)",
  "konaklama_yol_destegi": null,
  "odul_miktari_turu": "Ön kuluçka sürecini tamamlayan ekiplere 100 bin TL’ye kadar malzeme desteği, şirketleşen girişimlere 500 bin TL yatırım fırsatı, hızlandırma aşamasını tamamlayan projelere 1 milyon TL’ye kadar yatırım desteği",
  "katilim_sartlari": "Özellikle TEKNOFEST teknoloji yarışmalarına katılan takım ve üyeler",
  "takim_buyuklugu_limiti": null,
  "basvuru_maliyeti": null,
  "istenen_materyal": null,
  "sponsor_kurumlar": "Burdur Mehmet Akif Ersoy Üniversitesi (Paydaş)"
}
```

**Kalite degerlendirmesi:** En zengin sonuclardan biri: organizator, iki farkli asama/yer bilgisi (Sanliurfa final + Istanbul ofis), uc kademeli odul/destek tutari (100 bin / 500 bin / 1 milyon TL) dogru ve tutarli cikarildi. Universite duyuru sayfalari TEKNOFEST baglaminda oldukca bilgi yogun, kalite yuksek.

### [devlet] https://bilimgenc.tubitak.gov.tr/makale/teknofest-2026-teknoloji-yarismalari-basvurulari-basladi

**Tavily:** basarili=True, karakter_sayisi=21620

**Gemini:** input_token=8376, output_token=346

```json
{
  "organizator": "Türkiye Teknoloji Takımı Vakfı (T3 Vakfı) ve T.C. Sanayi ve Teknoloji Bakanlığı",
  "konu_kategori": "Havacılık, uzay ve teknoloji (52 ana kategori ve 127 alt kategoride teknoloji yarışmaları)",
  "son_basvuru_tarihi": "20 Şubat 2026",
  "onemli_tarihler": "Başvuru son tarihi: 20 Şubat 2026, Festival tarihi: 30 Eylül – 4 Ekim 2026",
  "basvuru_asamalari": "teknofest.org adresi üzerinden çevrim içi başvuru",
  "yer_mekan": "Şanlıurfa GAP Havalimanı",
  "konaklama_yol_destegi": null,
  "odul_miktari_turu": "Toplam 75 milyon TL ödül ve 100 milyon TL’yi aşan maddi destek",
  "katilim_sartlari": "İlkokul, ortaokul, lise, ön lisans ve lisans, lisansüstü, mezun, girişim ve özel sektörden katılımcılar ile uluslararası katılıma açık",
  "takim_buyuklugu_limiti": null,
  "basvuru_maliyeti": null,
  "istenen_materyal": null,
  "sponsor_kurumlar": null
}
```

**Kalite degerlendirmesi:** TUBITAK kaynagi en detayli sonuclardan biri: iki ortak organizator, kategori sayilari (52 ana/127 alt kategori), toplam odul tutarlari (75M+100M TL), genis katilim sartlari - hepsi metinle tutarli, uydurma emaresi yok. Devlet kurumu duyurulari icin pipeline'in guclu oldugunu gosteriyor.

### [devlet] https://sgb.meb.gov.tr/www/2026-yili-ar-ge-bulusmalari-kapsaminda-quotgirisimcilik-ve-ogrenci-liderligi-calistayiquot-gerceklestirildi/icerik/821

**Tavily:** basarili=True, karakter_sayisi=3829

**Gemini:** input_token=1444, output_token=220

```json
{
  "organizator": "T.C. Millî Eğitim Bakanlığı Strateji Geliştirme Başkanlığı",
  "konu_kategori": "Girişimcilik ve Öğrenci Liderliği",
  "son_basvuru_tarihi": null,
  "onemli_tarihler": "Çalıştay Tarihi: 12 Şubat 2026 Perşembe",
  "basvuru_asamalari": null,
  "yer_mekan": "İstanbul Sabancı Öğretmenevi",
  "konaklama_yol_destegi": null,
  "odul_miktari_turu": null,
  "katilim_sartlari": null,
  "takim_buyuklugu_limiti": null,
  "basvuru_maliyeti": null,
  "istenen_materyal": null,
  "sponsor_kurumlar": null
}
```

**Kalite degerlendirmesi:** Bu sayfa bir basvuru duyurusu degil, gecmiste yapilmis bir calistayin haberiydi ('gerceklestirildi'). Model bunu dogru okudu: son_basvuru_tarihi ve cogu alani null birakti, sadece calistay tarihi ve yerini (Istanbul Sabanci Ogretmenevi) verdi. Metnin dogasini dogru yorumlayip uydurmamasi guven verici.

### [instagram] https://www.instagram.com/p/DTTNZByCpou

**Tavily:** basarili=True, karakter_sayisi=834

**Gemini:** input_token=473, output_token=154

```json
{
  "organizator": "T3 Vakfı",
  "konu_kategori": "Teknoloji Yarışmaları",
  "son_basvuru_tarihi": "20 Şubat 2026",
  "onemli_tarihler": "Son başvuru: 20 Şubat 2026",
  "basvuru_asamalari": null,
  "yer_mekan": null,
  "konaklama_yol_destegi": null,
  "odul_miktari_turu": null,
  "katilim_sartlari": null,
  "takim_buyuklugu_limiti": null,
  "basvuru_maliyeti": null,
  "istenen_materyal": null,
  "sponsor_kurumlar": null
}
```

**Kalite degerlendirmesi:** Tavily'nin cektigi icerik oldukca kisa (834 karakter, muhtemelen sadece caption). Buna ragmen organizator (T3 Vakfi), kategori ve son basvuru tarihi dogru cikarildi. Instagram gonderilerinden zengin bilgi beklenmemeli ama temel alanlar icin yeterli.

### [instagram] https://www.instagram.com/reel/DWgbOHujXyI?hl=en

**Tavily:** basarili=True, karakter_sayisi=1273

**Gemini:** input_token=645, output_token=188

```json
{
  "organizator": null,
  "konu_kategori": "Fuar (Teknoloji, Verimlilik, Dijital Dönüşüm, İnovasyon)",
  "son_basvuru_tarihi": null,
  "onemli_tarihler": "16–19 Nisan 2026",
  "basvuru_asamalari": "http://verimlilikveteknoloji.com adresini ziyaret ederek kayıt olmak ve dijital giriş kartı oluşturmak",
  "yer_mekan": "ATO Congresium",
  "konaklama_yol_destegi": null,
  "odul_miktari_turu": null,
  "katilim_sartlari": null,
  "takim_buyuklugu_limiti": null,
  "basvuru_maliyeti": "Girişler Ücretsizdir",
  "istenen_materyal": null,
  "sponsor_kurumlar": null
}
```

**Kalite degerlendirmesi:** Reel aciklamasindan fuar bilgisi (ATO Congresium, 16-19 Nisan 2026, ucretsiz giris, kayit linki) makul bicimde cikarildi. organizator alani null birakildi - muhtemelen caption'da net bir kurum adi gecmiyordu, dogru davranis.

### [pdf_tr] https://www.atonet.org.tr/Yuklemeler/kurumsal_iletisim_ve_basin_yayin_mudurlugu/TEKNOFEST%202026%20Yar%C4%B1%C5%9Fmalar%20Ba%C5%9Fvuru%20K%C4%B1lavuzu.pdf

**Tavily:** basarili=False, karakter_sayisi=0, hata=404 page not found

**Gemini:** calistirilmadi (Tavily basarisiz ya da icerik bos)

**Kalite degerlendirmesi:** Bu link artik 404 veriyor (kaynak PDF kaldirilmis/tasinmis). Bu, radar.py'nin topladigi linklerin zamanla curuyebilecegini (link rot) gosteren gercekci ve onemli bir bulgu - production entegrasyonunda basarisiz extract'lerin sessizce atlanmasi ya da isaretlenmesi gerekecek.

### [yabanci_dil_pdf_fr] https://www.ubacameroon.com/wp-content/uploads/sites/8/2026/01/LANCEMENT-DU-PROGRAMME-TEF-2026.pdf

**Tavily:** basarili=True, karakter_sayisi=7604

**Gemini:** input_token=1971, output_token=318

```json
{
  "organizator": "Tony Elumelu Foundation (TEF)",
  "konu_kategori": "Girişimcilik",
  "son_basvuru_tarihi": "1 Mart 2026",
  "onemli_tarihler": "Başvurular 1 Ocak - 1 Mart 2026 tarihleri arasında kabul edilmektedir.",
  "basvuru_asamalari": null,
  "yer_mekan": "Çevrimiçi (TEFConnect)",
  "konaklama_yol_destegi": null,
  "odul_miktari_turu": "5.000 ABD Doları geri ödemesiz tohum sermayesi, yoğun işletme eğitimi ve mentörlük",
  "katilim_sartlari": "54 Afrika ülkesinden hırslı genç girişimciler",
  "takim_buyuklugu_limiti": null,
  "basvuru_maliyeti": null,
  "istenen_materyal": null,
  "sponsor_kurumlar": "European Union (EU), United Nations Development Programme (UNDP), International Committee of the Red Cross (ICRC), US Government via United States African Development Foundation (USADF), Organisation of African, Caribbean and Pacific States (OACPS), French Development Agency (AFD), German Development Finance Institution (DEG), German Agency for International Cooperation (GIZ), African Development Bank (AfDB), Google, United Nations Children's Fund (UNICEF) Generation Unlimited (GenU), Khalifa Bin Zayed Al Nahyan Foundation (KBZF)"
}
```

**Kalite degerlendirmesi:** En guclu sonuclardan biri. Fransizca bir PDF'ten (Tony Elumelu Foundation) organizator, odul tutari (5.000 USD), katilim sarti (54 Afrika ulkesi) ve 12 farkli ortak kurumdan olusan sponsor listesi eksiksiz ve Turkceye cevrilerek cikarildi. Hem PDF hem yabanci dil destegini ayni anda kanitliyor.

### [yabanci_dil_zh] https://www.nsfc.gov.cn/p1/3381/2824/99667.html

**Tavily:** basarili=True, karakter_sayisi=8361

**Gemini:** input_token=5535, output_token=647

```json
{
  "organizator": "国家自然科学基金委员会 (Çin Ulusal Doğa Bilimleri Vakfı - NSFC)",
  "konu_kategori": "Bilimsel Araştırma Projeleri Fonu (Doğa Bilimleri)",
  "son_basvuru_tarihi": "2026-03-20 16:00",
  "onemli_tarihler": "15 Ocak 2026: Başvuru sisteminin açılması; 1 Mart 2026: Başvuru alımının başlaması; 20 Mart 2026 16:00: Başvuru alımının sona ermesi; 29 Nisan 2026 öncesi: İlk değerlendirme sonuçlarının açıklanması; 24 Şubat 2026 16:00 öncesi: Bağlı kurumların结题 (sonuçlandırma) materyallerini onaylaması.",
  "basvuru_asamalari": "1. 15 Ocak 2026 tarihinden sonra Bilim Vakfı Ağ Bilgi Sistemi'ne giriş yapılarak başvuru şablonunun indirilmesi ve doldurulması. 2. Başvurunun araştırma niteliğine göre 'Serbest Keşif' veya 'Hedef Odaklı' olarak sınıflandırılması. 3. Katılımcıların sisteme davet edilerek özgeçmişlerinin ve akademik yayınlarının (PDF formatında) yüklenmesi. 4. Başvurunun sistem üzerinden tamamen kağıtsız (dijital) olarak gönderilmesi. 5. Bağlı bulunan kurum tarafından onaylanıp nihai listenin teslim edilmesi.",
  "yer_mekan": "Çevrimiçi (科学基金网络信息系统 - Bilim Vakfı Ağ Bilgi Sistemi)",
  "konaklama_yol_destegi": null,
  "odul_miktari_turu": "Ulusal Doğa Bilimleri Vakfı Proje Fonu Desteği (Götürü usulü '包干制' veya bütçe usulü '预算制' finansman modeli)",
  "katilim_sartlari": "Mali destekli bilim ve teknoloji faaliyetlerinden kısıtlanmamış olmak, geçerli akademik unvanlara sahip olmak, yapay zeka tarafından doğrudan üretilen başvuru metinlerini kullanmamak ve kullanılan AI araçlarını beyan etmek.",
  "takim_buyuklugu_limiti": null,
  "basvuru_maliyeti": null,
  "istenen_materyal": "Elektronik başvuru formu, tavsiye/referans mektupları (gerekli hallerde), katılımcıların PDF formatındaki özgeçmişleri, temsilci akademik makalelerin tam metin PDF'leri, kitapların kapak, özet ve dizin taramaları.",
  "sponsor_kurumlar": "国家自然科学基金委员会 (Çin Ulusal Doğa Bilimleri Vakfı)"
}
```

**Kalite degerlendirmesi:** Cince kaynaktan alinan en detayli sonuc: cok asamali basvuru sureci, spesifik saat/tarih bilgileri, hatta 'yapay zeka araclarinin kullanimini beyan etme' gibi ince bir sart bile dogru yakalandi. Karakter setinin farkli olmasi extraction kalitesini dusurmedi.

### [yabanci_dil_ja] https://www.jetro.go.jp/services/j-starx/pre-startup.html

**Tavily:** basarili=True, karakter_sayisi=8971

**Gemini:** input_token=4240, output_token=500

```json
{
  "organizator": "JETRO (Japan External Trade Organization)",
  "konu_kategori": "Girişimcilik / Startup Eğitim Programı",
  "son_basvuru_tarihi": "2026-05-20 23:59 (JST)",
  "onemli_tarihler": "Başvuru Dönemi: 30 Nisan - 20 Mayıs 2026; Sonuç Açıklama: 26 Mayıs 2026 civarı; Yurtiçi Program (Tokyo): 5 - 7 Haziran 2026; Yurtdışı Program (Silikon Vadisi): 24 Ağustos - 11 Eylül 2026; Takip Programı: Kasım 2026 sonrası",
  "basvuru_asamalari": "Belge incelemesi, çevrimiçi video değerlendirmesi ve mülakat (gerekli görülmesi halinde)",
  "yer_mekan": "Yurtiçi Program: Tokyo (JETRO Genel Merkezi), Yurtdışı Program: Silikon Vadisi (Palo Alto, ABD)",
  "konaklama_yol_destegi": true,
  "odul_miktari_turu": "Silikon Vadisi eğitim programına katılım, eğitim ücreti muafiyeti, yurtiçi ve yurtdışı ulaşım ile konaklama masraflarının karşılanması, birebir mentörlük desteği",
  "katilim_sartlari": "1 Temmuz 2026 tarihi itibarıyla en az 18 yaşında olan öğrenciler; Pre-seed (kurulum öncesi) aşamasında olmak; İngilizce mentörlük, sunum ve iş görüşmesi yapabilecek düzeyde İngilizce bilgisine sahip olmak; Geliştirilen ürün/hizmetin yurtdışı açılımında karar yetkisine sahip olmak; Program sonrası anketlere katılım sağlamak",
  "takim_buyuklugu_limiti": null,
  "basvuru_maliyeti": "Ücretsiz",
  "istenen_materyal": "İngilizce pitch deck (sunum belgesi) ve İngilizce pitch videosu",
  "sponsor_kurumlar": null
}
```

**Kalite degerlendirmesi:** Japonca kaynaktan da yuksek kalite: saat dilimi dahil son basvuru tarihi (JST), iki farkli program yeri (Tokyo/Silikon Vadisi), yas/dil sartlari, boolean alan (konaklama_yol_destegi=true) dogru tipte donduruldu. Sema disiplini iyi korunmus.

### [genel_org_sayfasi] https://www.teknofest.org

**Tavily:** basarili=True, karakter_sayisi=138787

**Gemini:** input_token=7239, output_token=207

```json
{
  "organizator": "TEKNOFEST",
  "konu_kategori": "Aerospace and Technology",
  "son_basvuru_tarihi": null,
  "onemli_tarihler": null,
  "basvuru_asamalari": null,
  "yer_mekan": "Gölcük Naval Shipyard Command",
  "konaklama_yol_destegi": null,
  "odul_miktari_turu": null,
  "katilim_sartlari": null,
  "takim_buyuklugu_limiti": null,
  "basvuru_maliyeti": null,
  "istenen_materyal": "Simulation Report, Presentation, Preliminary Design Report, Critical Design Report, Conceptual Design Report, Technical Qualification Form, Project Presentation Report",
  "sponsor_kurumlar": null
}
```

**Kalite degerlendirmesi:** Beklenen sinirlama burada ortaya cikti: bu bir genel organizasyon ana sayfasi oldugu icin tek bir 'firsat' degil, onlarca yarismanin semsiyesi. Model bunu kismen dogru yonetti (cogu tekil alani null birakti) ama istenen_materyal alanina farkli yarismalardan genel bir liste karisti. Sonuc: sema, coklu-etkinlik barindiran genel sayfalar icin uygun degil - bu tur linkler ozel bir mantikla (or. atla ya da coklu kayit) yonlendirilmeli.
