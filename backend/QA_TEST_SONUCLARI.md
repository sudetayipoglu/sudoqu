# QA Test Sonuclari - SudoQu (13 Temmuz 2026)

Test yontemi: backend uctan uca curl ile 127.0.0.1:8001 (izole, sadece SSH terminalden), frontend tarayici ile 34.30.225.219:3001 (Next.js dev sunucusu, API_BASE kodda halen production 8000'e sabit oldugu icin bu sekmedeki veri cagrilari fiilen production backend'e gidiyor - asagida her sonucta ortam acikca belirtilmistir). Test sonunda olusturulan tum test verileri (1 gorev, 1 proje, 1 basvuru) JSON dosyalarindan temizlendi.

## KRITIK YENI BULGU: Production backend 21 saattir yeniden baslatilmamis
systemctl status sudoqu-backend -> "Active: active (running) since Sun 2026-07-12 11:14:48 UTC; 21h ago". Bu, item 8 (Projelerimiz) ve item 9 (sudola) kodlari git'e commit edilmeden ONCE baslamis bir process. Python/uvicorn --reload olmadigi icin degisiklikler diskte olsa da calisan process'e yansimiyor. Kanit (ortam: PRODUCTION, localhost:8000 uzerinden curl): GET /projeler -> 404, GET /sudola/oneri/test -> 404, GET /basvurular -> 200 (OK, bu endpoint eskiden beri var), GET /tasklar -> 200 (OK). Yani su an gercek production'da Projelerimiz ve sudola ozellikleri TAMAMEN calismiyor - sadece servisin yeniden baslatilmasi (kod degisikligi gerekmiyor) yeterli. Bu Asama 4'te ele alinacak.

