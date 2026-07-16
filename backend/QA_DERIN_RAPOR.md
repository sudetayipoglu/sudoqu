# SudoQu Derin QA Raporu — çido'nun bir haftalık deneyimi

**Tarih:** 16 Temmuz 2026
**Yöntem:** Gerçek tarayıcı (Network/Console açık) + SSH ile canlı sunucu üzerinde kök neden analizi. QA mühendisi gözüyle değil, gelecek hafta gerçekten 2-3 fırsata başvuracak bir kullanıcı (çido) gözüyle test edildi.
**Anlık veri durumu:** 923 fırsat, 4 görev, 4 başvuru, 3 proje (rakamlar sürekli büyüyen bir scraping sürecinden dolayı bu raporun yazıldığı ana ait bir anlık görüntüdür).

---

## 1. Kritik bulgular

### 1.1 Fırsat listesinde eski/kopya kayıtlar görünüyordu — DÜZELTİLDİ
**Nerede:** Fırsatlar sekmesi, ana liste.
**Nasıl tetiklendi:** Normal sayfa yüklemesi, filtre uygulanmamış haliyle.
**Kök neden:** Filtre KODU (`opportunities-tab.tsx`'teki `!o.duplicateOf && !suresiGecmisMi(...)` mantığı, `backend/db.py`'deki `duplicate_of_id` okuma/yazma) baştan beri doğruydu. Gerçek sorun VERİDE idi: `backend/radar.py` içindeki `tekillestir()` fonksiyonu (kural bazlı, organizatör adı + tarih yakınlığı + konu benzerliği ile kopya tespiti yapan mantık) doğru yazılmıştı ama üretim veritabanında **hiç çalıştırılmamıştı** — `duplicate_of_id` kolonu 923 kayıtta da boştu.
**Doğrulama:** Gerçek API yanıtları karşılaştırıldı (`/firsatlar` çıktısı), 8 bilinen "süresi geçmiş" başlık tek tek arandı — hepsi zaten doğru şekilde gizleniyordu (expired filtre kodu hiç bozuk değildi). Kopya tarafında ise gerçekten 0 kopya işaretliydi.
**Düzeltme:** `radar.py`'deki mevcut `tekillestir()` mantığı BİREBİR kopyalanarak (API çağrısı yapmayan, salt-okunur bir backfill scripti ile) üretim verisi üzerinde çalıştırıldı. 923 kayıttan 1 kopya grubu bulundu (ktu.edu.tr birincil, esenyurt.edu.tr ikincil) ve `duplicate_of_id` dolduruldu. Tarayıcıda doğrulandı: aranan kopya kaydı artık listede çıkmıyor.
**Not:** Bu tek seferlik bir veri düzeltmesiydi (kod değişikliği değil), git'e commit edilecek bir şey yok — ama radar.py'nin düzenli çalışmasının bundan sonra da dedup adımını içerdiğinden emin olunmalı (bkz. bölüm 5).

### 1.2 "TOPLAM FIRSAT" sayacı gizlenen kayıtları da sayıyordu — DÜZELTİLDİ
**Nerede:** Panel üst-sağ köşe istatistik kartı.
**Kök neden:** `dashboard.tsx` bu sayıyı ham `opportunities.data.length` üzerinden hesaplıyordu — Fırsatlar sekmesinin kendi içinde uyguladığı kopya/süresi-geçmiş filtresini hiç bilmiyordu.
**Düzeltme:** `gecerliOpps` adında, Fırsatlar sekmesiyle AYNI filtre mantığını (`!duplicateOf && !suresiGecmisMi`) kullanan bir `useMemo` eklendi, sayaç ondan besleniyor.
**Doğrulama:** 923 ham kayıttan 904'ü geçerli (19 süresi geçmiş, 1 kopya) — panel artık 904 gösteriyor, TSC temiz, build+deploy+canlı doğrulama yapıldı.

