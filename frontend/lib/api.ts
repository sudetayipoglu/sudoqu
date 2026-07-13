export const API_BASE = "http://34.30.225.219:8000"

/* ---------- Types (normalized) ---------- */
export interface Opportunity {
  id: string
  baslik: string
  link: string
  bulunmaTarihi: string
  basvuruldu: boolean
  raw: Record<string, unknown>
  organizator: string | null
  konuKategori: string | null
  sonBasvuruTarihi: string | null
  onemliTarihler: string | null
  basvuruAsamalari: string | null
  yerMekan: string | null
  konaklamaYolDestegi: string | null
  odulMiktariTuru: string | null
  katilimSartlari: string | null
  takimBuyukluguLimiti: string | null
  basvuruMaliyeti: string | null
  istenenMateryal: string | null
  sponsorKurumlar: string | null
  duplicateOf: string | null
}

export interface Task {
  id: string
  baslik: string
  atanan: string
  tur: string
  deadline: string
  durum: string
  tamamlandi: boolean
  raw: Record<string, unknown>
}

export interface Application {
  id: string
  baslik: string
  link: string
  durum: string
  raw: Record<string, unknown>
}

/* ---------- Helpers ---------- */
type AnyRecord = Record<string, unknown>

function pick(obj: AnyRecord, keys: string[], fallback = ""): string {
  for (const k of keys) {
    const v = obj[k]
    if (v !== undefined && v !== null && String(v).trim() !== "") return String(v)
  }
  return fallback
}

function pickBool(obj: AnyRecord, keys: string[]): boolean {
  for (const k of keys) {
    const v = obj[k]
    if (typeof v === "boolean") return v
    if (typeof v === "string") return ["true", "1", "evet", "yes", "tamamlandi", "tamamlandı"].includes(v.toLowerCase())
    if (typeof v === "number") return v === 1
  }
  return false
}

function pickNullable(obj: AnyRecord, keys: string[]): string | null {
  for (const k of keys) {
    const v = obj[k]
    if (v === undefined || v === null) continue
    if (typeof v === "boolean") return v ? "Evet" : "Hayır"
    const s = String(v).trim()
    if (s !== "" && s.toLowerCase() !== "null") return s
  }
  return null
}

async function getJson(path: string): Promise<AnyRecord[]> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { Accept: "application/json" },
    cache: "no-store",
  })
  if (!res.ok) throw new Error(`İstek başarısız (${res.status})`)
  const data = await res.json()
  if (Array.isArray(data)) return data as AnyRecord[]
  // Some APIs wrap results, try common wrappers
  for (const key of ["data", "items", "results", "firsatlar", "tasklar", "basvurular"]) {
    if (Array.isArray((data as AnyRecord)[key])) return (data as AnyRecord)[key] as AnyRecord[]
  }
  return []
}

/* ---------- Endpoints ---------- */
export async function getOpportunities(): Promise<Opportunity[]> {
  const rows = await getJson("/firsatlar")
  return rows.map((r, i) => ({
    id: pick(r, ["id", "_id", "uuid"], String(i)),
    baslik: pick(r, ["baslik", "başlık", "title", "isim", "name"], "İsimsiz Fırsat"),
    link: pick(r, ["link", "url", "adres"]),
    bulunmaTarihi: pick(r, ["bulunma_tarihi", "bulunmaTarihi", "tarih", "date", "created_at", "createdAt"]),
    basvuruldu: pickBool(r, ["basvuruldu", "başvuruldu", "applied", "isApplied"]),
    organizator: pickNullable(r, ["organizator"]),
    konuKategori: pickNullable(r, ["konu_kategori"]),
    sonBasvuruTarihi: pickNullable(r, ["son_basvuru_tarihi"]),
    onemliTarihler: pickNullable(r, ["onemli_tarihler"]),
    basvuruAsamalari: pickNullable(r, ["basvuru_asamalari"]),
    yerMekan: pickNullable(r, ["yer_mekan"]),
    konaklamaYolDestegi: pickNullable(r, ["konaklama_yol_destegi"]),
    odulMiktariTuru: pickNullable(r, ["odul_miktari_turu"]),
    katilimSartlari: pickNullable(r, ["katilim_sartlari"]),
    takimBuyukluguLimiti: pickNullable(r, ["takim_buyuklugu_limiti"]),
    basvuruMaliyeti: pickNullable(r, ["basvuru_maliyeti"]),
    istenenMateryal: pickNullable(r, ["istenen_materyal"]),
    sponsorKurumlar: pickNullable(r, ["sponsor_kurumlar"]),
    duplicateOf: pickNullable(r, ["duplicate_of"]),
    raw: r,
  }))
}

export async function getTasks(): Promise<Task[]> {
  const rows = await getJson("/tasklar")
  return rows.map((r, i) => ({
    id: pick(r, ["id", "_id", "uuid"], String(i)),
    baslik: pick(r, ["baslik", "başlık", "title", "isim", "name"], "İsimsiz Görev"),
    atanan: pick(r, ["atanan", "assignee", "kisi", "kişi", "assigned_to", "assignedTo", "sorumlu"]),
    tur: pick(r, ["tur", "tür", "type", "kategori", "category"]),
    deadline: pick(r, ["deadline", "son_tarih", "sonTarih", "bitis", "bitiş", "due", "due_date", "dueDate", "tarih"]),
    durum: pick(r, ["durum", "status", "state"], "beklemede"),
    tamamlandi: pickBool(r, ["tamamlandi", "tamamlandı", "completed", "done", "isDone"]),
    raw: r,
  }))
}

export async function getApplications(): Promise<Application[]> {
  const rows = await getJson("/basvurular")
  return rows.map((r, i) => ({
    id: pick(r, ["id", "_id", "uuid"], String(i)),
    baslik: pick(r, ["baslik", "başlık", "title", "isim", "name"], "İsimsiz Başvuru"),
    link: pick(r, ["link", "url", "adres"]),
    durum: pick(r, ["durum", "status", "state"], "gönderildi"),
    raw: r,
  }))
}

export async function markApplied(link: string): Promise<void> {
  const res = await fetch(`${API_BASE}/basvurular/${encodeURIComponent(link)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
  })
  if (!res.ok) throw new Error(`Başvuru işaretlenemedi (${res.status})`)
}

export async function completeTask(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/tasklar/${encodeURIComponent(id)}/tamamla`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
  })
  if (!res.ok) throw new Error(`Görev tamamlanamadı (${res.status})`)
}
