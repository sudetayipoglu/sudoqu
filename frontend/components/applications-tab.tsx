"use client"

import { ArrowUpRight, FileText } from "lucide-react"
import { Reveal } from "@/components/reveal"
import { StatusBadge, statusTone } from "@/components/status-badge"
import { type Application } from "@/lib/api"

export function ApplicationsTab({ items }: { items: Application[] }) {
  if (items.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-border bg-card/40 py-16 text-center text-sm text-muted-foreground">
        Henüz başvurun yok. Fırsatlar sekmesinden bir fırsatı başvur olarak işaretle.
      </div>
    )
  }

  return (
    <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {items.map((a, i) => (
        <Reveal as="li" key={a.id} delay={Math.min(i * 60, 360)}>
          <article className="glow-hover flex h-full flex-col rounded-2xl border border-border bg-card/70 p-5 backdrop-blur">
            <div className="mb-3 flex items-start justify-between gap-3">
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-cyan/15 text-cyan">
                <FileText className="h-4 w-4" />
              </span>
              <StatusBadge tone={statusTone(a.durum)}>{a.durum || "Gönderildi"}</StatusBadge>
            </div>

            <h3 className="text-pretty text-base font-semibold leading-snug text-foreground">
              {a.baslik}
            </h3>

            {a.link && (
              <a
                href={a.link}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-auto inline-flex items-center gap-1 truncate pt-3 text-sm text-cyan transition-colors hover:text-primary"
              >
                <span className="truncate">{a.link.replace(/^https?:\/\//, "")}</span>
                <ArrowUpRight className="h-3.5 w-3.5 shrink-0" />
              </a>
            )}
          </article>
        </Reveal>
      ))}
    </ul>
  )
}
