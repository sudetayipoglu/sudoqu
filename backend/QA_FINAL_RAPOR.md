# SudoQu QA Raporu — Aşama 5 (Final)

QA görevi kapsamı: "Dünyanın en titiz iş analisti ve QA mühendisi gibi davran" talimatıyla başlatılan 6 aşamalı bağımsız doğrulama turu. Bu turda hiçbir yeni canlı Gemini (sudola) çağrısı yapılmadı; sadece mevcut arayüzün açılıp kapandığı doğrulandı.

Ortam kuralı (her bulguda geçerli): TEST = backend 127.0.0.1:8001 (sadece SSH-terminal curl), 3001 (tarayıcı, ama API_BASE sabit olduğu için veri PRODUCTION 8000'den gelir). PRODUCTION = backend 8000, frontend 3000 (gerçek kullanıcı erişimi).

---

## 1) Aşama -1 — Önceki Segmentten Devreden Kök Neden ve Düzeltme

Bu QA turu başlamadan önce production frontend (port 3000) çökme döngüsündeydi. Kök neden: `next start` moduna geçişten sonra `.next` build dizini eksik/yarım kalmıştı (`_app.js`, `_document.js`, `_error.js`, hata sayfaları eksikti). Düzeltme: `sudo systemctl stop sudoqu-frontend && rm -rf .next && pnpm run build` ile temiz bir build alındı, gerekli tüm shim dosyalarının (`_app.js`, `_document.js`, `_error.js`, `404.html`, `500.html`) üretildiği doğrulandıktan sonra servis yeniden başlatıldı. Bu düzeltme bu QA turunun ÖNCESİNDE tamamlanmıştı; bu turda sadece kalıcı olduğu yeniden teyit edildi.

---

## 2) QA_ENVANTER.md ve QA_TEST_SONUCLARI.md Özeti

**QA_ENVANTER.md** (kod incelemesiyle, hiçbir test yapılmadan önce hazırlandı): Fırsatlar sekmesinin tüm alt-özellikleri (listeleme, arama, sıralama, filtre, veri alanı, başvur-işaretle, çoklama-gizleme, sudola-butonu) kodda VAR olarak doğrulandı. Başvurularım sekmesinde KRİTİK bir senkron hatasının kök nedeni kod okumasıyla ÖNCEDEN teşhis edildi (backend dict döndürüyor, frontend generic-unwrap sadece belirli anahtarları arıyor, hiçbiri eşleşmediği için sessizce boş dizi dönüyordu). Task & Takvim'de görev oluşturma/düzenleme arayüzü ve kişi bazlı görünümün EKSİK olduğu, backend'de PUT /tasklar/{id} endpoint'inin bulunmadığı teyit edildi. Projelerimiz'de backend CRUD'ın tam olduğu ama doğru portlarda yeniden test edilmesi gerektiği not edildi.

**QA_TEST_SONUCLARI.md** (fiili test sonuçları): Backend'in 14 endpoint'i TEST ortamında (127.0.0.1:8001, SSH-terminal curl) tek tek doğrulandı. Ayrıca kritik bir YENİ bulgu ortaya çıktı: production backend 21 saattir yeniden başlatılmamıştı, bu yüzden /projeler ve /sudola/oneri production'da 404 veriyordu (kod repo'da vardı ama çalışan process eskiydi). Frontend'de (test 3001, veri production 8000'den) dashboard sayaç hataları canlı doğrulandı, ayrıca ikinci bir hata (görev tamamlama rozetinin hep "tamamlanmadı" göstermesi) bu aşamada keşfedildi. Projelerimiz sekmesi bu aşamada production'ın bayat olması nedeniyle doğrulanamadı olarak işaretlendi (Aşama 4'te çözüldü, aşağıya bakınız).

---

## 3) Bulunan ve Düzeltilen Sorunlar — Sayım

