#!/bin/bash
# Gunluk veri yedekleme scripti. radar.py'nin cron zamanlamasindan (Cuma 09:00 UTC) bagimsiz olarak her gun farkli bir saatte calisir.
# FAZ B (docker-compose + Postgres gecisi) sonrasi: asil veri artik Postgres'te. pg_dump ile SQL yedegi aliniyor.
# Eski JSON kopyalama adimi geriye donuk uyumluluk icin korunuyor; DATABASE_URL set oldugunda bu JSON dosyalari
# artik canli guncellenmiyor (donuk/tarihi veri), asil yedek pg_dump'tir.
set -e
KAYNAK_DIZIN="/home/asiyesudetayipoglu/sudoqu/backend"
YEDEK_DIZIN="/home/asiyesudetayipoglu/sudoqu-backups"
COMPOSE_DOSYASI="/home/asiyesudetayipoglu/sudoqu/docker-compose.yml"
TARIH=$(date +%Y%m%d_%H%M%S)

mkdir -p "$YEDEK_DIZIN"

for dosya in firsatlar.json tasklar.json basvurular.json projeler.json; do
  if [ -f "$KAYNAK_DIZIN/$dosya" ]; then
    cp "$KAYNAK_DIZIN/$dosya" "$YEDEK_DIZIN/${dosya%.json}_$TARIH.json"
  fi
done

if sudo docker-compose -f "$COMPOSE_DOSYASI" exec -T postgres pg_dump -U sudoqu sudoqu > "$YEDEK_DIZIN/postgres_$TARIH.sql" 2>>"$YEDEK_DIZIN/yedekleme_log.txt"; then
  echo "[$(date -u)] pg_dump basarili: postgres_$TARIH.sql" >> "$YEDEK_DIZIN/yedekleme_log.txt"
else
  echo "[$(date -u)] pg_dump BASARISIZ" >> "$YEDEK_DIZIN/yedekleme_log.txt"
  rm -f "$YEDEK_DIZIN/postgres_$TARIH.sql"
fi

# 7 gunden eski yedekleri sil
find "$YEDEK_DIZIN" -name '*.json' -mtime +7 -delete
find "$YEDEK_DIZIN" -name '*.sql' -mtime +7 -delete

echo "[$(date -u)] Yedekleme tamamlandi: $TARIH" >> "$YEDEK_DIZIN/yedekleme_log.txt"