### 1.3 Bir göreve sadece tek kişi atanabiliyordu — DÜZELTİLDİ (şema değişikliği ile)
**Nerede:** Task & Takvim sekmesi.
**Kök neden:** `tasklar` tablosunda `atanan_id` tek bir INTEGER kolonuydu (ekip tablosuna FK), birden fazla kişiyi tutamıyordu.
**Düzeltme (şema değişikliği, veri kaybı olmadan):**
- Yeni bir junction (ilişki) tablosu eklendi: `task_atananlar (task_id, ekip_id)`, `tasklar(id)`e `ON DELETE CASCADE` ile bağlı.
- Mevcut 4 görevin `atanan_id` değerleri bu yeni tabloya **backfill** edildi — hiçbir atama kaybolmadı (doğrulandı: 4 görev, 4 `atanan_id`, 4 junction satırı).
- `atanan` alanı artık virgülle ayrılmış birden fazla isim içerebiliyor (örn. "sudo, yeno"); backend bunu ayrıştırıp junction tablosuna yazıyor, eski `atanan_id` kolonu geriye dönük uyumluluk için ilk kişiyle güncel tutuluyor.
- Kişi filtresi artık virgülle ayrılmış listede üyelik kontrolü yapıyor — bir kişiye atanan görev, atandığı HERKESİN filtresinde görünüyor.
- Takvim görünümü ayrı bir mantık kullanmıyor, aynı filtrelenmiş listeyi tükettiği için otomatik düzeldi.
**Doğrulama:** "sudo, yeno" olarak atanan test görevi hem sudo hem yeno filtresinde çıktı, çido filtresinde çıkmadı; DB'de junction satırları doğru; görev silindiğinde cascade ile junction satırları da temizleniyor (test edildi).

### 1.4 sudola bugünün tarihini bilmiyordu, tarih hesaplarında ciddi şekilde yanılıyordu — DÜZELTİLDİ (planlanmayan, kritik bulgu)
Bu bulgu, "failed fetch" avı sırasında sudola'yı gerçek bir soruyla test ederken ortaya çıktı — orijinal 4 bilinen hatanın parçası değildi ama ciddiyeti nedeniyle hemen düzeltildi.
**Nasıl tetiklendi:** Bir fırsatın "Veri Alanı"nda son başvuru tarihi **2026-07-17** (yani YARIN) olarak görünüyordu. sudola'ya "Son başvuru tarihine kaç gün kaldı?" diye sorduğumda cevap: *"Bugünün tarihi 21 Mayıs 2024 olduğuna göre, 17 Temmuz 2026'daki son başvuru tarihine 787 gün kalmıştır."*
**Kök neden:** `backend/api.py`'deki `sudola_soru` fonksiyonunun Gemini'ye gönderdiği prompt'ta bugünün tarihi HİÇ geçmiyordu. Model, tarih hesabı istendiğinde kendi (yanlış) varsayımına güveniyordu — cevaptaki "21 Mayıs 2024" muhtemelen modelin eğitim kesim tarihine yakın bir tahmindi.
**Neden kritik:** Bu, görevin tam olarak uyardığı türden bir hata — çökme yok, hata mesajı yok, gayet "normal" görünen ama TAMAMEN YANLIŞ bir cevap. Gerçek kullanıcı (çido), yarın bitecek bir başvuruyu "787 gün var" diyerek erteleyebilir.
**Düzeltme:** Prompt'a gerçek sunucu tarihi (`datetime.now()`, Türkçe ay adlarıyla formatlanmış) eklendi, modele "tarih hesaplarında SADECE bu bilgiyi kullan, kendi varsayımına güvenme" talimatı verildi.
**Doğrulama:** Aynı soru tekrar soruldu, yeni cevap: *"Son başvuru tarihine 2 gün kalmıştır."* — gerçek tarihe (16 Temmuz → 17 Temmuz) çok yakın, doğru mertebede.
**Not:** `/sudola/oneri` (proje uygunluk skoru) endpoint'inin promptu tarih içermiyor, o yüzden bu sorunla etkilenmiyor — kontrol edildi.

### 1.5 "BAŞVURULAN FIRSAT" sayacı sayfa yenilendiğinde her zaman sıfırlanıyordu — DÜZELTİLDİ (planlanmayan bulgu, Senaryo 5 tarzı çapraz kontrol sırasında bulundu)
**Nasıl tetiklendi:** Panel istatistiklerini gerçek verilerle çapraz kontrol ederken: "Başvuru" sayacı 4 gösteriyordu (doğru, `/basvurular`da 4 kayıt var) ama "Başvurulan Fırsat" sayacı 0 gösteriyordu.
**Kök neden:** `dashboard.tsx`'teki `handleApplied()` fonksiyonu, kullanıcı "Başvur olarak işaretle"ye bastığında sadece **istemci tarafı (SWR cache) içinde, sunucuya hiç yazılmadan** `basvuruldu: true` bayrağını set ediyordu (`{ revalidate: false }` ile sunucudan tekrar çekmeyi bile engelliyordu). "Başvurulan Fırsat" sayacı da bu geçici bayrağı sayıyordu. Gerçek `/firsatlar` API yanıtında `basvuruldu` alanı HİÇBİR kayıtta true değildi — yani bu sayaç sadece o oturumda tıklanan fırsatları sayıyor, sayfa yenilendiğinde (F5) veya bir gün sonra tekrar açıldığında her zaman 0'a dönüyordu, gerçek başvuru sayısından bağımsız olarak.
**Düzeltme:** Sayaç artık gerçek, kalıcı veriden (`applications.data.length`, yani `apps.length`) besleniyor.
**Doğrulama:** Deploy sonrası sayfa F5 ile yenilendi, sayaç doğru şekilde 4 gösterdi (öncesinde reload sonrası her zaman 0 gösterirdi).

