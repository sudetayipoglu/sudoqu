# Model Karsilastirma Raporu: Firsat Verisi Cikarimi Icin LLM Secimi

Tarih: 2026-07-12
Test seti: Ayni 12 linkli cesitli kaynak grubu (universite x3, devlet x2, instagram x2, PDF/TR x1, yabanci dil PDF/FR x1, yabanci dil ZH x1, yabanci dil JA x1, genel organizasyon sayfasi x1) - pilot testte kullanilan set ile ayni.
Sema: 13 alanli, tumu nullable (organizator, konu_kategori, son_basvuru_tarihi, onemli_tarihler, basvuru_asamalari, yer_mekan, konaklama_yol_destegi, odul_miktari_turu, katilim_sartlari, takim_buyuklugu_limiti, basvuru_maliyeti, istenen_materyal, sponsor_kurumlar), prompt "uydurma, veri yoksa null don" talimati icerir.

## Not: DeepSeek testi bu turda yapilamadi

DeepSeek V4 Flash (NVIDIA NIM uzerinden, deepseek-ai/deepseek-v4-flash) test edilmek istendi ancak NVIDIA'nin ucretsiz katmaninda bu modele ozel paylasimli kapasite doluluguyla karsilasildi: art arda 3 denemede de "503 ResourceExhausted: Worker local total request limit reached (48/48)" hatasi alindi (bizim hesaba/anahtara ozel bir kota degil, modelin genel/paylasimli kapasitesi doluydu). Ayni hesapla deepseek-ai/deepseek-v4-pro sorunsuz calisti, deepseek-ai/deepseek-coder-6.7b-instruct ise hesapta etkin degildi (404). Karar geregi V4 Pro ile ikame yapilmadi; DeepSeek karsilastirmasi bu turda atlandi, NVIDIA'nin paylasimli kapasitesi musait oldugunda ileride tekrar denenebilir.

Bu rapor sadece 2 modeli karsilastirir: **Gemini 3.5 Flash** (alias: gemini-flash-latest, orijinal pilotta kullanilan tam model) ve **Gemini 3.1 Flash-Lite** (alias: gemini-flash-lite-latest, bu turda test edilen hafif model).

## Basari Sayisi (12 link uzerinden)

| Model | Basarili | Basarisiz | Not |
|---|---|---|---|
| Gemini 3.5 Flash (pilot, referans) | 11/12 | 1/12 | Tek hata Tavily kaynakli: atonet.org.tr PDF 404 (model calismadan once kaynak alinamadi) |
| Gemini 3.1 Flash-Lite (bu turda test edildi) | 11/12 | 1/12 | Ayni tek hata: atonet.org.tr Tavily 404 (kaynaktan bagimsiz, iki modelde de ayni sekilde basarisiz) |

Her iki modelde de Gemini tarafinda sifir basarisizlik var; tek basarisizlik Tavily'nin o siteye ulasamamasindan (site 404), model secimiyle ilgisi yok.

## Alan Bazinda Kalite Karsilastirmasi (gercek icerik ornekleriyle)

### son_basvuru_tarihi (en kritik alan)

Bu, iki model arasindaki en net farki gosteren alan. Gemini 3.5 Flash (pilot) tarihleri ISO'ya yakin/normallesmis ve okunakli bicimde donduruyordu; Gemini 3.1 Flash-Lite ise **kaynagin orijinal dilinde/biciminde, normallestirmeden** donduruyor:

| Kaynak | Gemini 3.5 Flash (pilot) | Gemini 3.1 Flash-Lite (bu test) |
|---|---|---|
| nsfc.gov.cn (Cince) | (pilotta bu link yoktu, karsilastirma yapilamadi) | "2026年3月20日16时" - Cince karakterlerle, cevrilmemis/normallesmemis |
| jetro.go.jp (Japonca) | Japon kaynaktan JST saat dilimiyle birlikte dogru cikarildigi not edilmisti ("Japonca kaynaktan da yuksek kalite: saat dilimi dahil son basvuru tarihi... dogru tipte donduruldu") | "2026年5月20日（水曜）23時59分（JST）" - Japonca karakter ve gun-adi bicimiyle aynen birakilmis, temizlenmemis |
| ubacameroon.com (Fransizca PDF) | Turkceye cevrilerek, temiz bicimde cikarildigi not edilmisti | "1 March 2026" - Ingilizce/orijinal bicimde, Turkce/ISO'ya cevrilmemis |
| bilimgenc.tubitak.gov.tr | "20 Subat 2026" tarzi okunakli | "20 Subat 2026" - ayni, bu Turkce kaynakta fark yok |

