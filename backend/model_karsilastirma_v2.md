# Model Karsilastirma Raporu v2: 5 Yeni NVIDIA Katalog Modeli

Tarih: 2026-07-12
Test seti: Onceki testlerle AYNI 12 linklik cesitli kaynak grubu (universite x3, devlet x2, instagram x2, PDF/TR x1, yabanci dil PDF/FR x1, yabanci dil ZH x1, yabanci dil JA x1, genel organizasyon sayfasi x1), ayni Tavily cache (model_test_tavily_cache.json) yeniden kullanildi, yeni Tavily cekimi yapilmadi.
Erisim: NVIDIA API katalogu (https://integrate.api.nvidia.com/v1), .env'deki DEEPSEEK_API_KEY degiskeninde duran NVIDIA NIM anahtariyla, openai Python kutuphanesi ile.
Sema: Onceki raporla ayni 13 alan + prompta EKLENEN 2 yeni kural: (1) tum alanlar TURKCEYE cevrilerek yazilacak, (2) tarihler HER ZAMAN YYYY-MM-DD formatina normalize edilecek.

## Model ID Dogrulama Notu

Tum 5 model ID'si NVIDIA'nin canli /v1/models endpoint'inden sorgulanarak (tahmin edilmeden) dogrulandi:
- mistralai/mistral-medium-3.5-128b - talep edilen ID ile birebir ayni
- **z-ai/glm-5.2** - DIKKAT: gorev tanimindaki tahmin "zhipuai/glm-5.2" idi, ancak kataloktaki gercek prefix "z-ai", "zhipuai" DEGIL. Tek eslesen model bu oldugu icin belirsizlik yok, dogru ID ile devam edildi.
- stepfun-ai/step-3.7-flash - talep edilen ID ile birebir ayni
- deepseek-ai/deepseek-v4-pro - talep edilen ID ile birebir ayni
- meta/llama-3.1-70b-instruct - talep edilen ID ile birebir ayni (not: build.nvidia.com'daki bu modelin ozel katalog sayfasi 404 donuyor, muhtemelen web sitesinden kaldirilmis, ama API endpoint'i canli ve calisir durumda - dogrulandi)

## Onemli Not: NVIDIA Katalog Endpoint'i Uretim Fiyatlandirmasi Degildir

build.nvidia.com uzerinden her 5 modelin kendi sayfasi kontrol edildi: hepsi "Model Availability: Free Endpoint - Available" olarak isaretli. NVIDIA'nin resmi dokumantasyonuna gore bu katalog erisimi kredi bazli bir deneme sistemi: hesap basina 1000 baslangic kredisi (talep ile 4000'e kadar ek kredi, toplam 5000), model basina dakikada 40 istek (RPM) sinirlamasi ile. NVIDIA bunu acikca "prototipleme ve gelistirme icin, uretim icin degil" olarak konumlandiriyor - gercek uretim icin ya NVIDIA AI Enterprise lisansiyla kendi GPU'nuzda NIM konteynerini calistirmaniz (donanim bazli maliyet, token bazli degil) ya da modelin kendi resmi ticari API'sine (Mistral'in kendi API'si, Z.ai'nin kendi API'si, vb.) gecmeniz gerekiyor. Bu nedenle asagidaki maliyet tahminleri NVIDIA'nin degil, ilgili modelin ORIJINAL SAGLAYICISININ kendi resmi API fiyatlandirmasina dayaniyor (uretimde guvenilir/kalici kapasite icin gercekci referans budur).

Bu ayni zamanda onceki testte DeepSeek V4 Flash'te gordugumuz "Worker local total request limit reached (48/48)" 503 hatasini da aciklyor - bu, NVIDIA'nin paylasimli/kredi bazli deneme kapasitesinin dolmasi, kalici bir kota degil.

## Basari Sayisi ve Rate-Limit Davranisi (12 link uzerinden)

| Model | Basarili | Rate-limit/kota hatasi | Not |
|---|---|---|---|
| mistralai/mistral-medium-3.5-128b | 2/12 | Yok | Basarisizliklarin neredeyse tamami sema uyumsuzlugu (asagida detay) |
| z-ai/glm-5.2 | 5/12 | Yok | En hizli ikinci model, orta basari orani |
| stepfun-ai/step-3.7-flash | 0/12 | Yok | TUM cagrilar sema hatasi verdi, tek bir basarili extraction bile yok |
| deepseek-ai/deepseek-v4-pro | 7/12 | **Yok - onceki 503 sorunu bu seferki testte HIC TEKRARLANMADI** | En yuksek basari orani, hem hizli hem guvenilir |
| meta/llama-3.1-70b-instruct | 5/12 | Yok | Orta basari, tarihleri ISO'ya cevirdi ama cevirisi tutarsiz |