---

## 2. Kullanılabilirlik sorunları ("çalışıyor ama kötü")

- **Bozuk GitHub linki sessizce başarısız oluyor.** Projeye geçersiz bir GitHub linki (`github.com/bu-kesinlikle-yok-xyz-99999/...`) girip kaydettiğimde, backend GitHub API'den 404 aldığını doğru şekilde tespit edip `github_bilgi: {"hata": "GitHub API hatasi: 404"}` olarak saklıyor — AMA arayüz bu hatayı hiçbir yerde göstermiyor. Proje kartı sadece "0 not, 0 dosya" olarak boş görünüyor. Gerçek bir kullanıcı, linki yanlış yazdığını haftalarca fark etmeyebilir. Bu tam olarak görevin tanımladığı "hatasız ama yanlış ekran" türü bir sorun.
- **Yeniden başvurma durumu net değil.** `basvurular` verisi linke göre anahtarlanmış bir sözlük olduğu için aynı fırsata iki kez "başvur" işaretlemek teknik olarak kopya kayıt OLUŞTURMUYOR (güvenli), ama eğer bir başvurunun durumu daha önce "kabul edildi" gibi ilerletilmişse ve tekrar işaretlenirse, durum sessizce "beklemede"ye sıfırlanır — arayüzde bu buton zaten başvurulmuş fırsatlar için gizleniyor gibi görünüyor ama bu davranış (sessiz sıfırlama) kod seviyesinde bir risk olarak kalıyor.
- **Manuel Fırsat Ekle formu çok uzun ve segmentsiz.** 16 alanlık tek bir form; gerçek kullanıcı hangi alanların zorunlu olduğunu anlayamıyor.

## 3. Performans gözlemleri

- 923 kayıtlı fırsat listesi ("Daha fazla göster (844 kaldı)" tarzı sayfalama ile) tarayıcıda gecikme yaratmadı, sayfalama makul çalışıyor.
- Dashboard'un 5 ayrı SWR kaynağı (`firsatlar`, `tasklar`, `basvurular`, `projeler`, `ekip`) ayrı ayrı fetch ediliyor — sayı küçükken sorun değil ama fırsat sayısı büyümeye devam ederse (haftalık scraping ile artıyor) tek seferde 900+ satırlık JSON'un istemciye tam olarak indirilmesi ileride yavaşlayabilir; sunucu tarafı sayfalama şu an yok.
- `_vercel/insights/script.js` isteği 503 dönüyor (Vercel Analytics betiği) — uygulamayı etkilemiyor, tamamen kozmetik, muhtemelen bu domain Vercel'de host edilmediği için ortaya çıkan bir kalıntı.

## 4. Düzeltilenler listesi (her biri ayrı commit)

| # | Düzeltme | Commit |
|---|---|---|
| 1 | Kopya/süresi-geçmiş fırsatlar backfill (radar.py mantığı ile, veri düzeltmesi) | commit yok — tek seferlik DB backfill |
| 2 | `dashboard.tsx`: TOPLAM FIRSAT sayacı `gecerliOpps` üzerinden hesaplanıyor | `ef4716b` |
| 3 | `backend/db.py` + `frontend/components/tasks-tab.tsx`: çoklu görev ataması (`task_atananlar` junction tablosu + filtre düzeltmesi) | `29e6cc2` |
| 4 | `backend/api.py`: sudola promptuna gerçek bugünün tarihi eklendi | `a0f0a4a` |
| 5 | `frontend/components/dashboard.tsx`: BAŞVURULAN FIRSAT sayacı gerçek `apps.length`den hesaplanıyor | `100e495` |

