"use client"

import { useState } from "react"
import useSWR from "swr"
import { AlertTriangle, CalendarCheck, FileText, Loader2, RefreshCw, Sparkles, Target } from "lucide-react"
import { Reveal } from "@/components/reveal"
import { OpportunitiesTab } from "@/components/opportunities-tab"
import { TasksTab } from "@/components/tasks-tab"
import { ApplicationsTab } from "@/components/applications-tab"
import {
  getApplications,
  getOpportunities,
  getTasks,
  type Application,
  type Opportunity,
  type Task,
} from "@/lib/api"
import { cn } from "@/lib/utils"

type TabKey = "firsatlar" | "tasklar" | "basvurular"

const TABS: { key: TabKey; label: string; icon: typeof Target }[] = [
  { key: "firsatlar", label: "Fırsatlar", icon: Target },
  { key: "tasklar", label: "Task & Takvim", icon: CalendarCheck },
  { key: "basvurular", label: "Başvurularım", icon: FileText },
]

export function Dashboard() {
  const [tab, setTab] = useState<TabKey>("firsatlar")

  const opportunities = useSWR<Opportunity[]>("firsatlar", getOpportunities)
  const tasks = useSWR<Task[]>("tasklar", getTasks)
  const applications = useSWR<Application[]>("basvurular", getApplications)

  const opps = opportunities.data ?? []
  const taskList = tasks.data ?? []
  const apps = applications.data ?? []

  const openTasks = taskList.filter((t) => !t.tamamlandi).length

  function handleApplied(id: string) {
    opportunities.mutate(
      (prev) => (prev ?? []).map((o) => (o.id === id ? { ...o, basvuruldu: true } : o)),
      { revalidate: false },
    )
    applications.mutate()
  }

  function handleCompleted(id: string) {
    tasks.mutate(
      (prev) => (prev ?? []).map((t) => (t.id === id ? { ...t, tamamlandi: true, durum: "tamamlandı" } : t)),
      { revalidate: false },
    )
  }

  function refreshAll() {
    opportunities.mutate()
    tasks.mutate()
    applications.mutate()
  }

  const anyLoading = opportunities.isLoading || tasks.isLoading || applications.isLoading
  const activeError =
    tab === "firsatlar" ? opportunities.error : tab === "tasklar" ? tasks.error : applications.error

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 lg:py-12">
      {/* Header */}
      <Reveal as="header" className="mb-8">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <span className="glow-primary flex h-11 w-11 items-center justify-center rounded-xl bg-primary/15 text-primary">
              <Sparkles className="h-5 w-5" />
            </span>
            <div>
              <h1 className="font-mono text-xl font-semibold tracking-tight text-foreground">
                Sudo<span className="text-primary">Qu</span>
              </h1>
              <p className="text-sm text-muted-foreground">Fırsat & ekip kontrol paneli</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={refreshAll}
              className="inline-flex h-11 w-11 items-center justify-center rounded-xl border border-border bg-card/60 text-muted-foreground transition-colors hover:border-primary/40 hover:text-primary"
              aria-label="Verileri yenile"
            >
              <RefreshCw className={cn("h-4 w-4", anyLoading && "animate-spin")} />
            </button>

            <div className="glow-hover flex items-center gap-3 rounded-2xl border border-border bg-card/70 px-4 py-2.5 backdrop-blur">
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan/15 text-cyan">
                <Target className="h-4 w-4" />
              </span>
              <div>
                <div className="text-2xl font-semibold leading-none text-gradient">{opps.length}</div>
                <div className="text-[11px] uppercase tracking-wide text-muted-foreground">Toplam Fırsat</div>
              </div>
            </div>
          </div>
        </div>

        {/* Mini stats */}
        <div className="mt-6 grid grid-cols-3 gap-3">
          <StatChip label="Açık görev" value={openTasks} tone="warning" />
          <StatChip label="Başvuru" value={apps.length} tone="cyan" />
          <StatChip
            label="Başvurulan fırsat"
            value={opps.filter((o) => o.basvuruldu).length}
            tone="success"
          />
        </div>
      </Reveal>

      {/* Tabs */}
      <Reveal className="mb-8">
        <div className="inline-flex w-full flex-wrap gap-1 rounded-2xl border border-border bg-card/50 p-1 backdrop-blur sm:w-auto">
          {TABS.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              type="button"
              onClick={() => setTab(key)}
              className={cn(
                "inline-flex flex-1 items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition-all sm:flex-none",
                tab === key
                  ? "bg-primary text-primary-foreground glow-primary"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </div>
      </Reveal>

      {/* Content */}
      {anyLoading && tab === "firsatlar" && opps.length === 0 ? (
        <LoadingState />
      ) : activeError ? (
        <ErrorState onRetry={refreshAll} />
      ) : (
        <section>
          {tab === "firsatlar" && <OpportunitiesTab items={opps} onApplied={handleApplied} />}
          {tab === "tasklar" && <TasksTab items={taskList} onCompleted={handleCompleted} />}
          {tab === "basvurular" && <ApplicationsTab items={apps} />}
        </section>
      )}
    </div>
  )
}

function StatChip({
  label,
  value,
  tone,
}: {
  label: string
  value: number
  tone: "warning" | "cyan" | "success"
}) {
  const toneClass = {
    warning: "text-warning",
    cyan: "text-cyan",
    success: "text-success",
  }[tone]
  return (
    <div className="rounded-xl border border-border bg-card/50 px-4 py-3 backdrop-blur">
      <div className={cn("text-lg font-semibold leading-none", toneClass)}>{value}</div>
      <div className="mt-1 text-[11px] uppercase tracking-wide text-muted-foreground">{label}</div>
    </div>
  )
}

function LoadingState() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-border bg-card/40 py-20 text-muted-foreground">
      <Loader2 className="h-6 w-6 animate-spin text-primary" />
      <p className="text-sm">Veriler yükleniyor...</p>
    </div>
  )
}

function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 rounded-2xl border border-destructive/30 bg-destructive/5 py-16 text-center">
      <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-destructive/15 text-destructive">
        <AlertTriangle className="h-5 w-5" />
      </span>
      <div className="max-w-sm px-6">
        <p className="font-medium text-foreground">Verilere ulaşılamadı</p>
        <p className="mt-1 text-sm text-muted-foreground">
          API sunucusuna bağlanılamadı. Sunucunun çalıştığından ve CORS ayarlarının doğru olduğundan emin ol.
        </p>
      </div>
      <button
        type="button"
        onClick={onRetry}
        className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-all hover:brightness-110 glow-primary"
      >
        <RefreshCw className="h-4 w-4" /> Tekrar dene
      </button>
    </div>
  )
}
