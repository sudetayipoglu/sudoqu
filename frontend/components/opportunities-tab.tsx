"use client"

import { useEffect, useMemo, useState } from "react"
import { ArrowUpRight, CalendarDays, Check, Loader2, Plus, Search, Sparkles, X } from "lucide-react"
import { Reveal } from "@/components/reveal"
import { StatusBadge } from "@/components/status-badge"
import { markApplied, getProjeler, getSudolaSonOneri, addManualFirsat, type Opportunity, type Proje, type SudolaSonOneri } from "@/lib/api"
import { cn } from "@/lib/utils"
import { SudolaPanel } from "@/components/sudola-panel"
import {
  maliyetDurumuHesapla,
  MALIYET_ETIKET,
  suresiGecmisMi,
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

export function OpportunitiesTab({
  items,
  onApplied,
  initialLink = null,
  onInitialLinkConsumed,
  onChanged,
}: {
  items: Opportunity[]
  onApplied: (id: string) => void
  initialLink?: string | null
  onInitialLinkConsumed?: () => void
  onChanged?: () => void
}) {
  const [query, setQuery] = useState("")
  const [pending, setPending] = useState<string | null>(null)
  const [selected, setSelected] = useState<Opportunity | null>(null)
  const [sudolaClicked, setSudolaClicked] = useState(false)
  const [siralama, setSiralama] = useState<SiralamaTuru>("son_basvuru")
  const [seciliKonu, setSeciliKonu] = useState<string>("")
  const [seciliEtkinlikTuru, setSeciliEtkinlikTuru] = useState<string>("")
  const [seciliFormat, setSeciliFormat] = useState<string>("")
  const [seciliUlke, setSeciliUlke] = useState<string>("")
  const [seciliMaliyetler, setSeciliMaliyetler] = useState<Set<MaliyetDurumu>>(new Set())
  const [gosterilenSayisi, setGosterilenSayisi] = useState(60)

  const [projeler, setProjeler] = useState<Proje[]>([])
  const [basvuruAcikId, setBasvuruAcikId] = useState<string | null>(null)
  const [basvuruSecim, setBasvuruSecim] = useState<Record<string, string>>({})
  const [basvuruOnerisi, setBasvuruOnerisi] = useState<Record<string, SudolaSonOneri | null>>({})

  const [manuelAcik, setManuelAcik] = useState(false)
  const [manuelBaslik, setManuelBaslik] = useState("")
  const [manuelOrganizator, setManuelOrganizator] = useState("")
  const [manuelKonuKategori, setManuelKonuKategori] = useState("")
  const [manuelSonBasvuru, setManuelSonBasvuru] = useState("")
  const [manuelYerMekan, setManuelYerMekan] = useState("")
  const [manuelOdulMiktariTuru, setManuelOdulMiktariTuru] = useState("")
  const [manuelKatilimSartlari, setManuelKatilimSartlari] = useState("")
  const [manuelGonderiliyor, setManuelGonderiliyor] = useState(false)
  const [manuelHata, setManuelHata] = useState<string | null>(null)

  useEffect(() => {
    getProjeler().then(setProjeler).catch(() => {})
  }, [])

  useEffect(() => {
    setGosterilenSayisi(60)
  }, [query, seciliKonu, seciliEtkinlikTuru, seciliFormat, seciliUlke, seciliMaliyetler, siralama])

  useEffect(() => {
    if (!initialLink) return
    const eslesen = items.find((o) => o.link === initialLink)
    if (eslesen) {
      setSelected(eslesen)
    }
    onInitialLinkConsumed?.()
  }, [initialLink, items])

  const visibleItems = useMemo(
    () => items.filter((o) => !o.duplicateOf && !suresiGecmisMi(o.sonBasvuruTarihi)),
    [items],
  )

  const ulkeSecenekleri = useMemo(() => {
    const s = new Set<string>()
    visibleItems.forEach((o) => {
      if (o.ulke) s.add(o.ulke)
    })
    return Array.from(s).sort((a, b) => a.localeCompare(b, "tr"))
  }, [visibleItems])

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
  }, [visibleItems, query, seciliKonu, seciliEtkinlikTuru, seciliFormat, seciliUlke, seciliMaliyetler, siralama])

  const gosterilecekler = useMemo(() => filtered.slice(0, gosterilenSayisi), [filtered, gosterilenSayisi])

  async function handleApply(o: Opportunity, projeId?: string) {
    if (o.basvuruldu || pending) return
    setPending(o.id)
    try {
      await markApplied(o.link || o.id, projeId || undefined)
      onApplied(o.id)
      setBasvuruAcikId(null)
    } catch (err) {
      console.log("[v0] markApplied error:", (err as Error).message)
    } finally {
      setPending(null)
    }
  }

  async function acBasvuruSecici(o: Opportunity) {
    setBasvuruAcikId(o.id)
    if (basvuruOnerisi[o.id] !== undefined) return
    try {
      const sonuc = await getSudolaSonOneri(o.link || o.id)
      setBasvuruOnerisi((m) => ({ ...m, [o.id]: sonuc }))
      setBasvuruSecim((m) =>
        m[o.id] !== undefined ? m : { ...m, [o.id]: sonuc.onerilenProjeId ?? "" },
      )
    } catch (err) {
      console.log("[v0] getSudolaSonOneri error:", (err as Error).message)
      setBasvuruOnerisi((m) => ({ ...m, [o.id]: null }))
    }
  }

  async function handleManuelEkle(e: React.FormEvent) {
    e.preventDefault()
    const baslik = manuelBaslik.trim()
    if (!baslik) {
      setManuelHata("Baslik gerekli")
      return
    }
    setManuelGonderiliyor(true)
    setManuelHata(null)
    try {
      await addManualFirsat({
        baslik,
        organizator: manuelOrganizator.trim() || undefined,
        konuKategori: manuelKonuKategori.trim() || undefined,
        sonBasvuruTarihi: manuelSonBasvuru.trim() || undefined,
        yerMekan: manuelYerMekan.trim() || undefined,
        odulMiktariTuru: manuelOdulMiktariTuru.trim() || undefined,
        katilimSartlari: manuelKatilimSartlari.trim() || undefined,
      })
      setManuelBaslik("")
      setManuelOrganizator("")
      setManuelKonuKategori("")
      setManuelSonBasvuru("")
      setManuelYerMekan("")
      setManuelOdulMiktariTuru("")
      setManuelKatilimSartlari("")
      setManuelAcik(false)
      onChanged?.()
    } catch (err) {
      setManuelHata((err as Error).message)
    } finally {
      setManuelGonderiliyor(false)
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

      <div className="flex items-center justify-end">
        <button
          type="button"
          onClick={() => setManuelAcik((v) => !v)}
          className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-all hover:brightness-110"
        >
          {manuelAcik ? <X className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
          {manuelAcik ? "Vazgec" : "Manuel Firsat Ekle"}
        </button>
      </div>

      {manuelAcik && (
        <Reveal className="rounded-2xl border border-border bg-card/60 p-5 backdrop-blur">
          <form onSubmit={handleManuelEkle} className="space-y-3">
            <div>
              <label className="mb-1 block text-xs text-muted-foreground">Baslik</label>
              <input
                value={manuelBaslik}
                onChange={(e) => setManuelBaslik(e.target.value)}
                maxLength={300}
                className="w-full rounded-lg border border-border bg-card/60 px-3 py-2 text-sm text-foreground outline-none focus:border-primary/50"
              />
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs text-muted-foreground">Organizator (opsiyonel)</label>
                <input
                  value={manuelOrganizator}
                  onChange={(e) => setManuelOrganizator(e.target.value)}
                  className="w-full rounded-lg border border-border bg-card/60 px-3 py-2 text-sm text-foreground outline-none focus:border-primary/50"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-muted-foreground">Konu / Kategori (opsiyonel)</label>
                <input
                  value={manuelKonuKategori}
                  onChange={(e) => setManuelKonuKategori(e.target.value)}
                  className="w-full rounded-lg border border-border bg-card/60 px-3 py-2 text-sm text-foreground outline-none focus:border-primary/50"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-muted-foreground">Son Basvuru Tarihi (opsiyonel)</label>
                <input
                  value={manuelSonBasvuru}
                  onChange={(e) => setManuelSonBasvuru(e.target.value)}
                  placeholder="2026-08-01"
                  className="w-full rounded-lg border border-border bg-card/60 px-3 py-2 text-sm text-foreground outline-none focus:border-primary/50"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-muted-foreground">Yer / Mekan (opsiyonel)</label>
                <input
                  value={manuelYerMekan}
                  onChange={(e) => setManuelYerMekan(e.target.value)}
                  className="w-full rounded-lg border border-border bg-card/60 px-3 py-2 text-sm text-foreground outline-none focus:border-primary/50"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-muted-foreground">Odul Miktari / Turu (opsiyonel)</label>
                <input
                  value={manuelOdulMiktariTuru}
                  onChange={(e) => setManuelOdulMiktariTuru(e.target.value)}
                  className="w-full rounded-lg border border-border bg-card/60 px-3 py-2 text-sm text-foreground outline-none focus:border-primary/50"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-muted-foreground">Katilim Sartlari (opsiyonel)</label>
                <input
                  value={manuelKatilimSartlari}
                  onChange={(e) => setManuelKatilimSartlari(e.target.value)}
                  className="w-full rounded-lg border border-border bg-card/60 px-3 py-2 text-sm text-foreground outline-none focus:border-primary/50"
                />
              </div>
            </div>
            {manuelHata && <p className="text-xs text-destructive">{manuelHata}</p>}
            <button
              type="submit"
              disabled={manuelGonderiliyor}
              className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-all hover:brightness-110 disabled:opacity-60"
            >
              {manuelGonderiliyor && <Loader2 className="h-4 w-4 animate-spin" />}
              Firsati Kaydet
            </button>
          </form>
        </Reveal>
      )}

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

      <select
        value={seciliKonu}
        onChange={(e) => setSeciliKonu(e.target.value)}
        className="rounded-lg border border-border bg-card/60 px-3 py-1.5 text-xs text-foreground outline-none"
      >
        <option value="">Tum konular</option>
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
        <option value="">Tum turler</option>
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
        <option value="">Tum formatlar</option>
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
        <option value="">Tum ulkeler</option>
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
                  acBasvuruSecici(o)
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
                  {basvuruAcikId === o.id && !o.basvuruldu && (
                    <div
                      className="mt-3 space-y-2 rounded-xl border border-border bg-card/60 p-3"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <label className="block text-xs font-medium text-muted-foreground">
                        İlişkili proje (opsiyonel)
                      </label>
                      <select
                        value={basvuruSecim[o.id] ?? ""}
                        onChange={(e) => setBasvuruSecim((m) => ({ ...m, [o.id]: e.target.value }))}
                        className="w-full rounded-lg border border-border bg-background px-2 py-1.5 text-sm"
                      >
                        <option value="">Proje seçme</option>
                        {projeler.map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.ad}
                          </option>
                        ))}
                      </select>
                      {basvuruOnerisi[o.id]?.onerilenProjeAdi && (
                        <p className="text-xs text-muted-foreground">
                          Sudo önerisi:{" "}
                          <span className="font-medium text-foreground">
                            {basvuruOnerisi[o.id]?.onerilenProjeAdi}
                          </span>
                        </p>
                      )}
                      <div className="flex items-center gap-2 pt-1">
                        <button
                          type="button"
                          onClick={() => handleApply(o, basvuruSecim[o.id] || undefined)}
                          disabled={pending === o.id}
                          className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground transition-all hover:brightness-110"
                        >
                          {pending === o.id ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <Check className="h-3.5 w-3.5" />
                          )}
                          Onayla
                        </button>
                        <button
                          type="button"
                          onClick={() => setBasvuruAcikId(null)}
                          className="rounded-lg border border-border px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
                        >
                          Vazgeç
                        </button>
                      </div>
                    </div>
                  )}
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
              Sudola
            </button>
            {sudolaClicked && selected && <SudolaPanel link={selected.link} />}
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