## Backend Endpoint Testleri (ortam: TEST, 127.0.0.1:8001)
* GET / -> PASS ({"durum":"SudoQu API calisiyor"})
* GET /firsatlar -> PASS (733 kayit, dizi olarak donuyor)
* GET /basvurular -> FAIL (kok neden asagida) - dict donuyor, dizi degil
* POST /basvurular/{link} -> PASS - basvuru sayisi 5'ten 6'ya cikti, dogru yazildi
* GET /tasklar -> PASS (dizi olarak donuyor)
* POST /tasklar -> PASS - yeni gorev basariyla olusturuldu (id 3 atandi)
* PUT /tasklar/{id}/tamamla -> PASS - durum "bekliyor"dan "tamamlandi"ya gecti
* GET /ekip -> PASS (3 kisi: sudo, yeno, cido)
* GET /projeler -> PASS (dizi olarak donuyor, TEST ortaminda - production'da 404, yukarida aciklandi)
* POST /projeler -> PASS - proje basariyla olusturuldu
* POST /projeler/{id}/not -> PASS - not basariyla eklendi
* POST /projeler/{id}/dosya -> PASS (izin verilen uzanti ile, ornegin .png) - .txt dogru sekilde reddedildi ("Desteklenmeyen dosya turu" - bu bir bug degil, bilincli bir validasyon)
* GET /projeler/{id}/dosya/{ad} -> PASS - yuklenen dosya byte-byte ayni sekilde indirildi
* PUT /projeler/{id} -> PASS - durum guncellendi

## Frontend Tarayici Testleri (ortam: TEST frontend 3001, veri gercekte PRODUCTION 8000 uzerinden geliyor - kod API_BASE'i hala prod'a sabit)
* Firsatlar listeleme, arama kutusu, siralama, filtre etiketleri, kart gorunumu -> PASS (733 kayit dogru render edildi)
* Veri Alani detay paneli (13 alan) -> PASS - tum alanlar dogru render edildi
* sudola butonu ve panel acilma/kapanma -> PASS - panel dogru aciliyor, "Sorunu yaz..." input'u ve "Proje Uygunluk Onerisi Al" butonu goruntuleniyor. Hicbir Gemini cagrisi tetiklenmedi (mesaj yazilmadi/gonderilmedi, oneri butonu tiklanmadi).
* Dashboard ozet sayaclari ("BASVURU", "BASVURULAN FIRSAT") -> FAIL - ikisi de 0 gosteriyor, gercekte 6 basvuru var. Bolum 2'deki (Basvurularim) kok nedenle ayni.
* Basvurularim sekmesi -> FAIL - "Henuz basvurun yok" gosteriyor, 6 gercek basvuru varken. KOK NEDEN (kod + curl ile dogrulandi): backend GET /basvurular dict donduruyor, frontend dizi bekliyor, getJson sessizce [] donduruyor.
* Task & Takvim listeleme -> PASS gorunum olarak, ama asagida ikinci bir bug bulundu
* [YENI BULUNAN BUG] "AÇIK GÖREV" sayaci ve gorev karti "Tamamlandi isaretle" butonu -> FAIL. Ayni aile hatasi: backend "durum" alaninda string tutuyor ("bekliyor"/"tamamlandi"), frontend ise "tamamlandi" adinda bir BOOLEAN alan bekliyor (pickBool ile obj["tamamlandi"] veya obj["tamamlandı"] anahtarini ariyor) - byle bir anahtar ham veride hic yok, bu yuzden pickBool her zaman false donduruyor. Sonuc: tamamlanmis gorevler bile ust kosede yesil "Tamamlandi" rozeti gosterse de (bu StatusBadge dogrudan "durum" stringini kullaniyor, dogru calisiyor), alt taraftaki mavi buton hep "Tamamlandi isaretle" yaziyor - hicbir zaman check-mark/pasif duruma gecmiyor. Dashboard'daki "AÇIK GOREV" sayaci da bu yuzden yanlis: gercekte 1 acik gorev varken 3 (tum gorev sayisi) gosteriyor. Canli dogrulama: tarayicida 3 gorev karti da (1 gercekten tamamlanmis, 1 acik, 1 QA test - tamamlanmis) hepsi ayni aktif mavi "Tamamlandi isaretle" butonunu gosterdi.
* Projelerimiz sekmesi -> EKSIK/DOGRULANAMADI - bu tarayici oturumu production backend'e (8000) bagli oldugu icin ve production'da /projeler 404 verdigi icin "Henuz proje eklenmedi" gosterdi. Backend kodu kendisi TEST ortaminda (8001, yukaridaki bolum) ayrica dogrulandi ve PASS. Gercek uctan uca UI dogrulamasi ancak Asama 4'te production backend yeniden baslatildiktan sonra yapilabilir.

## EKSIK Kalan Ozellikler (QA_ENVANTER.md'de zaten listelendi, burada teyit)
* Gorev olusturma formu (frontend) - EKSIK, backend hazir.
* Gorev duzenleme (hem backend PUT /tasklar/{id} hem frontend form) - EKSIK.
* Kisi bazli gorev gorunumu/filtresi - EKSIK.

## Asama 3 Oncelik Sirasi (guncel, iki bug ile)
1. [GERCEK BUG] GET /basvurular - dict yerine array donsun.
2. [GERCEK BUG - YENI] Task tamamlanma durumu - frontend'in "tamamlandi" boolean beklentisi ile backend'in "durum" string alani arasindaki uyusmazlik duzeltilsin (frontend tarafinda durum stringine gore hesaplama yapmak en az riskli duzeltme).
3. [EKSIK CORE CRUD UI] Gorev olusturma formu.
4. [EKSIK CORE CRUD UI] Gorev duzenleme (backend + frontend).
5. [EKSIK CORE CRUD UI] Kisi bazli gorev gorunumu/filtresi.
6. [DEPLOYMENT - KOD DEGISIKLIGI GEREKTIRMEZ] Production backend servisi yeniden baslatilsin (systemctl restart sudoqu-backend) - Projelerimiz ve sudola'yi production'da aktif hale getirir.
