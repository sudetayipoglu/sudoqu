"use client"

import { useEffect, useMemo, useState } from "react"
import { ArrowUpRight, CalendarDays, Check, Loader2, Search, Sparkles, X } from "lucide-react"
import { Reveal } from "@/components/reveal"
import { StatusBadge } from "@/components/status-badge"
import { markApplied, type Opportunity } from "@/lib/api"
import { cn } from "@/lib/utils"
import {
  formatTuruHesapla,
  FORMAT_ETIKET,
  maliyetDurumuHesapla,
  MALIYET_ETIKET,
  suresiGecmisMi,
  siralaFirsatlar,
  type SiralamaTuru,
  type FormatTuru,
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

export function OpportunitiesTab({
  items,
  onApplied,
}: {
  items: Opportunity[]
  onApplied: (id: string) => void
}) {
  const [query, setQuery] = useState("")
  const [pending, setPending] = useState<string | null>(null)
  const [selected, setSelected] = useState<Opportunity | null>(null)
  const [sudolaClicked, setSudolaClicked] = useState(false)
  const [siralama, setSiralama] = useState<SiralamaTuru>("son_basvuru")
  const [seciliTurler, setSeciliTurler] = useState<Set<string>>(new Set())
  const [seciliFormatlar, setSeciliFormatlar] = useState<Set<FormatTuru>>(new Set())
  const [seciliMaliyetler, setSeciliMaliyetler] = useState<Set<MaliyetDurumu>>(new Set())
  const [gosterilenSayisi, setGosterilenSayisi] = useState(60)

  useEffect(() => {
    setGosterilenSayisi(60)
  }, [query, seciliTurler, seciliFormatlar, seciliMaliyetler, siralama])

  const visibleItems = useMemo(
    () => items.filter((o) => !o.duplicateOf && !suresiGecmisMi(o.sonBasvuruTarihi)),
    [items],
  )

  const turSecenekleri = useMemo(() => {
    const s = new Set<string>()
    visibleItems.forEach((o) => {
      if (o.konuKategori) s.add(o.konuKategori)
    })
    return Array.from(s).sort((a, b) => a.localeCompare(b, "tr"))
  }, [visibleItems])

  function toggleTur(value: string) {
    const next = new Set(seciliTurler)
    if (next.has(value)) next.delete(value)
    else next.add(value)
    setSeciliTurler(next)
  }

  function toggleFormat(value: FormatTuru) {
    const next = new Set(seciliFormatlar)
    if (next.has(value)) next.delete(value)
    else next.add(value)
    setSeciliFormatlar(next)
  }

  function toggleMaliyet(value: MaliyetDurumu) {
    const next = new Set(seciliMaliyetler)
    if (next.has(value)) next.delete(value)
    else next.add(value)
    setSeciliMaliyetler(next)
  }

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    let sonuc = q
      ? visibleItems.filter((o) => o.baslik.toLowerCase().includes(q) || o.link.toLowerCase().includes(q))
      : visibleItems

    if (seciliTurler.size > 0) {
      sonuc = sonuc.filter((o) => o.konuKategori && seciliTurler.has(o.konuKategori))
    }
    if (seciliFormatlar.size > 0) {
      sonuc = sonuc.filter((o) => seciliFormatlar.has(formatTuruHesapla(o.yerMekan)))
    }
    if (seciliMaliyetler.size > 0) {
      sonuc = sonuc.filter((o) => seciliMaliyetler.has(maliyetDurumuHesapla(o.basvuruMaliyeti)))
    }

    return siralaFirsatlar(sonuc, siralama)
  }, [visibleItems, query, seciliTurler, seciliFormatlar, seciliMaliyetler, siralama])

  const gosterilecekler = useMemo(() => filtered.slice(0, gosterilenSayisi), [filtered, gosterilenSayisi])

  async function handleApply(o: Opportunity) {
    if (o.basvuruldu || pending) return
    setPending(o.id)
    try {
      await markApplied(o.link || o.id)
      onApplied(o.id)
    } catch (err) {
      console.log("[v0] markApplied error:", (err as Error).message)
    } finally {
      setPending(null)
    }
  }

  return (
    <div className="space-y-6">
      <Reveal className="relative">
        <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Fırsat ara — başlık ya da bağlantı..."
          className="w-full rounded-xl border border-border bg-card/60 py-3 pl-11 pr-4 text-sm text-foreground outline-none backdrop-blur transition-colors placeholder:text-muted-foreground focus:border-primary/50 focus:ring-2 focus:ring-primary/20"
        />
      </Reveal>

      <div className="flex flex-wrap items-center gap-3 text-xs">
        <select
          value={siralama}
          onChange={(e) => setSiralama(e.target.value as SiralamaTuru)}
          className="rounded-lg border border-border bg-card/60 px-3 py-1.5 text-xs text-foreground outline-none"
        >
          <option value="son_basvuru">Son basvuruya gore (yaklasan uste)</option>
          <option value="alfabetik">Alfabetik</option>
          <option value="region">Bolgeye gore</option>
        </select>

        {turSecenekleri.map((tur) => (
          <button
            key={tur}
            type="button"
            onClick={() => toggleTur(tur)}
            className={cn(
              "rounded-full border px-3 py-1 transition-colors",
              seciliTurler.has(tur)
                ? "border-primary/50 bg-primary/15 text-primary"
                : "border-border bg-card/60 text-muted-foreground hover:text-foreground",
            )}
          >
            {tur}
          </button>
        ))}

        {(Object.keys(FORMAT_ETIKET) as FormatTuru[])
          .filter((f) => f !== "belirtilmemis")
          .map((f) => (
            <button
              key={f}
              type="button"
              onClick={() => toggleFormat(f)}
              className={cn(
                "rounded-full border px-3 py-1 transition-colors",
                seciliFormatlar.has(f)
                  ? "border-cyan/50 bg-cyan/15 text-cyan"
                  : "border-border bg-card/60 text-muted-foreground hover:text-foreground",
              )}
            >
              {FORMAT_ETIKET[f]}
            </button>
          ))}

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
        <EmptyState text={query ? "Aramanla eşleşen fırsat yok." : "Henüz fırsat bulunamadı."} />
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {gosterilecekler.map((o, i) => (
            <Reveal as="li" key={o.id} delay={Math.min(i * 60, 360)}>
              <article
              className="glow-hover group flex h-full flex-col rounded-2xl border border-border bg-card/70 p-5 backdrop-blur cursor-pointer"
              onClick={() => {
                setSelected(o)
                setSudolaClicked(false)
              }}
            >
                <div className="mb-3 flex items-start justify-between gap-3">
                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/15 text-primary">
                    <Sparkles className="h-4 w-4" />
                  </span>
                  {o.basvuruldu && (
                    <StatusBadge tone="success">
                      <Check className="h-3 w-3" /> Başvuruldu
                    </StatusBadge>
                  )}
          {o.eforKazancSeviyesi && (
            <StatusBadge
              tone={o.eforKazancSeviyesi === "yuksek" ? "warning" : o.eforKazancSeviyesi === "orta" ? "cyan" : "success"}
            >
              Efor: {o.eforKazancSeviyesi === "yuksek" ? "Yüksek" : o.eforKazancSeviyesi === "orta" ? "Orta" : "Düşük"}
            </StatusBadge>
          )}
                </div>

                <h3 className="text-pretty text-base font-semibold leading-snug text-foreground">
                  {o.baslik}
                </h3>

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

                <button
                  type="button"
                  onClick={(e) => {
                  e.stopPropagation()
                  handleApply(o)
                }}
                  disabled={o.basvuruldu || pending === o.id}
                  className={cn(
                    "mt-auto inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition-all",
                    o.basvuruldu
                      ? "cursor-default border border-success/30 bg-success/10 text-success"
                      : "bg-primary text-primary-foreground hover:brightness-110 glow-primary",
                  )}
                >
                  {pending === o.id ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" /> İşaretleniyor
                    </>
                  ) : o.basvuruldu ? (
                    <>
                      <Check className="h-4 w-4" /> İşaretlendi
                    </>
                  ) : (
                    "Başvur olarak işaretle"
                  )}
                </button>
              </article>
            </Reveal>
          ))}
        </ul>
      )}

      {filtered.length > gosterilenSayisi && (
        <div className="flex justify-center pt-2">
          <button
            type="button"
            onClick={() => setGosterilenSayisi((n) => n + 60)}
            className="rounded-xl border border-border bg-card/60 px-4 py-2 text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            Daha fazla goster ({filtered.length - gosterilenSayisi} kaldi)
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

            <button
              type="button"
              onClick={() => setSudolaClicked(true)}
              className="mt-5 w-full rounded-xl bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-all hover:brightness-110 glow-primary"
            >
              sudola
            </button>
            {sudolaClicked && <p className="mt-2 text-center text-xs text-muted-foreground">Yakında</p>}
          </div>
        </div>
      )}
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