Onemli bulgu: DeepSeek V4 Pro icin onceki raporda (model_karsilastirma.md) DeepSeek V4 Flash'te gorulen 503 kapasite hatasi bu testte HICBIR ZAMAN olusmadi - 12/12 cagri da (basarili ya da sema-hatali) API'den gecerli bir yanit aldi, network/kapasite hatasi yasanmadi. Bu, V4 Pro'nun (kucuk paket boyutu/daha az yogun kullanilan bir model olmasi nedeniyle) su anda V4 Flash'e gore daha az paylasimli-kapasite baskisi altinda oldugunu gosteriyor - ancak bu durum NVIDIA'nin serbest katmaninda ani degisebilir, garanti degildir.

## JSON Sema Uyumu - Sistemik Bir Sorun Tespit Edildi

Bes modelin BESI de ayni tur hatayla basarisiz oldu: onemli_tarihler alani (bazen organizator veya konu_kategori da) semada string|null olarak tanimliyken, modeller genellikle bunu bir LISTE veya nesne olarak donduruyor (birden fazla onemli tarih oldugunda dogal olarak bir liste dusunuyorlar). Bu, Pydantic validasyonunda 'Input should be a valid string' hatasina yol aciyor.

Bu, tek bir modelin degil, SEMANIN KENDISININ bir tasarim sorunu olabilir: onemli_tarihler (cogul bir isim) alani icin string tipi modellere dogal gelmiyor. Basarisizlik siklikta:
- stepfun-ai/step-3.7-flash: 12/12 basarisizlik, TAMAMI bu hatadan
- mistralai/mistral-medium-3.5-128b: 10/12 basarisizlik, buyuk cogunlugu bu hatadan
- z-ai/glm-5.2: 7/12 basarisizlik, hepsi bu hatadan
- meta/llama-3.1-70b-instruct: 7/12 basarisizlik (2si Tavily kaynakli), geri kalani bu hatadan
- deepseek-ai/deepseek-v4-pro: 5/12 basarisizlik (1i Tavily kaynakli), geri kalani bu hatadan

DeepSeek V4 Pro bu soruna en az dusen model oldu (12 cagridan sadece 4u bu hatayla basarisiz oldu, geri kalaninda model dogru sekilde string donmeyi basardi).

Onemli not/oz-elestiri: Bu sema-katiligi sorunu kismen benim semamdan kaynaklaniyor olabilir - onemli_tarihler alanini yalnizca string olarak tanimladim, modellerin birden fazla tarih varsa dogal olarak liste dondurme egilimini hesaba katmadim. Ileride bu alan icin ya List[str]|str|None gibi daha esnek bir tip tanimlanabilir ya da prompt icinde bu alani TEK BIR STRING olarak, birden fazla tarihi virgul/noktali virgulle ayirarak yaz seklinde daha acik bir talimat eklenebilir. Bu, model kalitesinden once semanin/promptun iyilestirilmesi gereken bir alan.

## Alan Bazinda Dogruluk (basarili cikan sonuclardan gercek ornekler)

### son_basvuru_tarihi (ISO YYYY-MM-DD normalizasyonu)

Tum basarili cikan sonuclarda TUM 5 model tarihleri dogru sekilde YYYY-MM-DD formatina normalize etti (orn. bilimgenc.tubitak.gov.tr icin '2026-02-20', mehmetakif.edu.tr icin '2026-04-27'). Bu, onceki testte Gemini 3.1 Flash-Lite'in basarisiz oldugu tam da bu nokta - Gemini Flash-Lite yabanci kaynaklarda tarihi orijinal dilde/formatta birakiyordu (orn. Japonca '2026年5月20日'), bu 5 modelin basarili ciktilarinin HICBIRINDE boyle bir sorun gorulmedi.

### odul_miktari_turu ve Turkceye Ceviri (en onemli fark buradaydi)

| Kaynak | Model | Sonuc |
|---|---|---|
| ubacameroon.com (Fransizca PDF) | DeepSeek V4 Pro | "5.000 ABD Dolari geri odemesiz baslangic sermayesi, dunya standartlarinda egitim" - TAM TURKCEYE CEVRILMIS |
| ubacameroon.com (Fransizca PDF) | Llama-3.1-70B | "US$5,000 non-refundable seed capital" - CEVRILMEMIS, Ingilizce/orijinal dilde birakildi |
| bilimgenc.tubitak.gov.tr (Turkce) | GLM-5.2 | "Toplam 75 milyon TL odul ve 100 milyon TL'yi asan maddi destek" - doğru, Turkce kaynakta zaten fark yok |
| bilimgenc.tubitak.gov.tr (Turkce) | DeepSeek V4 Pro | Ayni icerik, dogru |

