CREATE TABLE IF NOT EXISTS ekip (
  id SERIAL PRIMARY KEY,
  isim TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS firsatlar (
  id SERIAL PRIMARY KEY,
  link TEXT UNIQUE NOT NULL,
  baslik TEXT NOT NULL,
  kaynak_sorgu TEXT,
  bulunma_tarihi TIMESTAMP,
  organizator TEXT,
  konu_kategori TEXT,
  son_basvuru_tarihi TEXT,
  onemli_tarihler TEXT,
  basvuru_asamalari TEXT,
  yer_mekan TEXT,
  konaklama_yol_destegi BOOLEAN,
  odul_miktari_turu TEXT,
  katilim_sartlari TEXT,
  takim_buyuklugu_limiti TEXT,
  basvuru_maliyeti TEXT,
  istenen_materyal TEXT,
  sponsor_kurumlar TEXT,
  extraction_durumu TEXT,
  extraction_tarihi TIMESTAMP,
  efor_seviyesi TEXT,
  duplicate_of_id INTEGER REFERENCES firsatlar(id),
  kaynak TEXT DEFAULT 'radar'
);

CREATE TABLE IF NOT EXISTS projeler (
  id TEXT PRIMARY KEY,
  ad TEXT NOT NULL,
  aciklama TEXT,
  github_link TEXT,
  durum TEXT,
  olusturma_tarihi TIMESTAMP
);

CREATE TABLE IF NOT EXISTS proje_notlar (
  id SERIAL PRIMARY KEY,
  proje_id TEXT REFERENCES projeler(id) ON DELETE CASCADE,
  tarih TIMESTAMP,
  metin TEXT
);

CREATE TABLE IF NOT EXISTS proje_dosyalar (
  id SERIAL PRIMARY KEY,
  proje_id TEXT REFERENCES projeler(id) ON DELETE CASCADE,
  dosya_adi TEXT,
  yuklenme_tarihi TIMESTAMP,
  boyut INTEGER
);

CREATE TABLE IF NOT EXISTS tasklar (
  id SERIAL PRIMARY KEY,
  baslik TEXT NOT NULL,
  atanan_id INTEGER REFERENCES ekip(id),
  tur TEXT,
  deadline TEXT,
  durum TEXT,
  olusturma_tarihi TIMESTAMP,
  firsat_id INTEGER REFERENCES firsatlar(id),
  proje_id TEXT REFERENCES projeler(id)
);

CREATE TABLE IF NOT EXISTS basvurular (
  id SERIAL PRIMARY KEY,
  firsat_id INTEGER REFERENCES firsatlar(id) NOT NULL,
  proje_id TEXT REFERENCES projeler(id),
  durum TEXT,
  basvuru_tarihi TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sudola_onerileri (
  id SERIAL PRIMARY KEY,
  firsat_id INTEGER REFERENCES firsatlar(id) NOT NULL,
  onerilen_proje_id TEXT REFERENCES projeler(id),
  skor INTEGER,
  aciklama TEXT,
  guclu_yonler TEXT,
  riskler TEXT,
  olusturma_tarihi TIMESTAMP
);
