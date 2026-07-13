# QA Envanteri - SudoQu (13 Temmuz 2026)

Bu dosya koda bakilarak (opportunities-tab.tsx, applications-tab.tsx, tasks-tab.tsx, projeler-tab.tsx, sudola-panel.tsx, dashboard.tsx, lib/api.ts, backend/api.py) cikarilan gercek kullanici yolculuklari envanteridir. Asama 2'de her biri 8001/3001 test ortaminda fiilen test edilecektir.

## 1. Firsatlar Sekmesi
* Listeleme: GET /firsatlar -> getOpportunities() -> kart listesi. (Koda gore VAR)
* Arama: metin kutusu (Firsat ara - baslik ya da baglanti), setQuery ile filtreleme. (Koda gore VAR)
* Siralama: dropdown (SiralamaTuru, varsayilan son_basvuru). (Koda gore VAR)
* Filtre: maliyet durumuna gore (seciliMaliyetler.has), suresi gecmis/duplicateOf gizleme. (Koda gore VAR)
* Veri Alani paneli: 13 alan tanimli lib/api.ts Opportunity arayuzunde. (Koda gore VAR)
* Basvur olarak isaretle: onApplied callback -> dashboard.tsx handleApplied -> markApplied(link) [POST /basvurular/{link}] + applications.mutate(). (Koda gore VAR ama asagida KRITIK BUG bulundu)
* Coklama gizleme: duplicateOf alanina gore filtreleniyor. (Koda gore VAR)
* sudola butonu: acildiginda SudolaPanel render ediliyor, bu QA turunda YENI Gemini cagrisi yapilmayacak.

## 2. Basvurularim Sekmesi
* Listeleme: GET /basvurular -> getApplications() -> kart listesi.
* [KRITIK BUG - KOK NEDEN KOD OKUMASIYLA BULUNDU] Backend GET /basvurular (api.py satir 51-52) dosya_oku(BASVURULAR_DOSYA, {}) donduruyor - yani link'e gore anahtarlanmis bir DICT donuyor ({"https://...": {baslik, link, durum}, ...}), ARRAY DEGIL. Frontend getJson() (lib/api.ts satir 79-92) once Array.isArray(data) kontrol ediyor (false donuyor), sonra data icinde ["data","items","results","firsatlar","tasklar","basvurular"] anahtarlarindan birinin array olup olmadigina bakiyor - ama basvurular.json'daki anahtarlar firsat linkleridir, literal "basvurular" stringi degil. Hicbir kosul saglanmadigi icin getJson SESSIZCE bos array donduruyor. Sonuc: POST /basvurular/{link} basariyla calisiyor ve basvurular.json'a doguru yaziyor (backend dogru), ama Basvurularim sekmesi HER ZAMAN "Henuz basvurun yok" bos durumunu gosteriyor - kac tane basvuru isaretlenirse isaretlensin. Bu bir yaris durumu (race condition) DEGIL, backend/frontend veri sozlesmesi (contract) uyusmazligidir - GET /basvurular obje donduruyor, frontend dizi bekliyor.
* Onerilen duzeltme (Asama 3'te uygulanacak): backend'de basvurulari_getir() fonksiyonunu list(dosya_oku(BASVURULAR_DOSYA, {}).values()) donduracek sekilde degistirmek - tek satirlik, POST tarafini etkilemeyen, geriye donuk uyumlu bir duzeltme.
* Durum degistirme / geri donus linki: applications-tab.tsx sadece salt-okunur kart listesi (49 satir) - durum degistirme veya firsata geri donme linki YOK, sadece dis baglanti (href=a.link) var.

## 3. Task & Takvim Sekmesi
* Listeleme: GET /tasklar -> getTasks() -> kart listesi. (Koda gore VAR)
* Tamamlandi isaretleme: PUT /tasklar/{id}/tamamla + optimistic mutate (dashboard.tsx handleCompleted). (Koda gore VAR, calisiyor gorunuyor - Asama 2'de dogrulanacak)
* [EKSIK - INSA EDILECEK] Gorev olusturma arayuzu YOK. Backend'de POST /tasklar (task_ekle: baslik, atanan, tur, deadline) MEVCUT ama tasks-tab.tsx'te (141 satir, sadece 4 useState/atanan/deadline referansi var) hicbir form/input/create-button yok. Sadece dashboard.tsx'te salt-okunur kart listesi render ediliyor.
* [EKSIK - INSA EDILECEK] Gorev duzenleme arayuzu YOK. Backend'de PUT /tasklar/{id} (genel duzenleme, sadece tamamla degil) da YOK - sadece PUT /tasklar/{task_id}/tamamla var. Duzenleme icin hem backend PUT endpoint hem frontend form gerekiyor.
* [EKSIK - INSA EDILECEK] Kisiye gore gorunum/filtre YOK. tasks-tab.tsx sadece t.atanan degerini salt-okunur meta alani olarak gosteriyor (satir 85), ekip.json'daki kisilere gore filtre/sekme/tab yok. Backend GET /ekip zaten mevcut, kisi listesini saglayabilir.
* Silme: backend'de DELETE /tasklar/{id} yok, frontend'de de silme butonu yok - gereksinim netlestirilmeli.

## 4. Projelerimiz Sekmesi
* Backend tam CRUD: GET/POST /projeler, PUT /projeler/{id}, POST /projeler/{id}/not, POST /projeler/{id}/dosya (yukleme), GET /projeler/{id}/dosya/{ad} (indirme). (Koda gore VAR - item 8'de yapildi)
* [YENIDEN TEST GEREKLI] Onceki test turunda (item 8) yanlis portlar kullanilmisti (ORTAM_REHBERI.md oncesi). Asama 2'de DOGRU portlarla (backend curl 8001, frontend tarayici 3001) yeniden dogrulanacak: proje olusturma, duzenleme, not ekleme, dosya yukleme/indirme.

## 5. sudola
* Sohbet arayuzu (sudola-panel.tsx): POST /sudola/soru - Tavily arastirma + Gemini yapilandirilmis yanit. (item 9'da TAMAMLANDI, canli test basarili - bkz. /tmp/test_sudola_out.txt gece calismasi)
* Proje Uygunluk Onerisi: GET /sudola/oneri/{link} - skor/aciklama/guclu_yonler/riskler. (item 9'da TAMAMLANDI)
* Bu QA turunda: SADECE panelin acilip kapanmasi ve onceki (gece testinden kalma) yanitlarin dogru render edilmesi kontrol edilecek - YENI Gemini cagrisi YAPILMAYACAK.

## 6. Ozet - Asama 3 Oncelik Sirasi
1. [GERCEK BUG - backend contract duzeltmesi] GET /basvurular dict yerine array donsun.
2. [EKSIK CORE CRUD UI] Gorev olusturma formu (frontend) - backend zaten hazir.
3. [EKSIK CORE CRUD UI] Gorev duzenleme (backend PUT /tasklar/{id} + frontend form).
4. [EKSIK CORE CRUD UI] Kisi bazli gorev gorunumu/filtresi.
5. [KOZMETIK/DOGRULAMA] Projelerimiz dogru portlarda yeniden test, sudola UI acilma/render dogrulamasi.
