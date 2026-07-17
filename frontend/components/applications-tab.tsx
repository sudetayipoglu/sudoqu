"use client"

import { useEffect, useMemo, useState, type ChangeEvent } from "react"
import {
  ArrowUpRight,
  CalendarDays,
  Check,
  FileText,
  Loader2,
  Search,
  Sparkles,
  Trash2,
  Upload,
  X,
} from "lucide-react"
import { Reveal } from "@/components/reveal"
import { StatusBadge } from "@/components/status-badge"
import {
  type Application,
  type Opportunity,
  type BasvuruDosya,
  setTakipDurumu,
  updateApplicationStatus,
  updateBasvuruNot,
  uploadBasvuruDosya,
  deleteBasvuruDosya,
  basvuruDosyaIndirUrl,
} from "@/lib/api"
import { cn } from "@/lib/utils"
import {
  maliyetDurumuHesapla,
  MALIYET_ETIKET,
  siralaFirsatlar,
  formatTuruEtkin,
  KONU_KATEGORI_SECENEKLERI,
  KONU_KATEGORI_ETIKET,
  ETKINLIK_TURU_SECENEKLERI,
  ETKINLIK_TURU_ETIKET,
  FORMAT_TURU_SECENEKLERI,
  FORMAT_TURU_ETIKET,
  type SiralamaTuru,
  type MaliyetDurumu,
} from "@/lib/opportunity-utils"

function formatDate(value: string) {
  if (!value) return "—"
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return d.toLocaleDateString("tr-TR", { day: "2-digit", month: "short", year: "numeric" })
}

type DetailFieldKey =
  | "organizator"
  | "konuKategori"
  | "sonBasvuruTarihi"
  | "onemliTarihler"
  | "basvuruAsamalari"
  | "yerMekan"
  | "konaklamaYolDestegi"
  | "odulMiktariTuru"
  | "katilimSartlari"
  | "takimBuyukluguLimiti"
  | "basvuruMaliyeti"
  | "istenenMateryal"
  | "sponsorKurumlar"

const DETAIL_FIELDS: { key: DetailFieldKey; label: string }[] = [
  { key: "organizator", label: "Organizatör" },
  { key: "konuKategori", label: "Konu / Kategori" },
  { key: "sonBasvuruTarihi", label: "Son Başvuru Tarihi" },
  { key: "onemliTarihler", label: "Önemli Tarihler" },
  { key: "basvuruAsamalari", label: "Başvuru Aşamaları" },
  { key: "yerMekan", label: "Yer / Mekan" },
  { key: "konaklamaYolDestegi", label: "Konaklama / Yol Desteği" },
  { key: "odulMiktariTuru", label: "Ödül Miktarı / Türü" },
  { key: "katilimSartlari", label: "Katılım Şartları" },
  { key: "takimBuyukluguLimiti", label: "Takım Büyüklüğü Limiti" },
  { key: "basvuruMaliyeti", label: "Başvuru Maliyeti" },
  { key: "istenenMateryal", label: "İstenen Materyal" },
  { key: "sponsorKurumlar", label: "Sponsor Kurumlar" },
]

const DURUM_SECENEKLERI: { value: string; label: string; tone: "warning" | "success" | "primary" }[] = [
  { value: "beklemede", label: "Beklemede", tone: "warning" },
  { value: "kazandi", label: "Kazandı", tone: "success" },
  { value: "kaybetti", label: "Kaybetti", tone: "primary" },
]

function durumTon(durum: string) {
  return DURUM_SECENEKLERI.find((d) => d.value === durum)?.tone ?? "warning"
}
function durumEtiket(durum: string) {
  return DURUM_SECENEKLERI.find((d) => d.value === durum)?.label ?? durum
}

type SubTab = "basvurulacaklar" | "basvurulanlar"

