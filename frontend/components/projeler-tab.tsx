"use client"

import { useState } from "react"
import { FolderGit2, ExternalLink, Star, Upload, Download, Plus, X, Loader2, Trash2 } from "lucide-react"
import { Reveal } from "@/components/reveal"
import { StatusBadge } from "@/components/status-badge"
import {
  addProjeNot,
  createProje,
  deleteProje,
  projeDosyaUrl,
  updateProjeDurum,
  uploadProjeDosya,
  type Proje,
} from "@/lib/api"
import { cn } from "@/lib/utils"

const DURUM_TONE: Record<string, "success" | "warning" | "muted" | "primary"> = {
  aktif: "primary",
  tamamlandi: "success",
  beklemede: "warning",
}

export function ProjelerTab({ items, onChanged }: { items: Proje[]; onChanged: () => void }) {
  const [formAcik, setFormAcik] = useState(false)
  const [ad, setAd] = useState("")
  const [aciklama, setAciklama] = useState("")
  const [githubLink, setGithubLink] = useState("")
  const [gonderiliyor, setGonderiliyor] = useState(false)
  const [hata, setHata] = useState<string | null>(null)
  const [secili, setSecili] = useState<Proje | null>(null)
  const [notMetni, setNotMetni] = useState("")
  const [notGonderiliyor, setNotGonderiliyor] = useState(false)
  const [siliniyor, setSiliniyor] = useState<string | null>(null)
  const [dosyaYukleniyor, setDosyaYukleniyor] = useState(false)
  const [dosyaHata, setDosyaHata] = useState<string | null>(null)

  async function handleEkle(e: React.FormEvent) {
    e.preventDefault()
    if (!ad.trim()) {
      setHata("Proje adi bos olamaz")
      return
    }
    setGonderiliyor(true)
    setHata(null)
    try {
      await createProje(ad.trim(), aciklama.trim(), githubLink.trim())
      setAd("")
      setAciklama("")
      setGithubLink("")
      setFormAcik(false)
      onChanged()
    } catch (err) {
      setHata(err instanceof Error ? err.message : "Proje eklenemedi")
    } finally {
      setGonderiliyor(false)
    }
  }

  async function handleDurumDegistir(proje: Proje, yeniDurum: string) {
    await updateProjeDurum(proje.id, yeniDurum)
    onChanged()
    if (secili?.id === proje.id) {
      setSecili({ ...proje, durum: yeniDurum })
    }
  }

  async function handleSil(proje: Proje, e: React.MouseEvent) {
    e.stopPropagation()
    if (
      !window.confirm(
        `"${proje.ad}" projesini silmek istediginize emin misiniz? Bu islem geri alinamaz. (Iliskili gorevler ve basvurular silinmeyecek, sadece bu projeyle baglantilari kaldirilacak.)`,
      )
    )
      return
    setSiliniyor(proje.id)
    try {
      await deleteProje(proje.id)
      if (secili?.id === proje.id) setSecili(null)
      onChanged()
    } catch (err) {
      alert(err instanceof Error ? err.message : "Proje silinemedi")
    } finally {
      setSiliniyor(null)
    }
  }

  async function handleNotEkle() {
    if (!secili || !notMetni.trim()) return
    setNotGonderiliyor(true)
    try {
      await addProjeNot(secili.id, notMetni.trim())
      setNotMetni("")
      onChanged()
    } finally {
      setNotGonderiliyor(false)
    }
  }

  async function handleDosyaSec(e: React.ChangeEvent<HTMLInputElement>) {
    if (!secili) return
    const file = e.target.files?.[0]
    if (!file) return
    setDosyaYukleniyor(true)
    setDosyaHata(null)
    try {
      await uploadProjeDosya(secili.id, file)
      onChanged()
    } catch (err) {
      setDosyaHata(err instanceof Error ? err.message : "Dosya yuklenemedi")
    } finally {
      setDosyaYukleniyor(false)
      e.target.value = ""
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium text-muted-foreground">Projelerimiz</h2>
        <button
          type="button"
          onClick={() => setFormAcik((v) => !v)}
          className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-all hover:brightness-110"
        >
          {formAcik ? <X className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
          {formAcik ? "Vazgec" : "Yeni Proje"}
        </button>
      </div>

      {formAcik && (
        <Reveal className="rounded-2xl border border-border bg-card/60 p-5 backdrop-blur">
          <form onSubmit={handleEkle} className="space-y-3">
            <div>
              <label className="mb-1 block text-xs text-muted-foreground">Proje adi</label>
              <input
                value={ad}
                onChange={(e) => setAd(e.target.value)}
                maxLength={200}
                className="w-full rounded-lg border border-border bg-card/60 px-3 py-2 text-sm text-foreground outline-none focus:border-primary/50"
                placeholder="orn. SudoQu"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-muted-foreground">Aciklama</label>
              <textarea
                value={aciklama}
                onChange={(e) => setAciklama(e.target.value)}
                maxLength={5000}
                rows={2}
                className="w-full rounded-lg border border-border bg-card/60 px-3 py-2 text-sm text-foreground outline-none focus:border-primary/50"
                placeholder="Kisa proje aciklamasi"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-muted-foreground">GitHub linki (opsiyonel)</label>
              <input
                value={githubLink}
                onChange={(e) => setGithubLink(e.target.value)}
                className="w-full rounded-lg border border-border bg-card/60 px-3 py-2 text-sm text-foreground outline-none focus:border-primary/50"
                placeholder="https://github.com/kullanici/repo"
              />
            </div>
            {hata && <p className="text-xs text-destructive">{hata}</p>}
            <button
              type="submit"
              disabled={gonderiliyor}
              className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-all hover:brightness-110 disabled:opacity-60"
            >
              {gonderiliyor && <Loader2 className="h-4 w-4 animate-spin" />}
              Projeyi Kaydet
            </button>
          </form>
        </Reveal>
      )}

      {items.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-border bg-card/40 py-20 text-center text-muted-foreground">
          <FolderGit2 className="h-6 w-6" />
          <p className="text-sm">Henuz proje eklenmedi.</p>
        </div>
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {items.map((p) => (
            <Reveal as="li" key={p.id}>
              <article
                onClick={() => setSecili(p)}
                className="glow-hover group flex h-full cursor-pointer flex-col rounded-2xl border border-border bg-card/70 p-5 backdrop-blur"
              >
                <div className="mb-3 flex items-start justify-between gap-3">
                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/15 text-primary">
                    <FolderGit2 className="h-4 w-4" />
                  </span>
                  <StatusBadge tone={DURUM_TONE[p.durum] ?? "muted"}>{p.durum}</StatusBadge>
                  <button
                    type="button"
                    onClick={(e) => handleSil(p, e)}
                    disabled={siliniyor === p.id}
                    title="Projeyi sil"
                    className="ml-auto rounded-md p-1.5 text-muted-foreground opacity-0 transition group-hover:opacity-100 hover:bg-destructive/10 hover:text-destructive disabled:opacity-60"
                  >
                    {siliniyor === p.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Trash2 className="h-3.5 w-3.5" />}
                  </button>
                </div>
                <h3 className="text-pretty text-lg font-semibold leading-snug text-foreground">{p.ad}</h3>
                {p.aciklama && <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{p.aciklama}</p>}
                {p.githubLink && (
                  <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
                    <ExternalLink className="h-3.5 w-3.5" />
                    {p.githubBilgi?.yildizSayisi != null && (
                      <span className="inline-flex items-center gap-1">
                        <Star className="h-3 w-3" /> {p.githubBilgi.yildizSayisi}
                      </span>
                    )}
                    {p.githubBilgi?.dil && <span>{p.githubBilgi.dil}</span>}
                  </div>
                )}
                <div className="mt-3 flex items-center gap-3 text-xs text-muted-foreground">
                  <span>{p.notlar.length} not</span>
                  <span>{p.dosyalar.length} dosya</span>
                </div>
              </article>
            </Reveal>
          ))}
        </ul>
      )}

      {secili && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
          onClick={() => setSecili(null)}
        >
          <div
            className="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-2xl border border-border bg-card p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-4 flex items-start justify-between gap-3">
              <div>
                <h3 className="text-lg font-semibold text-foreground">{secili.ad}</h3>
                {secili.aciklama && <p className="mt-1 text-sm text-muted-foreground">{secili.aciklama}</p>}
              </div>
              <button type="button" onClick={() => setSecili(null)} className="text-muted-foreground hover:text-foreground">
                <X className="h-5 w-5" />
              </button>
            </div>

            {secili.githubLink && (
              <div className="mb-4 rounded-xl border border-border bg-card/60 p-3 text-xs">
                <a href={secili.githubLink} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 text-primary hover:underline">
                  <ExternalLink className="h-3.5 w-3.5" /> {secili.githubLink}
                </a>
                {secili.githubBilgi?.hata ? (
                  <p className="mt-1 text-destructive">{secili.githubBilgi.hata}</p>
                ) : secili.githubBilgi ? (
                  <div className="mt-2 space-y-1 text-muted-foreground">
                    <p>Yildiz: {secili.githubBilgi.yildizSayisi ?? "-"} | Dil: {secili.githubBilgi.dil ?? "-"}</p>
                    {secili.githubBilgi.sonCommit && (
                      <p className="truncate">Son commit: {secili.githubBilgi.sonCommit.mesaj} ({secili.githubBilgi.sonCommit.yazar})</p>
                    )}
                  </div>
                ) : null}
              </div>
            )}

            <div className="mb-4 flex flex-wrap gap-2">
              {["aktif", "beklemede", "tamamlandi"].map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => handleDurumDegistir(secili, d)}
                  className={cn(
                    "rounded-full border px-3 py-1 text-xs transition-colors",
                    secili.durum === d
                      ? "border-primary/50 bg-primary/15 text-primary"
                      : "border-border bg-card/60 text-muted-foreground hover:text-foreground",
                  )}
                >
                  {d}
                </button>
              ))}
            </div>

            <div className="mb-4">
              <h4 className="mb-2 text-xs uppercase tracking-wide text-muted-foreground">Notlar</h4>
              <div className="mb-2 max-h-40 space-y-2 overflow-y-auto">
                {secili.notlar.length === 0 && <p className="text-xs text-muted-foreground">Henuz not yok.</p>}
                {secili.notlar.map((n, i) => (
                  <div key={i} className="rounded-lg border border-border bg-card/60 p-2 text-xs">
                    <p className="text-muted-foreground">{n.tarih}</p>
                    <p className="text-foreground">{n.metin}</p>
                  </div>
                ))}
              </div>
              <div className="flex gap-2">
                <input
                  value={notMetni}
                  onChange={(e) => setNotMetni(e.target.value)}
                  maxLength={5000}
                  placeholder="Yeni not ekle..."
                  className="flex-1 rounded-lg border border-border bg-card/60 px-3 py-1.5 text-xs text-foreground outline-none focus:border-primary/50"
                />
                <button
                  type="button"
                  onClick={handleNotEkle}
                  disabled={notGonderiliyor || !notMetni.trim()}
                  className="rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground disabled:opacity-60"
                >
                  Ekle
                </button>
              </div>
            </div>

            <div>
              <h4 className="mb-2 text-xs uppercase tracking-wide text-muted-foreground">Dosyalar</h4>
              <div className="mb-2 space-y-1">
                {secili.dosyalar.length === 0 && <p className="text-xs text-muted-foreground">Henuz dosya yok.</p>}
                {secili.dosyalar.map((d, i) => (
                  <a
                    key={i}
                    href={projeDosyaUrl(secili.id, d.ad)}
                    className="flex items-center justify-between rounded-lg border border-border bg-card/60 px-3 py-1.5 text-xs text-foreground hover:border-primary/40"
                  >
                    <span className="truncate">{d.ad}</span>
                    <Download className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                  </a>
                ))}
              </div>
              <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg border border-border bg-card/60 px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground">
                {dosyaYukleniyor ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Upload className="h-3.5 w-3.5" />}
                Dosya yukle (pdf, docx, png, jpg, zip - maks 10MB)
                <input type="file" className="hidden" onChange={handleDosyaSec} disabled={dosyaYukleniyor} />
              </label>
              {dosyaHata && <p className="mt-1 text-xs text-destructive">{dosyaHata}</p>}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
