#!/bin/bash
# Gunluk veri yedekleme scripti. radar.py'nin cron zamanlamasindan (Cuma 09:00 UTC)
# bagimsiz olarak her gun farkli bir saatte calisir.
set -e
KAYNAK_DIZIN="/home/asiyesudetayipoglu/sudoqu/backend"
YEDEK_DIZIN="/home/asiyesudetayipoglu/sudoqu-backups"
TARIH=$(date +%Y%m%d_%H%M%S)

mkdir -p "$YEDEK_DIZIN"

for dosya in firsatlar.json tasklar.json basvurular.json projeler.json; do
  if [ -f "$KAYNAK_DIZIN/$dosya" ]; then
    cp "$KAYNAK_DIZIN/$dosya" "$YEDEK_DIZIN/${dosya%.json}_$TARIH.json"
  fi
done

# 7 gunden eski yedekleri sil
find "$YEDEK_DIZIN" -name '*.json' -mtime +7 -delete

echo "[$(date -u)] Yedekleme tamamlandi: $TARIH" >> "$YEDEK_DIZIN/yedekleme_log.txt"
