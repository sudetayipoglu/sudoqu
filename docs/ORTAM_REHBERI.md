# SudoQu Ortam Rehberi (KESIN REFERANS)

## GUNCEL DURUM (14 Temmuz 2026 itibariyle - FAZ B tamamlandi)
Production artik systemd degil, docker-compose ile calisiyor. Asil veri kaynagi PostgreSQL'dir.

## PRODUCTION (canli, gercek kullanici erisimi - dikkatli davran)
| | Backend | Frontend | Postgres |
|---|---|---|---|
| Port | 8000 | 3000 | 5432 (sadece container-ici aga acik, disaridan erisilemez) |
| Calistirma yontemi | docker-compose (servis: backend) | docker-compose (servis: frontend) | docker-compose (servis: postgres) |
| Compose dosyasi | ~/sudoqu/docker-compose.yml (uc servis de ayni dosyada) |
| Kod yolu | ~/sudoqu/backend | ~/sudoqu/frontend | named volume: postgres_data |
| Disaridan (tarayici) erisim | EVET, firewall acik | EVET, firewall acik | HAYIR |
| Veri kaynagi | PostgreSQL (DATABASE_URL set, dosya_oku/dosya_yaz otomatik Postgres'e yonleniyor) |
| JSON dosyalari (firsatlar.json, tasklar.json, basvurular.json, projeler.json) | ARTIK CANLI GUNCELLENMIYOR - sadece migration ani fallback/referans, tarihi (donuk) veri iceriyorlar, SILINMEDILER |
| Ne zaman dokunulur | SADECE test ortaminda dogrulanmis, onaylanmis degisiklik canliya alinirken |

## ESKI SYSTEMD SERVISLERI (FAZ B ile devre disi birakildi - SILINMEDI, sadece acil rollback icin duruyor)
| | Backend | Frontend |
|---|---|---|
| systemd servisi | sudoqu-backend | sudoqu-frontend |
| Durum | inactive + disabled (boot'ta kendiliginden baslamaz) |
| Ne zaman kullanilir | SADECE docker-compose stack'i ciddi bicimde bozulursa acil rollback icin |
| Veri kaynagi (rollback sirasinda) | JSON dosyalari (DATABASE_URL set degil) - migration sonrasi Postgres'e giren yeni veriyi ICERMEZ, bu yuzden gercek bir "geri don" degil, gecici acil onlemdir |

## Rollback prosedurü (production'da ciddi sorun cikarsa)
1. `cd ~/sudoqu && sudo docker-compose down`
2. `sudo systemctl start sudoqu-backend sudoqu-frontend`
3. Dogrula: `sudo systemctl is-active sudoqu-backend sudoqu-frontend` (ikisi de "active" donmeli)
4. NOT: Bu adim, Postgres'e gectikten sonra girilen veriyi JSON'a yansitmaz - sadece "eski sisteme gecici don" onlemidir. Kalici cozum icin sorunu docker-compose tarafinda coz ve tekrar `docker-compose up -d` ile geri don.

## Yedekleme (guncellendi - pg_dump eklendi)
- Cron: `0 3 * * * ~/sudoqu/backend/yedekle.sh`
- Script artik iki seyi birden yapiyor: (1) eski JSON kopyalama adimi - geriye donuk referans, artik canli veri degil (2) gercek `pg_dump -U sudoqu sudoqu` ciktisi, `~/sudoqu-backups/postgres_TARIH.sql` olarak. **Asil geri yuklenebilir yedek pg_dump'tir.**
- 7 gunden eski hem .json hem .sql yedekleri otomatik silinir.
- Log: `~/sudoqu-backups/yedekleme_log.txt`
- 17 Temmuz 2026: `yedekle.sh` icindeki `sudo docker-compose` satirinin AYNI sudo-sifre sorunu yasadigi kesfedildi - 15/16/17 Temmuz gecelerinde (3 gun) pg_dump SESSIZCE basarisiz olmustu (sadece JSON kopyalari alinmisti, gercek DB yedegi YOKTU). Duzeltme: sudo kaldirildi, `docker-compose` -> `docker compose` (v2) yapildi. Ayni gun manuel calistirilip basarili pg_dump dogrulandi.

## radar.py cron'u (guncellendi - artik container icinde calisiyor)
- Onceki: host'taki venv ile `venv/bin/python3 radar.py` calisiyordu (JSON dosyalarina yaziyordu).
- Simdi: `docker compose -f ~/sudoqu/docker-compose.yml exec -T backend python3 radar.py` (Cuma 09:00 UTC, sudo YOK - asiyesudetayipoglu docker grubunda) - container icinde DATABASE_URL gorup dogrudan Postgres'e yaziyor.
- Log: `~/sudoqu/backend/radar_log.txt` (degismedi).
- 17 Temmuz 2026: Cron'da `sudo docker-compose` calisirken "sudo: a password is required" hatasiyla sessizce cok haftadir calismadigi kesfedildi. Duzeltme: crontab'dan sudo kaldirildi, kullanici docker grubuna eklendi (`usermod -aG docker`). Ayrica ayni anda iki radar.py cron satiri oldugu (biri eski venv tabanli, biri docker tabanli, ayni flock kilidini paylasiyorlardi) fark edildi, eski venv satiri silindi. Ayni gun gercek cron tetiklenmesiyle (09:00 UTC) uctan uca dogrulandi: sudo hatasi yok, docker exec calisiyor, ulke taramasi basladi.
- 17 Temmuz 2026 (ayni gun, ikinci duzeltme): `docker-compose` v1.29.2 tamamen kaldirilip `docker-compose-plugin` (v2) kuruldu, crontab'daki komut `docker-compose` -> `docker compose` yapildi (tireli komut artik sistemde YOK). Sebep: v1'in bilinen 'KeyError: ContainerConfig' recreate hatasi - bkz. KESIN KURALLAR 7/8.

## KESIN KURALLAR (bunlari ihlal etme)
1. Production'a (docker-compose, 8000/3000) degisiklik yapmadan once test ortaminda dogrulanmis olmali.
2. systemd servislerini (sudoqu-backend, sudoqu-frontend) SILME - disabled kalmalilar, sadece acil rollback icin duruyorlar.
3. JSON veri dosyalarini SILME - fallback/referans olarak kalmalilar, DATABASE_URL yoksa hala kullanilirlar (ornegin lokal gelistirmede).
4. Postgres sifresini (~/sudoqu/.env icindeki POSTGRES_PASSWORD) ve API anahtarlarini (~/sudoqu/backend/.env) asla loglama veya commit etme.
5. `docker-compose.yml`'de port degisikligi yapmadan once hangi ortamda oldugunu (test mi production mu) acikca belirle - production portlari HER ZAMAN 8000/3000 olmali.
6. 17 Temmuz 2026: `docker-compose` v1.29.2 (legacy binary) TAMAMEN KALDIRILDI (apt-get remove --purge). Yerine resmi Docker deposundan `docker-compose-plugin` (v2) kuruldu. ARTIK SADECE `docker compose` (TIRESIZ, iki kelime) kullanilmali - tireli `docker-compose` komutu sistemde YOK. Tum scriptler (crontab, extraction_backfill_supervisor.py, yedekle.sh) guncellendi.
7. [COZULDU - 17 Temmuz 2026] Eskiden bir servisin volume/config'i degisip `docker-compose up -d` "KeyError: 'ContainerConfig'" hatasi veriyordu (v1.29.2 + yeni Docker Engine uyumsuzlugu). v2'ye gecisle sorun ortadan kalkti, `docker compose up -d <servis>` artik direkt calisir. Test ortaminda gercek build+recreate ile dogrulandi.

---
## ESKI NOT (13 Temmuz 2026 - FAZ A test asamasinda yazildi, artik guncel degil, tarihsel referans icin birakildi)
O donemde 8001/3001 "test ortami", 8000/3000 ise systemd tabanli "production" idi. 14 Temmuz 2026'da yapilan FAZ B ile bu ayrim degisti: 8000/3000 artik docker-compose'un kendisidir, systemd devre disi. Asagidaki eski notlar sadece o donemin firewall/port test surecini anlamak icin saklaniyor.

# SudoQu Ortam Rehberi (KESIN REFERANS) [ESKI]

## PRODUCTION (canli, gercek kullanici erisimi - dikkatli davran) [ESKI - systemd donemi]
| | Backend | Frontend |
|---|---|---|
| Port | 8000 | 3000 |
| systemd servisi | sudoqu-backend | sudoqu-frontend |
| Dosya yolu | ~/sudoqu/backend | ~/sudoqu/frontend |
| Disaridan (tarayici) erisim | EVET, firewall acik | EVET, firewall acik |
| Ne zaman dokunulur | SADECE test ortaminda dogrulanmis, onaylanmis degisiklik canliya alinirken |

## TEST (deneme ortami - canliyi etkilemez, serbestce kullan) [ESKI]
| | Backend | Frontend |
|---|---|---|
| Port | 8001 | 3001 |
| Disaridan (tarayici) erisim | HAYIR - firewall kapali, SADECE SSH-terminal icinden curl http://localhost:8001/... ile test edilir | EVET - firewall acik, dogrulanmis. Hem curl http://localhost:3001 hem gercek tarayicidan http://34.30.225.219:3001 ile test edilebilir |

## Ek not - port 3001 (13 Temmuz 2026, ~06:55 UTC teshisi) [ESKI]
3001 portu SUREKLI acik bir servis degildir, sadece aktif test sirasinda bir process baslatildiginda dinler. Test bitince port kapanir, bu normaldir.