export function ApplicationsTab({
  items,
  applications,
  onChanged,
}: {
  items: Opportunity[]
  applications: Application[]
  onChanged: () => void
}) {
  const [subTab, setSubTab] = useState<SubTab>("basvurulacaklar")
  const [query, setQuery] = useState("")
  const [selected, setSelected] = useState<Opportunity | null>(null)
  const [detay, setDetay] = useState<Opportunity | null>(null)
  const [pending, setPending] = useState<string | null>(null)
  const [siralama, setSiralama] = useState<SiralamaTuru>("son_basvuru")
  const [seciliKonu, setSeciliKonu] = useState<string>("")
  const [seciliEtkinlikTuru, setSeciliEtkinlikTuru] = useState<string>("")
  const [seciliFormat, setSeciliFormat] = useState<string>("")
  const [seciliUlke, setSeciliUlke] = useState<string>("")
  const [seciliMaliyetler, setSeciliMaliyetler] = useState<Set<MaliyetDurumu>>(new Set())
  const [gosterilenSayisi, setGosterilenSayisi] = useState(60)

  useEffect(() => {
    setGosterilenSayisi(60)
  }, [subTab])

  const appByLink = useMemo(() => {
    const m = new Map<string, Application>()
    applications.forEach((a) => m.set(a.link, a))
    return m
  }, [applications])

  const subTabItems = useMemo(
    () => items.filter((o) => o.takipDurumu === (subTab === "basvurulacaklar" ? "basvurulacak" : "basvuruldu")),
    [items, subTab],
  )

  const ulkeSecenekleri = useMemo(() => {
    const s = new Set<string>()
    subTabItems.forEach((o) => {
      if (o.ulke) s.add(o.ulke)
    })
    return Array.from(s).sort((a, b) => a.localeCompare(b, "tr"))
  }, [subTabItems])

  function toggleMaliyet(value: MaliyetDurumu) {
    const next = new Set(seciliMaliyetler)
    if (next.has(value)) next.delete(value)
    else next.add(value)
    setSeciliMaliyetler(next)
  }

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    let sonuc = q
      ? subTabItems.filter((o) => o.baslik.toLowerCase().includes(q) || o.link.toLowerCase().includes(q))
      : subTabItems

    if (seciliKonu) {
      sonuc = sonuc.filter((o) => o.konuKategori === seciliKonu)
    }
    if (seciliEtkinlikTuru) {
      sonuc = sonuc.filter((o) => o.etkinlikTuru === seciliEtkinlikTuru)
    }
    if (seciliFormat) {
      sonuc = sonuc.filter((o) => formatTuruEtkin(o) === seciliFormat)
    }
    if (seciliUlke) {
      sonuc = sonuc.filter((o) => o.ulke === seciliUlke)
    }
    if (seciliMaliyetler.size > 0) {
      sonuc = sonuc.filter((o) => seciliMaliyetler.has(maliyetDurumuHesapla(o.basvuruMaliyeti)))
    }

    return siralaFirsatlar(sonuc, siralama)
  }, [subTabItems, query, seciliKonu, seciliEtkinlikTuru, seciliFormat, seciliUlke, seciliMaliyetler, siralama])

  const gosterilecekler = useMemo(() => filtered.slice(0, gosterilenSayisi), [filtered, gosterilenSayisi])

  async function handleGeriGonder(link: string) {
    setPending(link)
    try {
      await setTakipDurumu(link, "")
      onChanged()
    } catch (err) {
      console.log("[v0] geri gonder error:", (err as Error).message)
    } finally {
      setPending(null)
    }
  }

  async function handleBasvurulduYap(link: string) {
    setPending(link)
    try {
      await setTakipDurumu(link, "basvuruldu")
      onChanged()
    } catch (err) {
      console.log("[v0] basvuruldu error:", (err as Error).message)
    } finally {
      setPending(null)
    }
  }

  async function handleDurumDegistir(link: string, yeniDurum: string) {
    try {
      await updateApplicationStatus(link, yeniDurum)
      onChanged()
    } catch (err) {
      console.log("[v0] durum degistir error:", (err as Error).message)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => setSubTab("basvurulacaklar")}
          className={cn(
            "rounded-xl px-4 py-2 text-sm font-medium transition-all",
            subTab === "basvurulacaklar"
              ? "bg-primary text-primary-foreground glow-primary"
              : "border border-border bg-card/60 text-muted-foreground hover:text-foreground",
          )}
        >
          Başvurulacaklar
        </button>
        <button
          type="button"
          onClick={() => setSubTab("basvurulanlar")}
          className={cn(
            "rounded-xl px-4 py-2 text-sm font-medium transition-all",
            subTab === "basvurulanlar"
              ? "bg-primary text-primary-foreground glow-primary"
              : "border border-border bg-card/60 text-muted-foreground hover:text-foreground",
          )}
        >
          Başvurulanlar
        </button>
      </div>

      <Reveal>
        <div className="relative">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ara — başlık ya da bağlantı..."
            className="w-full rounded-xl border border-border bg-card/60 py-3 pl-11 pr-4 text-sm text-foreground outline-none backdrop-blur transition-colors placeholder:text-muted-foreground focus:border-primary/50 focus:ring-2 focus:ring-primary/20"
          />
        </div>
      </Reveal>

      <div className="flex flex-wrap items-center gap-3 text-xs">
        <select
          value={siralama}
          onChange={(e) => setSiralama(e.target.value as SiralamaTuru)}
          className="rounded-lg border border-border bg-card/60 px-3 py-1.5 text-xs text-foreground outline-none"
        >
          <option value="son_basvuru">Son başvuruya göre (yaklaşan üste)</option>
          <option value="alfabetik">Alfabetik</option>
          <option value="region">Bölgeye göre</option>
        </select>

        <select
          value={seciliKonu}
          onChange={(e) => setSeciliKonu(e.target.value)}
          className="rounded-lg border border-border bg-card/60 px-3 py-1.5 text-xs text-foreground outline-none"
        >
          <option value="">Tüm konular</option>
          {KONU_KATEGORI_SECENEKLERI.map((k) => (
            <option key={k} value={k}>
              {KONU_KATEGORI_ETIKET[k]}
            </option>
          ))}
        </select>

        <select
          value={seciliEtkinlikTuru}
          onChange={(e) => setSeciliEtkinlikTuru(e.target.value)}
          className="rounded-lg border border-border bg-card/60 px-3 py-1.5 text-xs text-foreground outline-none"
        >
          <option value="">Tüm türler</option>
          {ETKINLIK_TURU_SECENEKLERI.map((t) => (
            <option key={t} value={t}>
              {ETKINLIK_TURU_ETIKET[t]}
            </option>
          ))}
        </select>

        <select
          value={seciliFormat}
          onChange={(e) => setSeciliFormat(e.target.value)}
          className="rounded-lg border border-border bg-card/60 px-3 py-1.5 text-xs text-foreground outline-none"
        >
          <option value="">Tüm formatlar</option>
          {FORMAT_TURU_SECENEKLERI.map((f) => (
            <option key={f} value={f}>
              {FORMAT_TURU_ETIKET[f]}
            </option>
          ))}
        </select>

        <select
          value={seciliUlke}
          onChange={(e) => setSeciliUlke(e.target.value)}
          className="rounded-lg border border-border bg-card/60 px-3 py-1.5 text-xs text-foreground outline-none"
        >
          <option value="">Tüm ülkeler</option>
          {ulkeSecenekleri.map((u) => (
            <option key={u} value={u}>
              {u}
            </option>
          ))}
        </select>

        {(Object.keys(MALIYET_ETIKET) as MaliyetDurumu[])
          .filter((m) => m !== "belirtilmemis")
          .map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => toggleMaliyet(m)}
              className={cn(
                "rounded-full border px-3 py-1 transition-colors",
                seciliMaliyetler.has(m)
                  ? "border-success/50 bg-success/15 text-success"
                  : "border-border bg-card/60 text-muted-foreground hover:text-foreground",
              )}
            >
              {MALIYET_ETIKET[m]}
            </button>
          ))}
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          text={
            query
              ? "Aramanla eşleşen başvuru yok."
              : subTab === "basvurulacaklar"
                ? "Henüz başvurulacak olarak işaretlenmiş fırsat yok."
                : "Henüz başvurulmuş fırsat yok."
          }
        />
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {gosterilecekler.map((o, i) => {
            const app = appByLink.get(o.link)
            return (
              <Reveal as="li" key={o.id} delay={Math.min(i * 60, 360)}>
                <article
                  className="glow-hover group flex h-full flex-col rounded-2xl border border-border bg-card/70 p-5 backdrop-blur cursor-pointer"
                  onClick={() => setSelected(o)}
                >
                  <div className="mb-3 flex items-start justify-between gap-3">
                    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/15 text-primary">
                      <Sparkles className="h-4 w-4" />
                    </span>
                    {subTab === "basvurulanlar" && app && (
                      <StatusBadge tone={durumTon(app.durum)}>{durumEtiket(app.durum)}</StatusBadge>
                    )}
                  </div>

                  <h3 className="text-pretty text-base font-semibold leading-snug text-foreground">{o.baslik}</h3>

                  <div className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground">
                    <CalendarDays className="h-3.5 w-3.5" />
                    Bulunma: {formatDate(o.bulunmaTarihi)}
                  </div>

                  {o.link && (
                    <a
                      href={o.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="mt-3 inline-flex items-center gap-1 truncate text-sm text-cyan transition-colors hover:text-primary"
                    >
                      <span className="truncate">{o.link.replace(/^https?:\/\//, "")}</span>
                      <ArrowUpRight className="h-3.5 w-3.5 shrink-0" />
                    </a>
                  )}

                  <div className="mt-auto flex flex-col gap-2 pt-4">
                    {subTab === "basvurulacaklar" ? (
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={async (e) => {
                            e.stopPropagation()
                            await handleBasvurulduYap(o.link)
                          }}
                          disabled={pending === o.link}
                          className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-xl bg-primary px-3 py-2.5 text-xs font-medium text-primary-foreground transition-all hover:brightness-110 glow-primary"
                        >
                          {pending === o.link ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <Check className="h-3.5 w-3.5" />
                          )}
                          Başvuruldu
                        </button>
                        <button
                          type="button"
                          onClick={async (e) => {
                            e.stopPropagation()
                            await handleGeriGonder(o.link)
                          }}
                          disabled={pending === o.link}
                          className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-xl border border-border bg-card/60 px-3 py-2.5 text-xs font-medium text-foreground transition-all hover:brightness-110"
                        >
                          Fırsatlara geri gönder
                        </button>
                      </div>
                    ) : (
                      <>
                        <select
                          value={app?.durum ?? "beklemede"}
                          onClick={(e) => e.stopPropagation()}
                          onChange={(e) => {
                            e.stopPropagation()
                            handleDurumDegistir(o.link, e.target.value)
                          }}
                          className="w-full rounded-xl border border-border bg-card/60 px-3 py-2 text-xs text-foreground outline-none"
                        >
                          {DURUM_SECENEKLERI.map((d) => (
                            <option key={d.value} value={d.value}>
                              {d.label}
                            </option>
                          ))}
                        </select>
                        <div className="flex items-center gap-2">
                          <button
                            type="button"
                            onClick={async (e) => {
                              e.stopPropagation()
                              await handleGeriGonder(o.link)
                            }}
                            disabled={pending === o.link}
                            className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-xl border border-border bg-card/60 px-3 py-2.5 text-xs font-medium text-foreground transition-all hover:brightness-110"
                          >
                            Fırsata geri gönder
                          </button>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation()
                              setDetay(o)
                            }}
                            className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-xl bg-primary px-3 py-2.5 text-xs font-medium text-primary-foreground transition-all hover:brightness-110 glow-primary"
                          >
                            <FileText className="h-3.5 w-3.5" />
                            Başvuru detayları
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                </article>
              </Reveal>
            )
          })}
        </ul>
      )}

      {filtered.length > gosterilenSayisi && (
        <div className="flex justify-center pt-2">
          <button
            type="button"
            onClick={() => setGosterilenSayisi((n) => n + 60)}
            className="rounded-xl border border-border bg-card/60 px-4 py-2 text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            Daha fazla göster ({filtered.length - gosterilenSayisi} kaldı)
          </button>
        </div>
      )}

      {selected && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
          onClick={() => setSelected(null)}
        >
          <div
            className="w-full max-w-lg max-h-[85vh] overflow-y-auto rounded-2xl border border-border bg-card p-6 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-4 flex items-start justify-between gap-3">
              <h3 className="text-pretty text-lg font-semibold leading-snug text-foreground">{selected.baslik}</h3>
              <button
                type="button"
                onClick={() => setSelected(null)}
                aria-label="Kapat"
                className="shrink-0 rounded-lg p-1 text-muted-foreground transition-colors hover:bg-primary/10 hover:text-foreground"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="mb-4 flex items-center gap-1.5 text-xs text-muted-foreground">
              <CalendarDays className="h-3.5 w-3.5" />
              Bulunma: {formatDate(selected.bulunmaTarihi)}
            </div>

            {selected.link && (
              <a
                href={selected.link}
                target="_blank"
                rel="noopener noreferrer"
                className="mb-4 inline-flex items-center gap-1 truncate text-sm text-cyan transition-colors hover:text-primary"
              >
                <span className="truncate">{selected.link.replace(/^https?:\/\//, "")}</span>
                <ArrowUpRight className="h-3.5 w-3.5 shrink-0" />
              </a>
            )}

            <dl className="space-y-3 text-sm">
              {DETAIL_FIELDS.map(({ key, label }) => (
                <div key={key} className="flex flex-col gap-0.5 border-b border-border/60 pb-2 last:border-none">
                  <dt className="text-xs font-medium text-muted-foreground">{label}</dt>
                  <dd className="text-foreground">{selected[key] ?? "Bilgi yok"}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      )}

      {detay && (
        <BasvuruDetayModal
          opportunity={detay}
          application={appByLink.get(detay.link)}
          onClose={() => setDetay(null)}
          onChanged={onChanged}
        />
      )}
    </div>
  )
}

function BasvuruDetayModal({
  opportunity,
  application,
  onClose,
  onChanged,
}: {
  opportunity: Opportunity
  application: Application | undefined
  onClose: () => void
  onChanged: () => void
}) {
  const mevcutDosyalar: BasvuruDosya[] = ((application?.raw as Record<string, unknown>)?.dosyalar as BasvuruDosya[]) ?? []
  const [not, setNot] = useState<string>(((application?.raw as Record<string, unknown>)?.not as string) ?? "")
  const [kaydediliyor, setKaydediliyor] = useState(false)
  const [yukleniyor, setYukleniyor] = useState(false)
  const [hata, setHata] = useState<string | null>(null)

  async function handleNotKaydet() {
    setKaydediliyor(true)
    setHata(null)
    try {
      await updateBasvuruNot(opportunity.link, not)
      onChanged()
    } catch (err) {
      setHata((err as Error).message)
    } finally {
      setKaydediliyor(false)
    }
  }

  async function handleDosyaSec(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setYukleniyor(true)
    setHata(null)
    try {
      await uploadBasvuruDosya(opportunity.link, file)
      onChanged()
    } catch (err) {
      setHata((err as Error).message)
    } finally {
      setYukleniyor(false)
      e.target.value = ""
    }
  }

  async function handleDosyaSil(ad: string) {
    try {
      await deleteBasvuruDosya(opportunity.link, ad)
      onChanged()
    } catch (err) {
      setHata((err as Error).message)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg max-h-[85vh] overflow-y-auto rounded-2xl border border-border bg-card p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between gap-3">
          <h3 className="text-pretty text-lg font-semibold leading-snug text-foreground">Başvuru Detayları</h3>
          <button
            type="button"
            onClick={onClose}
            aria-label="Kapat"
            className="shrink-0 rounded-lg p-1 text-muted-foreground transition-colors hover:bg-primary/10 hover:text-foreground"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <p className="mb-4 text-sm text-muted-foreground">{opportunity.baslik}</p>

        <div className="mb-5">
          <label className="mb-1 block text-xs text-muted-foreground">Notlar</label>
          <textarea
            value={not}
            onChange={(e) => setNot(e.target.value)}
            rows={5}
            placeholder="Başvuruyla ilgili notlarını buraya yaz..."
            className="w-full rounded-lg border border-border bg-card/60 px-3 py-2 text-sm text-foreground outline-none focus:border-primary/50"
          />
          <button
            type="button"
            onClick={handleNotKaydet}
            disabled={kaydediliyor}
            className="mt-2 inline-flex items-center gap-1.5 rounded-xl bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-all hover:brightness-110 disabled:opacity-60"
          >
            {kaydediliyor && <Loader2 className="h-4 w-4 animate-spin" />}
            Notu Kaydet
          </button>
        </div>

        <div>
          <label className="mb-1 block text-xs text-muted-foreground">Belgeler</label>
          <label className="inline-flex cursor-pointer items-center gap-1.5 rounded-xl border border-border bg-card/60 px-4 py-2 text-sm text-foreground transition-all hover:brightness-110">
            {yukleniyor ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
            Dosya Yükle
            <input type="file" className="hidden" onChange={handleDosyaSec} disabled={yukleniyor} />
          </label>

          {mevcutDosyalar.length > 0 ? (
            <ul className="mt-3 space-y-2">
              {mevcutDosyalar.map((d) => (
                <li
                  key={d.ad}
                  className="flex items-center justify-between gap-2 rounded-lg border border-border bg-card/60 px-3 py-2 text-xs"
                >
                  <a
                    href={basvuruDosyaIndirUrl(opportunity.link, d.ad)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex min-w-0 items-center gap-1.5 truncate text-foreground hover:text-primary"
                  >
                    <FileText className="h-3.5 w-3.5 shrink-0" />
                    <span className="truncate">{d.ad}</span>
                  </a>
                  <button
                    type="button"
                    onClick={() => handleDosyaSil(d.ad)}
                    aria-label="Sil"
                    className="shrink-0 rounded-md p-1 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-3 text-xs text-muted-foreground">Henüz belge yüklenmedi.</p>
          )}

          {hata && <p className="mt-2 text-xs text-destructive">{hata}</p>}
        </div>
      </div>
    </div>
  )
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-border bg-card/40 py-16 text-center text-sm text-muted-foreground">
      {text}
    </div>
  )
}
