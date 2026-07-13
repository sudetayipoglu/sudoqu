"use client"

import { useState } from "react"
import { ArrowUpRight, FileText, ArrowLeft, Loader2 } from "lucide-react"
import { Reveal } from "@/components/reveal"
import { StatusBadge } from "@/components/status-badge"
import { type Application, updateApplicationStatus } from "@/lib/api"

const DURUM_SECENEKLERI: { value: string; label: string; tone: "warning" | "success" | "primary" }[] = [
  { value: "beklemede", label: "Beklemede", tone: "warning" },
  { value: "kazandi", label: "Kazandı", tone: "success" },
  { value: "kaybetti", label: "Kaybetti", tone: "primary" },
]

function durumTon(durum: string): "warning" | "success" | "primary" | "muted" {
  const found = DURUM_SECENEKLERI.find((d) => d.value === durum)
  return found ? found.tone : "muted"
}

function durumEtiket(durum: string): string {
  const found = DURUM_SECENEKLERI.find((d) => d.value === durum)
  return found ? found.label : durum || "Gönderildi"
}

export function ApplicationsTab({
  items,
  onChanged,
  onGoToOpportunity,
}: {
  items: Application[]
  onChanged: () => void
  onGoToOpportunity: (link: string) => void
}) {
  const [guncelleniyor, setGuncelleniyor] = useState<string | null>(null)
  const [hata, setHata] = useState<string | null>(null)

  async function handleDurumDegistir(link: string, yeniDurum: string) {
    setGuncelleniyor(link)
    setHata(null)
    try {
      await updateApplicationStatus(link, yeniDurum)
      onChanged()
    } catch (e) {
      setHata(e instanceof Error ? e.message : "Durum güncellenemedi")
    } finally {
      setGuncelleniyor(null)
    }
  }

  if (items.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-border bg-card/40 py-16 text-center text-sm text-muted-foreground">
        Henüz başvurun yok. Fırsatlar sekmesinden bir fırsatı başvur olarak işaretle.
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {hata && <p className="text-xs text-destructive">{hata}</p>}
      <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {items.map((a, i) => (
          <Reveal as="li" key={a.id} delay={Math.min(i * 60, 360)}>
            <article className="glow-hover flex h-full flex-col rounded-2xl border border-border bg-card/70 p-5 backdrop-blur">
              <div className="mb-3 flex items-start justify-between gap-3">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-cyan/15 text-cyan">
                  <FileText className="h-4 w-4" />
                </span>
                <StatusBadge tone={durumTon(a.durum)}>{durumEtiket(a.durum)}</StatusBadge>
              </div>

              <h3 className="text-pretty text-base font-semibold leading-snug text-foreground">
                {a.baslik}
              </h3>

              {a.link && (
                <a
                  href={a.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-2 inline-flex items-center gap-1 truncate pt-1 text-sm text-cyan transition-colors hover:text-primary"
                >
                  <span className="truncate">{a.link.replace(/^https?:\/\//, "")}</span>
                  <ArrowUpRight className="h-3.5 w-3.5 shrink-0" />
                </a>
              )}

              <div className="mt-auto flex flex-wrap items-center gap-2 pt-4">
                <select
                  value={a.durum || "beklemede"}
                  disabled={guncelleniyor === a.link}
                  onChange={(e) => handleDurumDegistir(a.link, e.target.value)}
                  className="rounded-lg border border-border bg-card/60 px-2 py-1.5 text-xs text-foreground outline-none focus:border-primary/50"
                >
                  {DURUM_SECENEKLERI.map((d) => (
                    <option key={d.value} value={d.value}>
                      {d.label}
                    </option>
                  ))}
                </select>
                {guncelleniyor === a.link && <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />}

                <button
                  type="button"
                  onClick={() => onGoToOpportunity(a.link)}
                  className="ml-auto inline-flex items-center gap-1 rounded-lg border border-border bg-card/60 px-2.5 py-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
                >
                  <ArrowLeft className="h-3.5 w-3.5" />
                  Fırsata dön
                </button>
              </div>
            </article>
          </Reveal>
        ))}
      </ul>
    </div>
  )
}
