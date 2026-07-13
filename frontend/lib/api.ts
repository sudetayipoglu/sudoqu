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
  eforKazancSeviyesi: string | null
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
    eforKazancSeviyesi: pickNullable(r, ["efor_kazanc_seviyesi"]),
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
    tamamlandi: pickBool(r, ["tamamlandi", "tamamlandı", "completed", "done", "isDone"]) || String(r.durum ?? "").toLowerCase().includes("tamamlan"),
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

export async function createTask(baslik: string, atanan: string, tur: string, deadline: string): Promise<void> {
  const params = new URLSearchParams({ baslik, atanan, tur })
  if (deadline) params.set("deadline", deadline)
  const res = await fetch(`${API_BASE}/tasklar?${params.toString()}`, {
    method: "POST",
    headers: { Accept: "application/json" },
  })
  if (!res.ok) throw new Error(`Görev eklenemedi (${res.status})`)
}

export async function updateTask(id: string, fields: { baslik?: string; atanan?: string; tur?: string; deadline?: string }): Promise<void> {
  const params = new URLSearchParams()
  if (fields.baslik !== undefined) params.set("baslik", fields.baslik)
  if (fields.atanan !== undefined) params.set("atanan", fields.atanan)
  if (fields.tur !== undefined) params.set("tur", fields.tur)
  if (fields.deadline !== undefined) params.set("deadline", fields.deadline)
  const res = await fetch(`${API_BASE}/tasklar/${encodeURIComponent(id)}?${params.toString()}`, {
    method: "PUT",
    headers: { Accept: "application/json" },
  })
  if (!res.ok) throw new Error(`Görev güncellenemedi (${res.status})`)
}

export async function getEkip(): Promise<string[]> {
  const res = await fetch(`${API_BASE}/ekip`, { headers: { Accept: "application/json" }, cache: "no-store" })
  if (!res.ok) throw new Error(`Ekip getirilemedi (${res.status})`)
  const data = await res.json()
  return Array.isArray(data) ? data.map(String) : []
}

/* ---------- Projeler (V1.4) ---------- */
export interface ProjeNot {
  tarih: string
  metin: string
}

export interface ProjeDosya {
  ad: string
  tarih: string
  boyut: number
}

export interface ProjeGithubBilgi {
  aciklama: string | null
  yildizSayisi: number | null
  sonCommit: { mesaj: string; tarih: string | null; yazar: string | null } | null
  dil: string | null
  hata?: string
}

export interface Proje {
  id: string
  ad: string
  aciklama: string
  githubLink: string | null
  durum: string
  notlar: ProjeNot[]
  dosyalar: ProjeDosya[]
  olusturmaTarihi: string
  githubBilgi: ProjeGithubBilgi | null
}

export async function getProjeler(): Promise<Proje[]> {
  const rows = await getJson("/projeler")
  return rows.map((r: Record<string, unknown>) => ({
    id: String(r.id),
    ad: String(r.ad ?? ""),
    aciklama: String(r.aciklama ?? ""),
    githubLink: (r.github_link as string) ?? null,
    durum: String(r.durum ?? "aktif"),
    notlar: (r.notlar as ProjeNot[]) ?? [],
    dosyalar: (r.dosyalar as ProjeDosya[]) ?? [],
    olusturmaTarihi: String(r.olusturma_tarihi ?? ""),
    githubBilgi: r.github_bilgi
      ? {
          aciklama: (r.github_bilgi as Record<string, unknown>).aciklama as string | null,
          yildizSayisi: (r.github_bilgi as Record<string, unknown>).yildiz_sayisi as number | null,
          sonCommit: (r.github_bilgi as Record<string, unknown>).son_commit as ProjeGithubBilgi["sonCommit"],
          dil: (r.github_bilgi as Record<string, unknown>).dil as string | null,
          hata: (r.github_bilgi as Record<string, unknown>).hata as string | undefined,
        }
      : null,
  }))
}

export async function createProje(ad: string, aciklama: string, githubLink: string): Promise<Proje> {
  const params = new URLSearchParams({ ad, aciklama, github_link: githubLink })
  const res = await fetch(`${API_BASE}/projeler?${params.toString()}`, {
    method: "POST",
    headers: { Accept: "application/json" },
  })
  if (!res.ok) throw new Error(`Proje eklenemedi (${res.status})`)
  return res.json()
}

export async function updateProjeDurum(id: string, durum: string): Promise<void> {
  const params = new URLSearchParams({ durum })
  const res = await fetch(`${API_BASE}/projeler/${encodeURIComponent(id)}?${params.toString()}`, {
    method: "PUT",
    headers: { Accept: "application/json" },
  })
  if (!res.ok) throw new Error(`Proje guncellenemedi (${res.status})`)
}

export async function addProjeNot(id: string, metin: string): Promise<void> {
  const params = new URLSearchParams({ metin })
  const res = await fetch(`${API_BASE}/projeler/${encodeURIComponent(id)}/not?${params.toString()}`, {
    method: "POST",
    headers: { Accept: "application/json" },
  })
  if (!res.ok) throw new Error(`Not eklenemedi (${res.status})`)
}

export async function uploadProjeDosya(id: string, file: File): Promise<void> {
  const formData = new FormData()
  formData.append("file", file)
  const res = await fetch(`${API_BASE}/projeler/${encodeURIComponent(id)}/dosya`, {
    method: "POST",
    body: formData,
  })
  if (!res.ok) {
    const hata = await res.json().catch(() => ({ detail: "Dosya yuklenemedi" }))
    throw new Error(hata.detail || `Dosya yuklenemedi (${res.status})`)
  }
}

export function projeDosyaUrl(id: string, dosyaAdi: string): string {
  return `${API_BASE}/projeler/${encodeURIComponent(id)}/dosya/${encodeURIComponent(dosyaAdi)}`
}

export interface SudolaOneri {
  skor: number
  aciklama: string
  gucluYonler: string[]
  riskler: string[]
}

export async function sudolaSoru(link: string, soru: string): Promise<string> {
  const params = new URLSearchParams({ link, soru })
  const res = await fetch(`${API_BASE}/sudola/soru?${params.toString()}`, {
    method: "POST",
    headers: { Accept: "application/json" },
  })
  if (!res.ok) {
    const hata = await res.json().catch(() => null)
    throw new Error(hata?.detail ?? `sudola soru basarisiz (${res.status})`)
  }
  const data = await res.json()
  return String(data.cevap ?? "")
}

export async function sudolaOneri(link: string): Promise<SudolaOneri> {
  const res = await fetch(`${API_BASE}/sudola/oneri/${encodeURIComponent(link)}`, {
    headers: { Accept: "application/json" },
  })
  if (!res.ok) {
    const hata = await res.json().catch(() => null)
    throw new Error(hata?.detail ?? `sudola oneri basarisiz (${res.status})`)
  }
  const data = await res.json()
  return {
    skor: Number(data.skor ?? 0),
    aciklama: String(data.aciklama ?? ""),
    gucluYonler: Array.isArray(data.guclu_yonler) ? data.guclu_yonler.map(String) : [],
    riskler: Array.isArray(data.riskler) ? data.riskler.map(String) : [],
  }
}
