"use client"

import { ArrowUpRight, Layers } from "lucide-react"
import { Reveal } from "@/components/reveal"
import { type Opportunity } from "@/lib/api"

export function GenelSayfalarTab({ items }: { items: Opportunity[] }) {
  if (items.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-border bg-card/40 py-16 text-center text-sm text-muted-foreground">
        Şu an genel sayfa olarak işaretlenmiş kayıt yok.
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <p className="text-xs text-muted-foreground">
        Bu sayfalar tek bir fırsat değil, birden çok fırsatı listeleyen genel/liste sayfaları olduğu
        için otomatik ayrıştırılamadı. Bu yüzden Fırsatlar sekmesinde gösterilmiyorlar; linke tıklayıp
        elle inceleyebilirsin.
      </p>
      <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {items.map((o, i) => (
          <Reveal as="li" key={o.id} delay={Math.min(i * 60, 360)}>
            <article className="glow-hover flex h-full flex-col rounded-2xl border border-border bg-card/70 p-5 backdrop-blur">
              <span className="mb-3 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-cyan/15 text-cyan">
                <Layers className="h-4 w-4" />
              </span>

              <h3 className="text-pretty text-base font-semibold leading-snug text-foreground">
                {o.baslik}
              </h3>

              {o.link && (
                <a
                  href={o.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-2 inline-flex items-center gap-1 truncate pt-1 text-sm text-cyan transition-colors hover:text-primary"
                >
                  <span className="truncate">{o.link.replace(/^https?:\/\//, "")}</span>
                  <ArrowUpRight className="h-3.5 w-3.5 shrink-0" />
                </a>
              )}

              <div className="mt-auto flex flex-wrap items-center gap-2 pt-4 text-xs text-muted-foreground">
                {o.bulunmaTarihi && <span>Bulunma: {o.bulunmaTarihi}</span>}
                {typeof o.raw.kaynak_sorgu === "string" && o.raw.kaynak_sorgu && (
                  <span>· Sorgu: {o.raw.kaynak_sorgu}</span>
                )}
              </div>
            </article>
          </Reveal>
        ))}
      </ul>
    </div>
  )
}
