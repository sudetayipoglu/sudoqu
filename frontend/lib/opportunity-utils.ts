import type { Opportunity } from "./api"

/* ---------- Tarih ayrıştırma (ISO + Türkçe doğal dil) ----------
   radar.py'deki dedup mantığıyla aynı yaklaşım: önce ISO (YYYY-MM-DD)
   dener, olmazsa "28 Şubat 2026" gibi Türkçe doğal dil formatını dener. */
const TR_AYLAR: Record<string, number> = {
  ocak: 1, subat: 2, şubat: 2, mart: 3, nisan: 4,
  mayis: 5, mayıs: 5, haziran: 6, temmuz: 7, agustos: 8, ağustos: 8,
  eylul: 9, eylül: 9, ekim: 10, kasim: 11, kasım: 11, aralik: 12, aralık: 12,
}

export function parseTarihEsnek(s: string | null | undefined): Date | null {
  if (!s) return null
  const trimmed = s.trim()

  const isoMatch = trimmed.match(/^(\d{4})-(\d{2})-(\d{2})$/)
  if (isoMatch) {
    const [, y, m, d] = isoMatch
    const dt = new Date(Number(y), Number(m) - 1, Number(d))
    return Number.isNaN(dt.getTime()) ? null : dt
  }

  const parcalar = trimmed.toLowerCase().split(/\s+/)
  if (parcalar.length === 3) {
    const [gunS, ayS, yilS] = parcalar
    const ay = TR_AYLAR[ayS]
    const gun = Number.parseInt(gunS, 10)
    const yil = Number.parseInt(yilS, 10)
    if (ay && !Number.isNaN(gun) && !Number.isNaN(yil)) {
      const dt = new Date(yil, ay - 1, gun)
      return Number.isNaN(dt.getTime()) ? null : dt
    }
  }
  return null
}

/** Süresi geçmiş mi? Tarih yoksa (null) her zaman false döner - gizlenmez. */
export function suresiGecmisMi(sonBasvuruTarihi: string | null): boolean {
  const tarih = parseTarihEsnek(sonBasvuruTarihi)
  if (!tarih) return false
  const bugun = new Date()
  bugun.setHours(0, 0, 0, 0)
  return tarih.getTime() < bugun.getTime()
}

/* ---------- Format türetme (yer_mekan alanından) ---------- */
export type FormatTuru = "online" | "yuz_yuze" | "hibrit" | "belirtilmemis"

const ONLINE_KELIMELER = ["online", "çevrimiçi", "cevrimici", "uzaktan", "virtual", "sanal"]

export function formatTuruHesapla(yerMekan: string | null): FormatTuru {
  if (!yerMekan) return "belirtilmemis"
  const s = yerMekan.toLowerCase()
  const onlineVar = ONLINE_KELIMELER.some((k) => s.includes(k))
  const digerYerVar = /[a-zçğıöşü]{3,}/i.test(s.replace(new RegExp(ONLINE_KELIMELER.join("|"), "gi"), ""))
  if (onlineVar && digerYerVar) return "hibrit"
  if (onlineVar) return "online"
  return "yuz_yuze"
}

export const FORMAT_ETIKET: Record<FormatTuru, string> = {
  online: "Online",
  yuz_yuze: "Yüz yüze",
  hibrit: "Hibrit",
  belirtilmemis: "Belirtilmemiş",
}

/* ---------- Maliyet durumu türetme (basvuru_maliyeti alanından) ---------- */
export type MaliyetDurumu = "ucretsiz" | "ucretli" | "belirtilmemis"

const UCRETSIZ_KELIMELER = ["ücretsiz", "ucretsiz", "free", "bedava", "0 tl", "yok"]

export function maliyetDurumuHesapla(basvuruMaliyeti: string | null): MaliyetDurumu {
  if (!basvuruMaliyeti) return "belirtilmemis"
  const s = basvuruMaliyeti.toLowerCase()
  if (UCRETSIZ_KELIMELER.some((k) => s.includes(k))) return "ucretsiz"
  return "ucretli"
}

export const MALIYET_ETIKET: Record<MaliyetDurumu, string> = {
  ucretsiz: "Ücretsiz",
  ucretli: "Ücretli",
  belirtilmemis: "Belirtilmemiş",
}

/* ---------- Sıralama ---------- */
export type SiralamaTuru = "son_basvuru" | "alfabetik" | "region"

export function siralaFirsatlar(items: Opportunity[], siralama: SiralamaTuru): Opportunity[] {
  const kopya = [...items]
  if (siralama === "alfabetik") {
    return kopya.sort((a, b) => a.baslik.localeCompare(b.baslik, "tr"))
  }
  if (siralama === "region") {
    return kopya.sort((a, b) => {
      const ra = a.yerMekan || "￿"
      const rb = b.yerMekan || "￿"
      return ra.localeCompare(rb, "tr")
    })
  }
  return kopya.sort((a, b) => {
    const ta = parseTarihEsnek(a.sonBasvuruTarihi)
    const tb = parseTarihEsnek(b.sonBasvuruTarihi)
    if (ta && tb) return ta.getTime() - tb.getTime()
    if (ta && !tb) return -1
    if (!ta && tb) return 1
    return 0
  })
}

/* ---------- Kategori sistemi (konu / tur / format / ulke) ---------- */

export const KONU_KATEGORI_SECENEKLERI = [
  "sağlık", "finans", "sürdürülebilirlik", "yeşil teknoloji", "afet",
  "emlak", "eğitim", "yapay zeka", "diğer",
] as const

export const KONU_KATEGORI_ETIKET: Record<string, string> = {
  "sağlık": "Sağlık",
  "finans": "Finans",
  "sürdürülebilirlik": "Sürdürülebilirlik",
  "yeşil teknoloji": "Yeşil Teknoloji",
  "afet": "Afet",
  "emlak": "Emlak",
  "eğitim": "Eğitim",
  "yapay zeka": "Yapay Zeka",
  "diğer": "Diğer",
}

export const ETKINLIK_TURU_SECENEKLERI = ["hackathon", "datathon", "ideathon", "hibe"] as const

export const ETKINLIK_TURU_ETIKET: Record<string, string> = {
  hackathon: "Hackathon",
  datathon: "Datathon",
  ideathon: "Ideathon",
  hibe: "Hibe",
}

export const FORMAT_TURU_SECENEKLERI = ["yuzyuze", "online", "hibrit"] as const

export const FORMAT_TURU_ETIKET: Record<string, string> = {
  yuzyuze: "Yuz Yuze",
  online: "Online",
  hibrit: "Hibrit",
}

// Backend'den gelen format_turu Turkce karakterli olabilir ("yuzyuze" -> normalize)
function normalizeFormatDegeri(deger: string): string {
  const d = deger.toLowerCase()
  if (d === "yüzyüze" || d.includes("yüz")) return "yuzyuze"
  if (d.includes("hibrit")) return "hibrit"
  if (d.includes("online")) return "online"
  return d
}

// Backend alanini oncelikli kullan, yoksa eski yerMekan-bazli tahmine dus
export function formatTuruEtkin(o: Opportunity): string | null {
  if (o.formatTuruBackend) return normalizeFormatDegeri(o.formatTuruBackend)
  const tahmin = formatTuruHesapla(o.yerMekan)
  if (tahmin === "belirtilmemis") return null
  return tahmin === "yuz_yuze" ? "yuzyuze" : tahmin
}
