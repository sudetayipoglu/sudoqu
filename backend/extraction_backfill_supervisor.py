#!/usr/bin/env python3
"""
Extraction backfill supervisor (GOREV 2).

radar.py'yi RADAR_SKIP_SEARCH=1 ile (sadece extraction+dedup, yeni arama yok) tekrar
tekrar container icinde calistirir. Patched radar.py artik gunluk Gemini kotasi
dolduğunda kendi kendine duruyor ve kalan kayitlari "henuz_islenmedi" olarak birakiyor
(bkz. commit 43a7be6). Bu supervisor da:
  1) DB'de kac "henuz_islenmedi" kayit kaldigini olcer,
  2) 0 ise biter,
  3) degilse radar.py'yi (container icinde) calistirir, cikisini bekler,
  4) tekrar olcer - eger sayida ilerleme yoksa (kota hemen dolmus olabilir) veya
     ilerleme olduysa (kota bir noktada dolmus) - HER IKI durumda da 1 SAAT bekleyip
     tekrar dener (kullanicinin istegi: saatlik kontrol, 5/15 dakikada bir degil),
  5) MAX_TUR asilirsa vazgecer ve loglar.

Cikti: backend/radar_extraction_backfill_log.txt (radar.py'nin ham stdout/stderr'i,
her turun basi/sonu ile birlikte) + bu supervisor'in kendi durum satirlari de ayni dosyaya.
"""
import subprocess
import sys
import time
from datetime import datetime

COMPOSE_DIR = "/home/asiyesudetayipoglu/sudoqu"
COMPOSE_FILE = f"{COMPOSE_DIR}/docker-compose.yml"
LOG_FILE = f"{COMPOSE_DIR}/backend/radar_extraction_backfill_log.txt"
BEKLEME_SN = 60 * 60   # 1 SAAT
MAX_TUR = 500            # guvenlik siniri (~500 saat/~20 gun sonra vazgecer, loglar) - gunluk kota ~80-90 kayit isledigi ve 700+ kayit kalabildigi icin 40 saat cok kisaydi


def log(msg):
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def kalan_sayisi():
    r = subprocess.run(
        ["docker", "compose", "-f", COMPOSE_FILE, "exec", "-T", "postgres", "psql", "-U", "sudoqu", "-d", "sudoqu",
         "-t", "-A", "-c",
         "SELECT COUNT(*) FROM firsatlar WHERE extraction_durumu = 'henuz_islenmedi';"],
        capture_output=True, text=True, timeout=30,
    )
    cikti = r.stdout.strip()
    if r.returncode != 0 or not cikti.isdigit():
        log(f"UYARI: kalan_sayisi sorgusu basarisiz oldu (returncode={r.returncode}). "
            f"stdout={cikti!r} stderr={r.stderr.strip()!r}")
        raise RuntimeError(f"kalan_sayisi: DB sorgusu gecerli bir sayi dondurmedi: {cikti!r}")
    return int(cikti)


def radar_calistir():
    with open(LOG_FILE, "a") as f:
        f.write(f"\n===== {datetime.now().isoformat(timespec='seconds')} - radar.py (RADAR_SKIP_SEARCH=1) turu basliyor =====\n")
        f.flush()
        subprocess.run(
            ["docker", "compose", "-f", COMPOSE_FILE,
             "exec", "-T", "-e", "RADAR_SKIP_SEARCH=1", "backend", "python3", "-u", "radar.py"],
            stdout=f, stderr=subprocess.STDOUT,
        )


def main():
    log("Extraction backfill supervisor basladi (GOREV 2).")
    for tur in range(1, MAX_TUR + 1):
        try:
            kalan_once = kalan_sayisi()
            log(f"Tur {tur}/{MAX_TUR}: {kalan_once} 'henuz_islenmedi' kayit var.")
            if kalan_once == 0:
                log("Tum kayitlar islenmis. Backfill TAMAMLANDI.")
                return 0
            radar_calistir()
            kalan_sonra = kalan_sayisi()
            log(f"Tur {tur} bitti. {kalan_sonra} kayit hala 'henuz_islenmedi'.")
            if kalan_sonra == 0:
                log("Tum kayitlar islenmis. Backfill TAMAMLANDI.")
                return 0
            if kalan_sonra < kalan_once:
                log(f"Ilerleme kaydedildi ({kalan_once - kalan_sonra} kayit islendi). "
                    f"Muhtemelen gunluk kota bu turda doldu. {BEKLEME_SN}sn (1 saat) beklenip tekrar denenecek.")
            else:
                log(f"Bu turda ilerleme olmadi (kota zaten dolu olabilir). "
                    f"{BEKLEME_SN}sn (1 saat) beklenip tekrar denenecek.")
        except Exception as e:
            log(f"HATA (Tur {tur}): {type(e).__name__}: {e}. Cokmeden devam ediliyor, "
                f"{BEKLEME_SN}sn (1 saat) beklenip tekrar denenecek.")
        time.sleep(BEKLEME_SN)

    log(f"MAX_TUR ({MAX_TUR}) asildi, vazgeciliyor. Kalan kayit sayisi: {kalan_sayisi()}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
