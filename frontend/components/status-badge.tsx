import { cn } from "@/lib/utils"

type Tone = "primary" | "cyan" | "success" | "warning" | "purple" | "muted"

const toneMap: Record<Tone, string> = {
  primary: "bg-primary/15 text-primary border-primary/30",
  cyan: "bg-cyan/15 text-cyan border-cyan/30",
  success: "bg-success/15 text-success border-success/30",
  warning: "bg-warning/15 text-warning border-warning/30",
  purple: "bg-purple/15 text-purple border-purple/30",
  muted: "bg-muted text-muted-foreground border-border",
}

export function statusTone(durum: string): Tone {
  const s = durum.toLowerCase()
  if (/(tamam|complete|done|kabul|accept|onay|approved)/.test(s)) return "success"
  if (/(bekle|pending|inceleme|review|değerlend|degerlend)/.test(s)) return "warning"
  if (/(red|reject|iptal|cancel)/.test(s)) return "primary"
  if (/(devam|progress|aktif|active)/.test(s)) return "cyan"
  return "muted"
}

export function StatusBadge({
  children,
  tone = "muted",
  className,
}: {
  children: React.ReactNode
  tone?: Tone
  className?: string
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize",
        toneMap[tone],
        className,
      )}
    >
      {children}
    </span>
  )
}
