"use client"

import { useState, useEffect } from "react"
import { CalendarClock, Check, Loader2, Tag, User, Plus, X, Pencil, Trash2, Briefcase, Link2, List, CalendarDays, ChevronLeft, ChevronRight } from "lucide-react"
import { Reveal } from "@/components/reveal"
import { StatusBadge, statusTone } from "@/components/status-badge"
import { completeTask, createTask, updateTask, deleteTask, getProjeler, getOpportunities, type Task, type Proje, type Opportunity } from "@/lib/api"
import { cn } from "@/lib/utils"

function formatDate(value: string) {
  if (!value) return "—"
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return d.toLocaleDateString("tr-TR", { day: "2-digit", month: "short", year: "numeric" })
}

function deadlineTone(value: string, done: boolean): "success" | "warning" | "primary" | "muted" {
  if (done) return "success"
  if (!value) return "muted"
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return "muted"
  const diff = (d.getTime() - Date.now()) / 86_400_000
  if (diff < 0) return "primary"
  if (diff <= 3) return "warning"
  return "muted"
}

const inputClass =
  "w-full rounded-lg border border-border bg-card/60 px-3 py-2 text-sm text-foreground outline-none focus:border-primary/50"

function TakvimGorunumu({
  items,
  ay,
  setAy,
  onGoreve,
}: {
  items: Task[]
  ay: Date
  setAy: (d: Date) => void
  onGoreve: (t: Task) => void
}) {
  const yil = ay.getFullYear()
  const ayIndex = ay.getMonth()
  const ilkGun = new Date(yil, ayIndex, 1)
  const sonGun = new Date(yil, ayIndex + 1, 0)
  const gunSayisi = sonGun.getDate()
  const baslangicBosluk = (ilkGun.getDay() + 6) % 7

  const gunlereGoreGorevler = new Map<number, Task[]>()
  for (const t of items) {
    if (!t.deadline) continue
    const d = new Date(t.deadline)
    if (Number.isNaN(d.getTime())) continue
    if (d.getFullYear() === yil && d.getMonth() === ayIndex) {
      const arr = gunlereGoreGorevler.get(d.getDate()) || []
      arr.push(t)
      gunlereGoreGorevler.set(d.getDate(), arr)
    }
  }

  const hucreler: (number | null)[] = []
  for (let i = 0; i < baslangicBosluk; i++) hucreler.push(null)
  for (let g = 1; g <= gunSayisi; g++) hucreler.push(g)
  while (hucreler.length % 7 !== 0) hucreler.push(null)

  const ayAdlari = ["Ocak", "Subat", "Mart", "Nisan", "Mayis", "Haziran", "Temmuz", "Agustos", "Eylul", "Ekim", "Kasim", "Aralik"]
  const gunAdlari = ["Pzt", "Sal", "Car", "Per", "Cum", "Cmt", "Paz"]

  const bugun = new Date()
  const bugunAyniAy = bugun.getFullYear() === yil && bugun.getMonth() === ayIndex

  return (
    <div className="space-y-3 rounded-2xl border border-border bg-card/40 p-4 backdrop-blur">
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => setAy(new Date(yil, ayIndex - 1, 1))}
          className="rounded-lg border border-border p-1.5 text-muted-foreground transition-colors hover:text-foreground"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
        <div className="text-sm font-medium text-foreground">
          {ayAdlari[ayIndex]} {yil}
        </div>
        <button
          type="button"
          onClick={() => setAy(new Date(yil, ayIndex + 1, 1))}
          className="rounded-lg border border-border p-1.5 text-muted-foreground transition-colors hover:text-foreground"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
      <div className="grid grid-cols-7 gap-1 text-center text-[11px] text-muted-foreground">
        {gunAdlari.map((g) => (
          <div key={g} className="py-1">
            {g}
          </div>
        ))}
      </div>
      <div className="grid grid-cols-7 gap-1">
        {hucreler.map((gun, i) => {
          if (gun === null) {
            return <div key={i} className="min-h-[72px] rounded-lg border border-transparent" />
          }
          const gorevler = gunlereGoreGorevler.get(gun) || []
          const bugunMu = bugunAyniAy && bugun.getDate() === gun
          return (
            <div
              key={i}
              className={cn(
                "min-h-[72px] rounded-lg border p-1 text-left",
                bugunMu ? "border-primary/50 bg-primary/10" : "border-border bg-card/60",
              )}
            >
              <div className={cn("mb-1 text-[11px]", bugunMu ? "font-semibold text-primary" : "text-muted-foreground")}>{gun}</div>
              <div className="space-y-1">
                {gorevler.slice(0, 3).map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => onGoreve(t)}
                    title={t.baslik}
                    className={cn(
                      "block w-full truncate rounded px-1 py-0.5 text-left text-[10px] transition-colors",
                      t.tamamlandi ? "bg-success/15 text-success" : "bg-primary/15 text-primary hover:bg-primary/25",
                    )}
                  >
                    {t.baslik}
                  </button>
                ))}
                {gorevler.length > 3 && <div className="text-[10px] text-muted-foreground">+{gorevler.length - 3} daha</div>}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export function TasksTab({
  items,
  onCompleted,
  ekip,
  onChanged,
}: {
  items: Task[]
  onCompleted: (id: string) => void
  ekip: string[]
  onChanged: () => void
}) {
  const [pending, setPending] = useState<string | null>(null)
  const [siliniyor, setSiliniyor] = useState<string | null>(null)
  const [filterKisi, setFilterKisi] = useState<string>("hepsi")
  const [gorunum, setGorunum] = useState<"liste" | "takvim">("liste")
  const [takvimAy, setTakvimAy] = useState<Date>(() => { const d = new Date(); d.setDate(1); return d })

  const [formAcik, setFormAcik] = useState(false)
  const [baslik, setBaslik] = useState("")
  const [atanan, setAtanan] = useState("")
  const [tur, setTur] = useState("task")
  const [deadline, setDeadline] = useState("")
  const [gonderiliyor, setGonderiliyor] = useState(false)
  const [hata, setHata] = useState<string | null>(null)

  const [duzenlenenId, setDuzenlenenId] = useState<string | null>(null)
  const [editBaslik, setEditBaslik] = useState("")
  const [editAtanan, setEditAtanan] = useState("")
  const [editDeadline, setEditDeadline] = useState("")
  const [editKaydediliyor, setEditKaydediliyor] = useState(false)

  const [projeler, setProjeler] = useState<Proje[]>([])
  const [firsatlar, setFirsatlar] = useState<Opportunity[]>([])
  const [projeId, setProjeId] = useState("")
  const [firsatId, setFirsatId] = useState("")
  const [editProjeId, setEditProjeId] = useState("")
  const [editFirsatId, setEditFirsatId] = useState("")

  useEffect(() => {
    getProjeler().then(setProjeler).catch(() => {})
    getOpportunities().then(setFirsatlar).catch(() => {})
  }, [])

  async function handleComplete(t: Task) {
    if (t.tamamlandi || pending) return
    setPending(t.id)
    try {
      await completeTask(t.id)
      onCompleted(t.id)
    } catch (err) {
      console.log("[v0] completeTask error:", (err as Error).message)
    } finally {
      setPending(null)
    }
  }

  async function handleSil(t: Task) {
    if (!window.confirm(`"${t.baslik}" gorevini silmek istediginize emin misiniz?`)) return
    setSiliniyor(t.id)
    try {
      await deleteTask(t.id)
      onChanged()
    } catch (err) {
      console.log("[v0] deleteTask error:", (err as Error).message)
    } finally {
      setSiliniyor(null)
    }
  }

  async function handleEkle(e: React.FormEvent) {
    e.preventDefault()
    if (!baslik.trim()) {
      setHata("Başlık boş olamaz")
      return
    }
    setGonderiliyor(true)
    setHata(null)
    try {
      await createTask(baslik.trim(), (atanan || "belirsiz").trim(), tur, deadline, projeId || undefined, firsatId || undefined)
      setBaslik("")
      setAtanan("")
      setTur("task")
      setDeadline("")
      setProjeId("")
      setFirsatId("")
      setFormAcik(false)
      onChanged()
    } catch (err) {
      setHata(err instanceof Error ? err.message : "Görev eklenemedi")
    } finally {
      setGonderiliyor(false)
    }
  }

  function handleDuzenleBaslat(t: Task) {
    setDuzenlenenId(t.id)
    setEditBaslik(t.baslik)
    setEditAtanan(t.atanan === "belirsiz" ? "" : t.atanan)
    setEditDeadline(t.deadline || "")
    setEditProjeId(t.projeId || "")
    setEditFirsatId(t.firsatLink || "")
  }

  function handleDuzenleIptal() {
    setDuzenlenenId(null)
  }

  async function handleDuzenleKaydet(t: Task) {
    if (!editBaslik.trim()) return
    setEditKaydediliyor(true)
    try {
      await updateTask(t.id, {
        baslik: editBaslik.trim(),
        atanan: (editAtanan || "belirsiz").trim(),
        deadline: editDeadline,
        projeId: editProjeId,
        firsatId: editFirsatId,
      })
      setDuzenlenenId(null)
      onChanged()
    } catch (err) {
      console.log("[v0] updateTask error:", (err as Error).message)
    } finally {
      setEditKaydediliyor(false)
    }
  }

  const filtered =
    filterKisi === "hepsi"
      ? items
      : items.filter((t) =>
          (t.atanan || "belirsiz")
            .split(",")
            .map((s) => s.trim())
            .includes(filterKisi),
        )

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium text-muted-foreground">Task &amp; Takvim</h2>
        <button
          type="button"
          onClick={() => setFormAcik((v) => !v)}
          className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-all hover:brightness-110"
        >
          {formAcik ? <X className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
          {formAcik ? "Vazgeç" : "Yeni Görev"}
        </button>
      </div>

      {formAcik && (
        <Reveal className="rounded-2xl border border-border bg-card/60 p-5 backdrop-blur">
          <form onSubmit={handleEkle} className="space-y-3">
            <div>
              <label className="mb-1 block text-xs text-muted-foreground">Başlık</label>
              <input
                value={baslik}
                onChange={(e) => setBaslik(e.target.value)}
                maxLength={200}
                className={inputClass}
                placeholder="orn. Başvuru metnini hazırla"
              />
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              <div>
                <label className="mb-1 block text-xs text-muted-foreground">Atanan(lar)</label>
                <input
                  list="ekip-listesi"
                  value={atanan}
                  onChange={(e) => setAtanan(e.target.value)}
                  className={inputClass}
                  placeholder="belirsiz (birden fazla kisi icin virgulle ayirin: orn. sudo, yeno)"
                />
                <datalist id="ekip-listesi">
                  {ekip.map((kisi) => (
                    <option key={kisi} value={kisi} />
                  ))}
                </datalist>
              </div>
              <div>
                <label className="mb-1 block text-xs text-muted-foreground">Tür</label>
                <input value={tur} onChange={(e) => setTur(e.target.value)} className={inputClass} placeholder="task" />
              </div>
              <div>
                <label className="mb-1 block text-xs text-muted-foreground">Deadline</label>
                <input
                  type="date"
                  value={deadline}
                  onChange={(e) => setDeadline(e.target.value)}
                  className={inputClass}
                />
              </div>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs text-muted-foreground">Proje (opsiyonel)</label>
                <select
                  value={projeId}
                  onChange={(e) => setProjeId(e.target.value)}
                  className={inputClass}
                >
                  <option value="">Yok</option>
                  {projeler.map((p) => (
                    <option key={p.id} value={p.id}>{p.ad}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs text-muted-foreground">Fırsat (opsiyonel)</label>
                <select
                  value={firsatId}
                  onChange={(e) => setFirsatId(e.target.value)}
                  className={inputClass}
                >
                  <option value="">Yok</option>
                  {firsatlar.map((f) => (
                    <option key={f.link} value={f.link}>{f.baslik}</option>
                  ))}
                </select>
              </div>
            </div>
            {hata && <p className="text-xs text-destructive">{hata}</p>}
            <button
              type="submit"
              disabled={gonderiliyor}
              className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-all hover:brightness-110 disabled:opacity-60"
            >
              {gonderiliyor && <Loader2 className="h-4 w-4 animate-spin" />}
              Görevi Kaydet
            </button>
          </form>
        </Reveal>
      )}

      <div className="flex items-center gap-2 text-xs">
        <button
          type="button"
          onClick={() => setGorunum("liste")}
          className={cn(
            "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 transition-colors",
            gorunum === "liste" ? "border-primary/50 bg-primary/15 text-primary" : "border-border text-muted-foreground hover:text-foreground",
          )}
        >
          <List className="h-3.5 w-3.5" />
          Liste
        </button>
        <button
          type="button"
          onClick={() => setGorunum("takvim")}
          className={cn(
            "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 transition-colors",
            gorunum === "takvim" ? "border-primary/50 bg-primary/15 text-primary" : "border-border text-muted-foreground hover:text-foreground",
          )}
        >
          <CalendarDays className="h-3.5 w-3.5" />
          Takvim
        </button>
      </div>

      {ekip.length > 0 && (
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setFilterKisi("hepsi")}
            className={cn(
              "rounded-full border px-3 py-1 text-xs transition-colors",
              filterKisi === "hepsi" ? "border-primary/50 bg-primary/15 text-primary" : "border-border text-muted-foreground hover:text-foreground",
            )}
          >
            Tümü
          </button>
          {ekip.map((kisi) => (
            <button
              key={kisi}
              type="button"
              onClick={() => setFilterKisi(kisi)}
              className={cn(
                "rounded-full border px-3 py-1 text-xs transition-colors",
                filterKisi === kisi ? "border-primary/50 bg-primary/15 text-primary" : "border-border text-muted-foreground hover:text-foreground",
              )}
            >
              {kisi}
            </button>
          ))}
        </div>
      )}

      {gorunum === "takvim" ? (
        <TakvimGorunumu items={filtered} ay={takvimAy} setAy={setTakvimAy} onGoreve={(t) => { setGorunum("liste"); handleDuzenleBaslat(t) }} />
      ) : filtered.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-border bg-card/40 py-16 text-center text-sm text-muted-foreground">
          Henüz görev bulunamadı.
        </div>
      ) : (
        <ul className="grid gap-4 lg:grid-cols-2">
          {filtered.map((t, i) => {
            const dTone = deadlineTone(t.deadline, t.tamamlandi)
            const duzenleniyor = duzenlenenId === t.id
            return (
              <Reveal as="li" key={t.id} delay={Math.min(i * 60, 360)}>
                <article
                  className={cn(
                    "glow-hover flex h-full flex-col rounded-2xl border border-border bg-card/70 p-5 backdrop-blur",
                  )}
                >
                  {duzenleniyor ? (
                    <div className="space-y-3">
                      <div>
                        <label className="mb-1 block text-xs text-muted-foreground">Başlık</label>
                        <input value={editBaslik} onChange={(e) => setEditBaslik(e.target.value)} className={inputClass} />
                      </div>
                      <div className="grid gap-3 sm:grid-cols-2">
                        <div>
                          <label className="mb-1 block text-xs text-muted-foreground">Atanan(lar)</label>
                          <input
                            list="ekip-listesi"
                            value={editAtanan}
                            onChange={(e) => setEditAtanan(e.target.value)}
                            className={inputClass}
                            placeholder="belirsiz (birden fazla kisi icin virgulle ayirin: orn. sudo, yeno)"
                          />
                        </div>
                        <div>
                          <label className="mb-1 block text-xs text-muted-foreground">Deadline</label>
                          <input
                            type="date"
                            value={editDeadline}
                            onChange={(e) => setEditDeadline(e.target.value)}
                            className={inputClass}
                          />
                        </div>
                      </div>
                      <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <label className="mb-1 block text-xs text-muted-foreground">Proje</label>
                    <select
                      value={editProjeId}
                      onChange={(e) => setEditProjeId(e.target.value)}
                      className={inputClass}
                    >
                      <option value="">Yok</option>
                      {projeler.map((p) => (
                        <option key={p.id} value={p.id}>{p.ad}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="mb-1 block text-xs text-muted-foreground">Fırsat</label>
                    <select
                      value={editFirsatId}
                      onChange={(e) => setEditFirsatId(e.target.value)}
                      className={inputClass}
                    >
                      <option value="">Yok</option>
                      {firsatlar.map((f) => (
                        <option key={f.link} value={f.link}>{f.baslik}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => handleDuzenleKaydet(t)}
                          disabled={editKaydediliyor}
                          className="inline-flex items-center gap-2 rounded-xl bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground transition-all hover:brightness-110 disabled:opacity-60"
                        >
                          {editKaydediliyor && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                          Kaydet
                        </button>
                        <button
                          type="button"
                          onClick={handleDuzenleIptal}
                          className="inline-flex items-center gap-2 rounded-xl border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
                        >
                          İptal
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="mb-3 flex items-start justify-between gap-3">
                        <h3
                          className={cn(
                            "text-pretty text-base font-semibold leading-snug text-foreground",
                            t.tamamlandi && "line-through decoration-success/60",
                          )}
                        >
                          {t.baslik}
                        </h3>
                        <div className="flex shrink-0 items-center gap-2">
                          <button
                            type="button"
                            onClick={() => handleDuzenleBaslat(t)}
                            className="text-muted-foreground transition-colors hover:text-foreground"
                            aria-label="Düzenle"
                          >
                            <Pencil className="h-3.5 w-3.5" />
                          </button>
                          <button
                            type="button"
                            onClick={() => handleSil(t)}
                            disabled={siliniyor === t.id}
                            className="text-muted-foreground transition-colors hover:text-destructive disabled:opacity-40"
                            aria-label="Sil"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                          <StatusBadge tone={t.tamamlandi ? "success" : statusTone(t.durum)}>
                            {t.tamamlandi ? "Tamamlandı" : t.durum || "Beklemede"}
                          </StatusBadge>
                        </div>
                      </div>

                      <dl className="grid grid-cols-1 gap-2 text-sm sm:grid-cols-3">
                        <Meta icon={<User className="h-3.5 w-3.5" />} label="Atanan" value={t.atanan || "—"} />
                        <Meta icon={<Tag className="h-3.5 w-3.5" />} label="Tür" value={t.tur || "—"} />
            {t.projeAdi && (
              <Meta icon={<Briefcase className="h-3.5 w-3.5" />} label="Proje" value={t.projeAdi} />
            )}
            {t.firsatBaslik && (
              <Meta icon={<Link2 className="h-3.5 w-3.5" />} label="Fırsat" value={t.firsatBaslik} />
            )}
                        <div className="flex items-center gap-1.5">
                          <span className="text-muted-foreground">
                            <CalendarClock className="h-3.5 w-3.5" />
                          </span>
                          <div className="min-w-0">
                            <dt className="text-[11px] uppercase tracking-wide text-muted-foreground">Deadline</dt>
                            <dd>
                              <StatusBadge tone={dTone}>{formatDate(t.deadline)}</StatusBadge>
                            </dd>
                          </div>
                        </div>
                      </dl>

                      <button
                        type="button"
                        onClick={() => handleComplete(t)}
                        disabled={t.tamamlandi || pending === t.id}
                        className={cn(
                          "mt-4 inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition-all",
                          t.tamamlandi
                            ? "cursor-default border border-success/30 bg-success/10 text-success"
                            : "bg-primary text-primary-foreground hover:brightness-110 glow-primary",
                        )}
                      >
                        {pending === t.id ? (
                          <>
                            <Loader2 className="h-4 w-4 animate-spin" /> Güncelleniyor
                          </>
                        ) : t.tamamlandi ? (
                          <>
                            <Check className="h-4 w-4" /> Tamamlandı
                          </>
                        ) : (
                          "Tamamlandı işaretle"
                        )}
                      </button>
                    </>
                  )}
                </article>
              </Reveal>
            )
          })}
        </ul>
      )}
    </div>
  )
}

function Meta({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-muted-foreground">{icon}</span>
      <div className="min-w-0">
        <dt className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</dt>
        <dd className="truncate text-foreground">{value}</dd>
      </div>
    </div>
  )
}
