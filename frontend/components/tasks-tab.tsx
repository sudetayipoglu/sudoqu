"use client"

import { useState } from "react"
import { CalendarClock, Check, Loader2, Tag, User } from "lucide-react"
import { Reveal } from "@/components/reveal"
import { StatusBadge, statusTone } from "@/components/status-badge"
import { completeTask, type Task } from "@/lib/api"
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

export function TasksTab({
  items,
  onCompleted,
}: {
  items: Task[]
  onCompleted: (id: string) => void
}) {
  const [pending, setPending] = useState<string | null>(null)

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

  if (items.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-border bg-card/40 py-16 text-center text-sm text-muted-foreground">
        Henüz görev bulunamadı.
      </div>
    )
  }

  return (
    <ul className="grid gap-4 lg:grid-cols-2">
      {items.map((t, i) => {
        const dTone = deadlineTone(t.deadline, t.tamamlandi)
        return (
          <Reveal as="li" key={t.id} delay={Math.min(i * 60, 360)}>
            <article
              className={cn(
                "glow-hover flex h-full flex-col rounded-2xl border border-border bg-card/70 p-5 backdrop-blur",
                t.tamamlandi && "opacity-80",
              )}
            >
              <div className="mb-3 flex items-start justify-between gap-3">
                <h3
                  className={cn(
                    "text-pretty text-base font-semibold leading-snug text-foreground",
                    t.tamamlandi && "line-through decoration-success/60",
                  )}
                >
                  {t.baslik}
                </h3>
                <StatusBadge tone={t.tamamlandi ? "success" : statusTone(t.durum)}>
                  {t.tamamlandi ? "Tamamlandı" : t.durum || "Beklemede"}
                </StatusBadge>
              </div>

              <dl className="grid grid-cols-1 gap-2 text-sm sm:grid-cols-3">
                <Meta icon={<User className="h-3.5 w-3.5" />} label="Atanan" value={t.atanan || "—"} />
                <Meta icon={<Tag className="h-3.5 w-3.5" />} label="Tür" value={t.tur || "—"} />
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
            </article>
          </Reveal>
        )
      })}
    </ul>
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