- **2 gerçek hata** bulundu ve düzeltildi: (1) `/basvurular` endpoint'i dict döndürüyordu, frontend array bekliyordu → backend artık `list(...values())` döndürüyor. (2) Görev tamamlama rozeti backend alan adlarıyla uyuşmuyordu → frontend artık `durum` alanını da kontrol ediyor.
- **3 eksik arayüz** bulundu ve inşa edildi: görev oluşturma formu, görev düzenleme formu (+ backend PUT /tasklar/{id} endpoint'i), kişiye göre filtre (ekip listesi çekilerek).
- **1 deployment açığı** bulundu ve giderildi: production backend 21 saattir bayattı, yeniden başlatılarak güncel koda geçirildi.

Toplam: 2 hata + 3 eksik özellik + 1 deployment açığı = 6 bulgu, 6'sı da düzeltildi/tamamlandı.

---

## 4) Modül Bazlı Kullanıcı Yolculuğu Anlatımı (Doğrulanmış, PRODUCTION üzerinde)

**Fırsatlar:** Kullanıcı ana sayfaya girer → 733 gerçek fırsat listelenir → arama kutusuna yazdığında liste anlık filtrelenir → sıralama seçeneğine tıkladığında (yeni/deadline) liste yeniden sıralanır → bir fırsat kartına tıkladığında detay paneli açılır (13 veri alanı görünür) → "Başvur olarak işaretle" butonuna tıkladığında fırsat Başvurularım'a taşınır ve dashboard'daki "BAŞVURU" sayacı anlık artar.

**Başvurularım:** Kullanıcı sekmeye tıklar → artık (düzeltme sonrası) gerçek 5 başvuru doğru şekilde listelenir, her biri başlık/link/"Beklemede" rozetiyle görünür — düzeltme öncesi bu sekme her zaman boş görünüyordu, kullanıcı başvurduğu hiçbir şeyi göremiyordu.

**Task & Takvim:** Kullanıcı sekmeye tıklar → görevler kişi filtresi çipleriyle (Tümü/sudo/yeno/çido) birlikte görünür → "Yeni Görev" butonuna tıkladığında form açılır, başlık/atanan/tür/deadline girip kaydettiğinde görev anlık listeye eklenir → mevcut bir görevin yanındaki kalem ikonuna tıkladığında satır içi düzenleme formu açılır, değiştirip kaydettiğinde PUT isteğiyle güncellenir → bir görevi tamamla butonuna tıkladığında (düzeltme sonrası) rozet doğru şekilde yeşil "Tamamlandı" işaretine döner — düzeltme öncesi bu rozet hep "tamamlanmadı" gösteriyordu.

**Projelerimiz:** Kullanıcı sekmeye tıklar → gerçek "SudoQu" proje kartı görünür (GitHub reposuna bağlı, "Tamamlandı" durumu, "1 not, 1 dosya" özet bilgisiyle) → karta tıkladığında detay modalı açılır, not geçmişi ve dosya listesi görünür, durum değiştirilebilir, yeni not/dosya eklenebilir. Bu sekme Aşama 2'de production'ın bayat olması nedeniyle doğrulanamamıştı; Aşama 4'te production backend yeniden başlatıldıktan sonra PRODUCTION tarayıcısında gerçek veriyle tam olarak doğrulandı.

**sudola:** Kullanıcı bir fırsatın detayında "sudola" panelini açar → fırsatın 13 alanı (yer/mekan, ödül, katılım şartları, vb.) panelde görünür, "sudola" butonu (soru sorma/öneri alma) görünür durumda ve tıklanabilir haldedir. Bu QA turunun kesin kısıtı gereği butona tıklanıp yeni bir Gemini çağrısı YAPILMADI — sadece panelin production'da doğru açıldığı ve önceki oturumlardan kalma canlı verinin doğru render edildiği görsel olarak doğrulandı.

---

## 5) Bekleyen Kullanıcı Kararları (Bu QA Turunun Kapsamı Dışında)

- **Madde 6 — Tavily site: sorgu kotası hesaplaması** üç senaryo olarak daha önce hesaplanmıştı: Senaryo A (düz ekleme) ~485 çağrı/ay, Senaryo B (sadece Türkçe anahtar kelimelere) ~724 çağrı/ay, Senaryo C (tüm 9 dil bloğuna) ~2.782 çağrı/ay. Hangi senaryonun uygulanacağına dair karar hâlâ kullanıcıdan bekleniyor.
- **Docker/production cutover onayı** hâlâ bekleniyor — bu QA turunda da (önceki tur gibi) Docker container'larının gerçek devreye alınması veya systemd servislerinin durdurulması KESİNLİKLE yapılmadı.

---

## 6) Ortam Etiketleme Notu

Bu raporda ve QA_TEST_SONUCLARI.md'de geçen her sonuç açıkça TEST (8001/3001) veya PRODUCTION (8000/3000) olarak etiketlendi. Aşama 3'teki tüm düzeltmeler önce TEST ortamında doğrulandı, sadece TEST'te doğrulananlar Aşama 4'te PRODUCTION'a alındı ve orada ayrıca yeniden doğrulandı.