Bu tek ornek (ayni Fransizca kaynak, iki farkli model) net bir ayrim gosteriyor: DeepSeek V4 Pro prompttaki 'tum alanlari Turkceye cevir' talimatina tam uydu, Llama-3.1-70B ise tarihi ISO'ya cevirdi ama metin icerigini cevirmedi. Mistral, GLM ve Step-3.7 yabanci dil kaynaklarinin (zh/ja/fr) HICBIRINDE basarili bir extraction yapamadi (hepsi onemli_tarihler sema hatasina takildi), bu yuzden bu 3 model icin yabanci-dil-cevirisi kalitesi bu testte dogrudan olculemedi.

### katilim_sartlari

GLM-5.2, bilimgenc.tubitak.gov.tr icin "Ilkokul, ortaokul, lise, on lisans ve lisans, lisansustu, mezun, girisim ve ozel sektorden katilimcilar ile uluslararasi" seklinde detayli ve dogru bir katilim sarti cikardi. Diger modellerin basarili orneklerinde bu alan siklikla null donduruldu (kaynakta acikca belirtilmemis olabilir, ya da model temkinli davranmis olabilir) - uydurma/halusinasyon belirtisi gorulmedi, bu olumlu bir bulgu.

## Ortalama Yanit Suresi

Her modelin toplam calisma suresinden, cagrilar arasindaki 5sn'lik bekleme (11 x 5sn = 55sn) cikarilarak yaklasik cagri-basina sure hesaplandi:

| Model | Toplam sure (12 cagri) | Yaklasik ort. cagri suresi |
|---|---|---|
| z-ai/glm-5.2 | 231sn | ~14.7sn/cagri (en hizli) |
| deepseek-ai/deepseek-v4-pro | 264sn | ~17.4sn/cagri |
| meta/llama-3.1-70b-instruct | 421sn | ~30.5sn/cagri |
| stepfun-ai/step-3.7-flash | 482sn | ~35.6sn/cagri |
| mistralai/mistral-medium-3.5-128b | 609sn | ~46.2sn/cagri (en yavas) |

Karsilastirma icin: onceki testte Gemini 3.1 Flash-Lite ~1.2sn/cagri idi - yani bu 5 NVIDIA modelinin HICBIRI Gemini Flash-Lite'in hizina yaklasamiyor, en hizlisi (GLM-5.2) bile ~12 kat daha yavas.

## Tahmini Tam 442 Kayit Backfill Maliyeti

NVIDIA katalog endpoint'i uzerinde su an icin $0 dogrudan maliyet var (kredi/RPM siniri dahilinde), ancak yukarida aciklandigi gibi bu uretim icin guvenilir/kalici bir model degil. Asagidaki tahminler, HER MODELIN KENDI ORIJINAL SAGLAYICISININ resmi ticari API fiyatlandirmasi kullanilarak hesaplanmistir (uretimde guvenilir kapasite icin gercekci referans):

| Model | Resmi kaynak fiyati (1M token) | Bu testte basarili cagri basina ort. token (in/out) | 442 icin tahmini toplam maliyet |
|---|---|---|---|
| DeepSeek V4 Pro | $0.435 in / $0.870 out (DeepSeek'in kendi API'si) | ~4.642 / ~297 | **~$1.01** |
| Llama-3.1-70B-Instruct | ~$0.40 blended (DeepInfra referans - Meta dogrudan satmiyor) | ~2.542 / ~198 | **~$0.48** |
| GLM-5.2 | $1.40 in / $4.40 out (Z.ai'nin kendi API'si) | ~4.386 / ~234 | **~$3.17** |
| Mistral Medium 3.5 | $1.50 in / $7.50 out (Mistral'in kendi API'si) | ~4.344 / ~167 | **~$3.44** |
| Step-3.7-Flash | $0.20 in / $1.15 out (StepFun'un kendi API'si) | Basarili cagri YOK, tahmin yapilamiyor | **Hesaplanamadi (0/12 basari)** |

Not: Basari orani dusuk olan modellerde (Mistral 2/12, Llama 5/12) ortalama token sayisi kucuk bir ornekten hesaplandigi icin 442'ye olcekleme kesinligi dusuk - bu rakamlar yaklasik referans olarak degerlendirilmeli, kesin butce degil.

Referans (onceki rapordan): Gemini 3.1 Flash-Lite icin tahmini 442 maliyeti ~$0.63 idi (Google'in kendi resmi API fiyatiyla, ayni sekilde 'gercek' bir uretim fiyati - Gemini'de NVIDIA katalogundaki gibi 'sadece deneme' belirsizligi yok).