Sonuc: Turkce kaynaklarda iki model de esdeger. Yabanci dil kaynaklarda tam model (3.5 Flash) tarihi normallestirip/cevirip donduruyor, Lite model ise ham/orijinal dil-bicimini oldugu gibi birakiyor - bu, sema talimatinda istenen "ISO YYYY-MM-DD veya null" formatina Lite modelin uymadigi anlamina geliyor (tam model de saf ISO degil ama en azindan okunakli/normallesmis Turkce/Ingilizce bicimde donduruyordu).

### odul_miktari_turu

Benzer desen: Lite model yabanci kaynaklarda cevirmeden birakiyor - orn. nsfc.gov.cn icin "科研项目资助" (Cince, cevrilmemis), ubacameroon.com icin "US\$5,000 non-refundable seed capital" (Ingilizce, cevrilmemis). Turkce kaynaklarda (bilimgenc.tubitak.gov.tr: "Toplam 75 milyon TL odul ve 100 milyon TL'yi asan maddi destek") iki model de dogru ve tutarli.

### katilim_sartlari

Lite model bazen tam modelin bos biraktigi alanlari da dolduruyor - orn. sgb.meb.gov.tr kaydinda tam model (pilot) katilim_sartlari alanini null birakmisti (sayfa gecmis bir calistay haberi oldugu icin), Lite model ise "Balikesir, Istanbul, Edirne, Canakkale, Tekirdag ve Kirklareli illerinden secilen ogrenci, ogretmen ve yoneticiler" seklinde bir deger uretti - bu ozgun icerikte gercekten var olan bilgi olabilir (yani Lite burada daha "cesur" davranip fazladan dogru bilgi cikarmis olabilir) fakat dogrulama yapilmadi, iki yorumdan biri secilemez. Yabanci dil kaynaklarda ise ayni cevrilmeme sorunu burada da gecerli (Cince/Japonca metin oldugu gibi kaliyor).

## JSON Sema Uyumu

Her iki modelde de basarili cagrilarin tamaminda (11/11 her iki model icin) JSON parse hatasi veya sema disi alan sorunu YOK. Lite modelde `response_mime_type=application/json` + `response_schema` (Pydantic) yapisal cikti zorlamasi sorunsuz calisti, ekstra temizlik/markdown-fence stripping gerekmedi. Basarisizliklarin tamami (1/1 her iki model icin) Tavily kaynak erisim hatasindan (atonet.org.tr 404) kaynaklandi, model tarafinda degil.

## Rate-Limit / Kota Davranisi

- **Gemini 3.5 Flash (gemini-flash-latest):** Onceki uretim entegrasyonu testinde (Task E, bu rapordan bagimsiz) bu projede ucretsiz katmanda gunde sadece **20 istek/gun (RPD)** kotasiyla karsilasildi (canli API 429 hata metadata'siyla dogrulandi). 442 kayitlik tam backfill icin bu, ~22 gun surer ya da faturalandirma (Tier 1) acilmasi/Batch API kullanilmasi gerekir.
- **Gemini 3.1 Flash-Lite (gemini-flash-lite-latest):** Bu 12 link testinde 13 saniyelik call araligiyla calistirildi, **hicbir 429/kota hatasi alinmadi**, 11/11 basarili cagri sorunsuz tamamlandi. Bu, kesin bir RPD rakami kanitlamiyor (12 cagri kucuk bir ornek) ama bu kadarlik bir hacimde Lite modelin gorunur bir kota duvarina carpmadigini gosteriyor - flash-lite ailesi genelde flash'tan daha yuksek ucretsiz RPD limitine sahip oluyor (Google'in genel kota yapisinda gozlemlenen bir egilim), fakat kesin sayi projeye ozel oldugundan Google AI Studio'dan teyit edilmeli.

## Ortalama Yanit Suresi