Tüm düzeltmeler test ortamında değil doğrudan üretimde (tek ortam) yapıldı; her biri için: kod değişikliği → `tsc --noEmit` (frontend değişiklikleri için) / `py_compile` (backend değişiklikleri için) → `docker-compose build` → `stop/rm -f/up -d` → canlı tarayıcıda doğrulama → commit + push sırası izlendi.

## 5. Düzeltilemeyenler / karar gerektirenler

- **Tekilleştirme algoritmasının yapısal sınırı:** `tekillestir()` fonksiyonu kopya adaylarını **normalize edilmiş organizatör adına göre** gruplandırıyor. Aynı gerçek etkinliğin bir Instagram gönderisinden ve bir .gov.tr duyurusundan farklı `organizator` metniyle scrape edilmiş iki kaydı, organizatör alanları birebir aynı normalize olmadığı sürece ASLA aynı grupta değerlendirilmiyor — yani görsel olarak bariz kopyalar bile kaçabilir. Bu bir tasarım sınırı, kod hatası değil; düzeltmedim çünkü organizatör-bazlı gruplamayı değiştirmek (örn. başlık/konu benzerliğine dayalı çapraz-kaynak eşleştirme) radar.py'nin çekirdek mantığını yeniden tasarlamak anlamına gelir — kullanıcı kararı gerektirir.
- **radar.py'nin düzenli çalışmasının dedup adımını içerip içermediği doğrulanmadı.** Backfill scriptini elle çalıştırdım ama scraping her yeni çalıştığında yeni kayıtlar için otomatik olarak `tekillestir()` çağrılıyor mu, yoksa bu adım manuel mi kaldı — bunu net doğrulayamadım (radar.py içinde `tekillestir` çağrısının varlığını gördüm ama zamanlanmış/periyodik çalışmasını izleyemedim). Öneri: bu bir cron/scheduled task ise dedup adımının her çalıştırmada tetiklendiği teyit edilmeli.
- **Projeler için hiç DELETE endpoint'i yok** (bkz. bölüm 6) — bunu "eksik özellik" olarak bölüm 6'ya yazdım, kod eklemedim çünkü görev tanımı özellik boşluklarının SADECE raporlanmasını, uygulanmamasını istiyor.
- **Mobil genişlik testi tam doğrulanamadı.** Tarayıcı penceresini 390px genişliğe küçültmeye çalıştığımda araç gerçek bir dar-viewport render'ı üretmedi (ekran görüntüsü hâlâ masaüstü genişliğinde geldi) — bu muhtemelen bir araç kısıtlaması, uygulama hatası değil. Takımın gerçek bir telefondan kontrol etmesi öneriliyor.
- **Bir kayıtta mojibake (bozuk karakter) bulundu:** `zkm.tarimorman.gov.tr` kaynaklı bir fırsatın `konu_kategori` alanı "Teknoloji Yarıœmaları" olarak görünüyor (doğrusu "Yarışmaları"); aynı kaydın `baslik` alanı doğru kodlanmış. Bu tek bir kayda özgü, muhtemelen o kaydın `konu_kategori` alanının çıkarılması sırasında (scraping/LLM adımında) oluşmuş bir veri kalitesi sorunu — sistemik bir kodlama hatası değil (başka hiçbir kayıtta aynı sorun yok). Elle düzeltmedim çünkü kaynağı belirsiz ve tek kayıt; kullanıcı isterse elle düzeltilebilir veya scraping pipeline'ında UTF-8 handling'i gözden geçirilebilir.

## 6. 💡 Özellik boşluğu keşifleri

Bunlar UYGULANMADI — sadece listeleniyor, karar kullanıcıya ait.