## 6 Modelin Tam Karsilastirmasi (Gemini 3.1 Flash-Lite referans + 5 yeni model)

| Model | Basari (12) | Sema uyumu | Yabanci dil ceviri+ISO tarih | Rate-limit sorunu | Ort. hiz | Tahmini 442 maliyeti |
|---|---|---|---|---|---|---|
| **Gemini 3.1 Flash-Lite** (mevcut en iyi) | 11/12 | Sorunsuz | HAYIR - orijinal dil/format birakiliyor | Yok | ~1.2sn (en hizli) | ~$0.63 |
| DeepSeek V4 Pro | 7/12 | Iyi (4/12 sema hatasi) | EVET - hem ceviri hem ISO (tek ornekte dogrulandi) | Yok (onceki 503 tekrarlanmadi) | ~17.4sn | ~$1.01 |
| Llama-3.1-70B | 5/12 | Orta (7/12 sema hatasi) | KISMEN - ISO tarih evet, ceviri hayir | Yok | ~30.5sn | ~$0.48 |
| GLM-5.2 | 5/12 | Orta (7/12 sema hatasi) | Test edilemedi (yabanci kaynaklarda hep basarisiz) | Yok | ~14.7sn | ~$3.17 |
| Mistral Medium 3.5 | 2/12 | Zayif (10/12 sema hatasi) | Test edilemedi | Yok | ~46.2sn | ~$3.44 |
| Step-3.7-Flash | 0/12 | Cok zayif (12/12 sema hatasi) | Test edilemedi | Yok | ~35.6sn | Hesaplanamadi |

## Oneri

Bu turun en carpici sonucu su: **Gemini 3.1 Flash-Lite, basari orani (11/12), hiz (~1.2sn/cagri) ve JSON sema uyumu acisindan bu 5 yeni modelin hepsinden acik ara onde.** 5 modelin dorduncu (onemli_tarihler sema hatasi) NVIDIA'nin serbest/deneme katmaninda calisan bu modellerin bu spesifik semaya Gemini kadar iyi uymadigini gosteriyor.

Bunun tek istisnasi **DeepSeek V4 Pro**: dusuk de olsa makul bir basari orani (7/12), rate-limit sorunu yok (onceki V4 Flash'teki 503 sorunu tekrarlanmadi), VE en onemlisi - basarili oldugu tek yabanci dil orneginde hem ceviriyi hem ISO tarih normallesmesini dogru yapti; bu, Gemini Flash-Lite'in tam basaramadigi konu. Eger asil hedef yabanci dilli kaynaklarda kaliteyi artirmaksa, DeepSeek V4 Pro bu 5 model icinde en umut verici aday.

Ancak DIKKAT: DeepSeek V4 Pro (ve digerleri) su an NVIDIA'nin PAYLASIMLI/DENEME kapasitesinde calisiyor - kalici degil, kredi sinirlariyla kisitli, ve 442 kayitlik bir backfill'i bu ücretsiz katmanla guvenle tamamlamak garanti degil (V4 Flash'te yasadigimiz kapasite dolulugu ornegi bunu gosteriyor). Gercek uretim icin DeepSeek'in kendi resmi API'sine (api.deepseek.com, ayri bir hesap/anahtar gerektirir) gecmek gerekir.

**Benim onerim:** Ana model olarak Gemini 3.1 Flash-Lite ile devam edilmesi (kota/hiz/sema uyumu/maliyet - hepsi acik favori). Eger yabanci dilli kaynaklarin cevirisi onemliyse, kucuk bir alt kume icin (tespit edilen yabanci-dil kayitlari) DeepSeek V4 Pro'ya - ama NVIDIA'nin ucretsiz katmaninda degil, DeepSeek'in KENDI resmi API'sinde (api.deepseek.com, ayri hesap) - yonlendiren bir hibrit yaklasim degerlendirilebilir. Mistral, GLM-5.2 ve Step-3.7-Flash bu haliyle (bu sema ile) production'a uygun degil - basari oranlari cok dusuk, temel sorun sema/prompt uyumsuzlugu (onemli_tarihler alani), model kalitesinden cok semanin bu modellerle uyusmamasi.

Son karar sizin - yukaridaki verilerle hangi yonde ilerlemek istediginizi belirtirseniz ona gore devam ederim. Hatirlatma: 442 kaydin tamami HICBIR modelle calistirilmadi, sadece 12 linklik test kullanildi; radar.py'nin uretim kodu bu testte degistirilmedi.