- **Gemini 3.1 Flash-Lite:** Bu testte olculen gercek model-cagrisi suresi (bekleme/sleep haric) cagri basina **~1.0-1.5 saniye**, ortalama ~1.25 saniye. Toplam test suresi 157 saniye gorunuyordu ama bunun buyuk kismi (12 cagri x 13 saniye = 156 sn) testte bilerek konulan bekleme araligindan kaynaklaniyordu, model gecikmesinden degil.
- **Gemini 3.5 Flash:** Orijinal pilot betigi cagri basina sureyi ayri loglamadigi icin bu rapor icin dogrudan bir rakam yok - bu bir eksiklik olarak not ediliyor, uydurma bir sayi verilmiyor. Genel beklenti: tam model, lite modelden yapisal olarak daha yavas olur (daha buyuk model boyutu), ama kesin farkla ilgili elimde olcum yok.

## Tahmini Tam 442 Kayit Backfill Maliyeti (guncel resmi fiyatlandirma ile)

Fiyatlar ai.google.dev/gemini-api/docs/pricing sayfasindan (2026-07-12 itibariyla) alinmistir, standart (batch olmayan) katman:

| Model | Input fiyat | Output fiyat | Pilot/test basina ort. token (in/out) | 442 icin tahmini toplam token (in/out) | Tahmini toplam maliyet |
|---|---|---|---|---|---|
| Gemini 3.5 Flash | $1.50 / 1M | $9.00 / 1M | ~4.130 / ~313 | ~1.83M / ~138K | **~$3.98** |
| Gemini 3.1 Flash-Lite | $0.25 / 1M | $1.50 / 1M | ~4.128 / ~266 | ~1.82M / ~117K | **~$0.63** |

Not: Her iki modelde de dolar bazinda mutlak fark kucuk (tek seferlik 442 kayitlik backfill icin ~$3.35 fark) - asil pratik fark maliyet degil, **Gemini 3.5 Flash'in 20 istek/gun kotasi**. Batch API kullanilirsa (her iki model icin de ~%50 indirim) maliyetler daha da duser (3.5 Flash icin ~$2, Lite icin ~$0.32) ama kota kisitini Batch API'nin cozup cozmedigi ayrica dogrulanmali.

## Oneri

Bu iki modelin sundugu tercih, klasik bir kalite/hiz/kota ucgeni:

- **Gemini 3.5 Flash** daha iyi kalite veriyor (ozellikle yabanci dil kaynaklarda ceviri + tarih normallestirme), ama gunde 20 istekle sinirli - 442 kaydin tamamini gecirmek icin ya haftalar surecek bir bekleme ya da faturali katmana gecis gerekiyor.
- **Gemini 3.1 Flash-Lite** bu testte hicbir kota duvarina carpmadi, cok daha hizli (~1.2 sn/cagri) ve cok daha ucuz (~6x daha ucuz), JSON sema uyumu ve Turkce kaynaklarda kalite tam modelle esdeger. Tek gercek zayifligi: yabanci dilli (Cince/Japonca/Fransizca) kaynaklarda ceviri yapmiyor ve tarihleri normallestirmeden birakiyor - bu isin "ISO YYYY-MM-DD veya null" hedefine tam uymuyor.

Benim onerim: **442 kayitlik tam backfill icin Gemini 3.1 Flash-Lite ile devam edilmesi** - kota tarafinda pratik bir engel yok, maliyet onemsiz, hiz iyi, ve kaynaklarin buyuk cogunlugu zaten Turkce (universite/devlet/yerel kaynaklar) oldugu icin bu testte gozlemlenen ceviri zayifligi kayitlarin kucuk bir azinligini (yabanci dilli kaynaklari) etkileyecektir. Bu azinlik icin iki secenek dusunulebilir: (a) kabul edilebilir bir odun olarak birakmak (son_basvuru_tarihi yine de var, sadece orijinal dilde/formatta), ya da (b) sadece yabanci-dil-tespit-edilen kayitlar icin ayrica Gemini 3.5 Flash'e (kota izin verdikce, kucuk bir alt kume oldugu icin 20/gun kotasiyla bile makul surede) yonlendirme yapan bir hibrit yaklasim.

Son karar tabii ki size ait - yukaridaki veriler isiginda hangi model/yaklasimla devam edilecegini belirtirseniz ona gore ilerlerim. Hatirlatma: bu rapor icin 442 kaydin tamami HICBIR modelle calistirilmadi, sadece 12 linklik test seti kullanildi; production backfill ayri bir adim olarak sizin onayinizla baslatilacak.
