# SudoQu - Docker ile sifirdan kurulum

Bu proje Docker ile calistirilabilir. Asagidaki adimlar sifir bir makinede
(Docker kurulu, baska hicbir sey kurulu olmayan) calisir.

## Gereksinimler
- Docker Engine (>= 20.x) ve Docker Compose plugin
- Bu repoyu klonlamis olmak

## 1) Ortam degiskenlerini ayarla

```bash
cp backend/.env.example backend/.env
```

Sonra `backend/.env` dosyasini gercek degerlerle doldur:
- `TAVILY_API_KEY` - https://tavily.com hesabindan alinir
- `GEMINI_API_KEY` - https://aistudio.google.com hesabindan alinir
- `DEEPSEEK_API_KEY` - opsiyonel, su an uretimde kullanilmiyor

Not: Eger Google Secret Manager erisimi varsa (proje: yeno-502112, secret
isimleri: `tavily-api-key`, `gemini-api-key`) backend bu degerleri once oradan
okumayi dener, erisim yoksa otomatik olarak .env dosyasina duser. Bu yuzden
.env dosyasi her durumda dolu olmali (fallback icin).

## 2) Build ve calistir (canli/gercek portlar: 8000, 3000)

```bash
docker compose build
docker compose up -d
```

Backend: http://localhost:8000
Frontend: http://localhost:3000

## 3) Loglari izle

```bash
docker compose logs -f
```

## 4) Durdur

```bash
docker compose down
```

## Test / paralel calisma (alternatif portlar: 8001, 3001)

Canli sisteme dokunmadan, ayni makinede paralel test icin:

```bash
docker compose -f docker-compose.test.yml build
docker compose -f docker-compose.test.yml up -d
curl http://localhost:8001/
curl http://localhost:3001/
docker compose -f docker-compose.test.yml down
```

## Notlar
- `backend/.env` ve `frontend/node_modules`, `.next` gibi klasorler Docker
  image'ina dahil edilmez (bkz. `.dockerignore` dosyalari).
- Veri dosyalari (`firsatlar.json`, `tasklar.json`, `basvurular.json`,
  `projeler.json`) backend image'ina kopyalanir; guncel/canli veriyle
  calismak icin bir volume mount (`- ./backend:/app`) eklenmesi
  degerlendirilebilir (bu hazirlik asamasinda eklenmedi, ileride karar
  gerektirir).
- Frontend, backend API adresini `frontend/lib/api.ts` icinde sabit
  `http://34.30.225.219:8000` olarak kullaniyor (tarayici uzerinden dogrudan
  cagriliyor, container-ici network degil). Bu yuzden test container'lari
  (8001) calisirken bile frontend hala canli 8000 portundaki backend'e
  baglanir - gercek bir Docker-ici entegrasyon testi icin bu adresin ortam
  degiskenine (`NEXT_PUBLIC_API_BASE`) tasinmasi gerekir. Bu, bu hazirlik
  gorevinin kapsami disindadir; sadece not edildi.