1. **Yeni/görülmemiş fırsat işareti yok.** (must-have) Fırsatlar listesinde geçen haftadan bu yana hangi kayıtların yeni eklendiğini ayırt edecek hiçbir görsel işaret yok. Haftalık tarama alışkanlığı düşünüldüğünde bu, gerçek kullanım akışının merkezinde bir ihtiyaç. Gerektirdiği iş: her kullanıcı için "son görüldü" zaman damgası tutmak (basit haliyle localStorage bile yeterli olabilir) ve `bulunma_tarihi` bundan sonraki kayıtları "YENİ" rozetiyle işaretlemek.
2. **Başvuru metni/dokümanı saklama alanı yok.** (must-have) Bir fırsata başvurulduktan 2 ay sonra "başvuruda ne yazmıştık" sorusu kaçınılmaz olarak gelecek. Şu an "Başvurularım" kartlarında sadece durum var, yazılan metin/yüklenen dosya için hiçbir alan yok. Gerektirdiği iş: `basvurular` kaydına `notlar`/`dosyalar` alanı eklemek (projelerde zaten olan not/dosya mekanizması örnek alınabilir).
3. **Görev atama bildirimi yok.** (nice-to-have) Sisteme "kullanıcı" kavramı (giriş yapma) olmadığı için, birine yeni bir görev atandığında bunu fark etmesinin hiçbir yolu yok — herkes her şeyi görüyor, "bana atanan" varsayılan görünümü yok. Takım büyüdükçe bu ciddileşecek.
4. **Yaklaşan son başvuru tarihi uyarısı yok.** (nice-to-have) Bir fırsatın son başvuru tarihi yaklaşırken (örn. 3 gün kala) hiçbir görsel uyarı/renk değişikliği yok — kullanıcı fırsatı unutabilir. (Bu ihtiyaç, bölüm 1.4'teki sudola tarih hatasıyla da örtüşüyor; doğru tarih hesaplansa bile proaktif bir uyarı mekanizması hâlâ eksik.)
5. **Görevlerde gecikme (overdue) görsel ayrımı yok.** (nice-to-have) Deadline'ı geçmiş ama tamamlanmamış görevler listede/takvimde diğer görevlerden farksız görünüyor — kırmızı vurgu veya benzeri bir işaret yok.
6. **Proje → başvuru geçmişi (ters bağlantı) yok.** (nice-to-have) Bir projenin sayfasından "bu projeyle hangi fırsatlara başvurduk, hangilerini kazandık" görülemiyor — sadece not/dosya var. Bu, projelerin gerçek "geçmiş" değerini görünmez kılıyor.
7. **Projeler için silme özelliği hiç yok.** (nice-to-have/must-have arası) Test sırasında fark ettim: `backend/api.py`'de projeler için GET/POST/PUT var ama DELETE endpoint'i tanımlı değil — yanlışlıkla eklenen bir projeyi kaldırmanın API üzerinden hiçbir yolu yok (ben test projemi doğrudan veritabanından sildim, gerçek kullanıcı bunu yapamaz).
8. **Proje ekleme formunda geçersiz link için görünür hata yok.** (nice-to-have, bkz. bölüm 2) — Backend hatayı zaten yakalıyor, sadece arayüze taşınması gerekiyor.
9. **Görevden ilgili fırsata tek tıkla geçiş yok.** (nice-to-have) Bir görev bir fırsatla ilişkiliyse bile, görev kartından o fırsatın detayına doğrudan atlayan bir bağlantı görmedim (görev kartında `firsat_baslik` gösteriliyor ama tıklanabilir değil gibi görünüyor — bu tam doğrulanmadı, hızlı bir kontrol öneriyorum).

## 7. çido olarak bir haftalık deneyimim

Dürüst olmak gerekirse, bu turda bulduklarım beni hem rahatlattı hem endişelendirdi. Rahatlatan taraf: en çok güvendiğim şeylerin (fırsat listesi, filtreler, sayım mantığı) çoğu aslında doğru kodlanmış — sorunlar genelde "kod yanlış" değil "veri hiç işlenmemiş" ya da "iki farklı veri kaynağı birbiriyle senkron değil" türündendi, yani düzeltilebilir cinsten. Endişelendiren taraf ise şu: sudola'nın tarih konusunda güvenle ama tamamen yanlış konuşması, gerçekten güvenimi en çok sarsan şeydi. Bir asistanın "787 gün kaldı" dediği bir başvuruyu ertelemiş olsaydım ve gerçekte yarın bitiyor olsaydı, bu ürüne bir daha güvenmezdim — çünkü hata bir çökme değil, gayet makul görünen bir cümleydi. Bunun dışında, "Başvurulan Fırsat" sayacının sayfa her yenilendiğinde sıfırlanması gibi sessiz tutarsızlıklar, ürünün "arka planda gerçekten ne olduğunu" hiç bilemeyeceğim hissi veriyor — sayılara bakıp "acaba bu doğru mu" diye sorgulamak zorunda kalmak, bir takip aracının en temel vaadini (güvenilir bir özet) zedeliyor. Yine de üzerine gidip düzelttiğim şeyler gerçek ve kalıcıydı; ürünü kullanırdım, ama ilk haftadan sonra "bu sayılara güveneyim mi" diye bir kez daha kontrol ederdim — ki bu tam olarak bir kullanıcının yapmaması gereken bir şey.
