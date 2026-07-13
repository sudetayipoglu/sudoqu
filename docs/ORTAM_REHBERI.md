# SudoQu Ortam Rehberi (KESIN REFERANS)

## PRODUCTION (canli, gercek kullanici erisimi - dikkatli davran)
| | Backend | Frontend |
|---|---|---|
| Port | 8000 | 3000 |
| systemd servisi | sudoqu-backend | sudoqu-frontend |
| Dosya yolu | ~/sudoqu/backend | ~/sudoqu/frontend |
| Disaridan (tarayici) erisim | EVET, firewall acik | EVET, firewall acik |
| Ne zaman dokunulur | SADECE test ortaminda dogrulanmis, onaylanmis degisiklik canliya alinirken |

## TEST (deneme ortami - canliyi etkilemez, serbestce kullan)
| | Backend | Frontend |
|---|---|---|
| Port | 8001 | 3001 |
| Disaridan (tarayici) erisim | **HAYIR** - firewall kapali, SADECE SSH-terminal icinden `curl http://localhost:8001/...` ile test edilir | **EVET** - firewall acik, dogrulanmis. Hem `curl http://localhost:3001` hem gercek tarayicidan `http://34.30.225.219:3001` ile test edilebilir |

## KESIN KURALLAR (bunlari ihlal etme)
1. Backend'i test ederken SADECE port 8001 kullan. 8002, 8003 gibi baska portlar DENEME - bosuna zaman kaybedersin, hicbiri firewall'da acik degil ve backend'in zaten disaridan (tarayicidan) dogrudan erisilmesine gerek yok (frontend sunucu-tarafli ona baglaniyor).
2. Frontend'i disaridan (tarayici) test etmen gerekiyorsa SADECE port 3001 kullan.
3. "Disaridan erisilebilir" sonucunu SADECE gercekten tarayicidan (ya da kullaniciya dogrulatarak) test ettiysen yaz. SSH-terminal icinden `curl localhost:PORT` basarili olmasi "disaridan erisilebilir" ANLAMINA GELMEZ - bunlar farkli seyler, ikisini birbirine karistirma.
4. Production'a (8000, 3000) hicbir degisiklik, once test ortaminda (8001/3001) dogrulanmadan ve gorevde acikca izin verilmeden yapilmaz.
5. Her raporda, hangi ortamda test ettigini (8001/3001 test mi, 8000/3000 production mu) ACIKCA yaz, belirsiz birakma.

## Ek not - port 3001 (13 Temmuz 2026, ~06:55 UTC teshisi)

3001 portu SUREKLI acik bir servis degildir, sadece aktif test sirasinda bir process baslatildiginda dinler. Test bitince port kapanir, bu normaldir. Bir sonraki gorevlerde 3001'i kullanmadan once ONCE orada bir sunucu baslat (ornek: `pnpm run dev -- -p 3001`), SONRA tarayici testi yap.

Teshis kaniti: `sudo lsof -i :3001` ve `sudo ss -tlnp | grep 3001` ikisi de bos donmustu - port uzerinde hicbir process dinlemiyordu. Bu, firewall sorunu DEGIL; test sunucusunun duzguce durdurulup temizlenmis olmasinin dogal sonucu.
