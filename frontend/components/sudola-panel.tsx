"use client"

import { useState } from "react"
import { Send, Loader2, Sparkles, TrendingUp } from "lucide-react"
import { sudolaSoru, sudolaOneri, type SudolaOneri } from "@/lib/api"
import { cn } from "@/lib/utils"

interface Mesaj {
  rol: "kullanici" | "sudola"
  metin: string
}

export function SudolaPanel({ link }: { link: string }) {
  const [mesajlar, setMesajlar] = useState<Mesaj[]>([])
  const [soru, setSoru] = useState("")
  const [gonderiliyor, setGonderiliyor] = useState(false)
  const [hata, setHata] = useState<string | null>(null)

  const [oneri, setOneri] = useState<SudolaOneri | null>(null)
  const [oneriYukleniyor, setOneriYukleniyor] = useState(false)
  const [oneriHata, setOneriHata] = useState<string | null>(null)

  async function gonder() {
    const q = soru.trim()
    if (!q || gonderiliyor) return
    setHata(null)
    setGonderiliyor(true)
    setMesajlar((m) => [...m, { rol: "kullanici", metin: q }])
    setSoru("")
    try {
      const cevap = await sudolaSoru(link, q)
      setMesajlar((m) => [...m, { rol: "sudola", metin: cevap }])
    } catch (e) {
      setHata(e instanceof Error ? e.message : "Sudo su an cevap veremedi")
    } finally {
      setGonderiliyor(false)
    }
  }

  async function oneriAl() {
    setOneriYukleniyor(true)
    setOneriHata(null)
    try {
      const sonuc = await sudolaOneri(link)
      setOneri(sonuc)
    } catch (e) {
      setOneriHata(e instanceof Error ? e.message : "Oneri alinamadi")
    } finally {
      setOneriYukleniyor(false)
    }
  }

  return (
    <div className="mt-4 space-y-3 rounded-xl border border-border bg-card/40 p-3">
      <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
        <Sparkles className="h-3.5 w-3.5" /> Sudo ile sohbet et
      </div>

      {mesajlar.length === 0 && (
        <p className="text-xs text-muted-foreground">
          Bu firsatla ilgili merak ettigini sor - Sudo, firsatin bilgilerine, organizator profiline, agirlikli yatirim yaptigi sektore ve gecmis kazananlar arastirmasina dayanarak cevaplar.
        </p>
      )}

      <div className="max-h-64 space-y-2 overflow-y-auto">
        {mesajlar.map((m, i) => (
          <div
            key={i}
            className={cn(
              "max-w-[90%] rounded-lg px-3 py-2 text-xs",
              m.rol === "kullanici"
                ? "ml-auto bg-primary/15 text-foreground"
                : "bg-border/40 text-foreground",
            )}
          >
            {m.metin}
          </div>
        ))}
        {gonderiliyor && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Loader2 className="h-3.5 w-3.5 animate-spin" /> Sudo dusunuyor...
          </div>
        )}
      </div>

      {hata && <p className="text-xs text-destructive">{hata}</p>}

      <div className="flex gap-2">
        <input
          value={soru}
          onChange={(e) => setSoru(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") gonder()
          }}
          placeholder="Sudolayabildiklerimizden misiniz sudolayamadıklarımızdan mısınız?"
          maxLength={1000}
          className="flex-1 rounded-lg border border-border bg-card/60 px-3 py-2 text-xs text-foreground outline-none focus:border-primary/50"
        />
        <button
          type="button"
          onClick={gonder}
          disabled={gonderiliyor || !soru.trim()}
          className="rounded-lg bg-primary px-3 py-2 text-primary-foreground disabled:opacity-40"
        >
          <Send className="h-3.5 w-3.5" />
        </button>
      </div>

      <div className="border-t border-border/60 pt-3">
        <button
          type="button"
          onClick={oneriAl}
          disabled={oneriYukleniyor}
          className="flex items-center gap-2 rounded-lg border border-border bg-card/60 px-3 py-2 text-xs font-medium text-foreground transition-colors hover:border-primary/50 disabled:opacity-40"
        >
          {oneriYukleniyor ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <TrendingUp className="h-3.5 w-3.5" />
          )}
          Proje Uygunluk Onerisi Al
        </button>

        {oneriHata && <p className="mt-2 text-xs text-destructive">{oneriHata}</p>}

        {oneri && (
          <div className="mt-3 space-y-2 rounded-lg bg-border/30 p-3 text-xs">
            <div className="flex items-center gap-2">
              <span className="text-lg font-semibold text-primary">{oneri.skor}</span>
              <span className="text-muted-foreground">/ 100 uygunluk skoru</span>
            </div>
            <p className="text-foreground">{oneri.aciklama}</p>
            {oneri.gucluYonler.length > 0 && (
              <div>
                <p className="font-medium text-success">Guclu yonler:</p>
                <ul className="list-inside list-disc text-muted-foreground">
                  {oneri.gucluYonler.map((g, i) => (
                    <li key={i}>{g}</li>
                  ))}
                </ul>
              </div>
            )}
            {oneri.riskler.length > 0 && (
              <div>
                <p className="font-medium text-warning">Riskler:</p>
                <ul className="list-inside list-disc text-muted-foreground">
                  {oneri.riskler.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
