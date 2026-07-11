import json
import os
from datetime import datetime

TASKLAR_DOSYA = "tasklar.json"
EKIP_DOSYA = "ekip.json"

def ekibi_yukle():
    if os.path.exists(EKIP_DOSYA):
        with open(EKIP_DOSYA, encoding="utf-8") as f:
            return json.load(f)
    return []

def ekibi_kaydet(ekip):
    with open(EKIP_DOSYA, "w", encoding="utf-8") as f:
        json.dump(ekip, f, ensure_ascii=False, indent=2)

def taskları_yukle():
    if os.path.exists(TASKLAR_DOSYA):
        with open(TASKLAR_DOSYA, encoding="utf-8") as f:
            return json.load(f)
    return []

def taskları_kaydet(tasklar):
    with open(TASKLAR_DOSYA, "w", encoding="utf-8") as f:
        json.dump(tasklar, f, ensure_ascii=False, indent=2)

def yeni_task_ekle(tasklar, ekip):
    if not ekip:
        print("Önce ekip listesine en az bir kişi eklemelisin (menü seçeneği 5).")
        return

    baslik = input("Task/toplantı başlığı: ")

    print("Kime atanıyor?")
    for i, kisi in enumerate(ekip):
        print(f"  [{i}] {kisi}")
    kisi_idx = input("Seçim: ")
    atanan = ekip[int(kisi_idx)] if kisi_idx.strip().isdigit() and int(kisi_idx) < len(ekip) else "belirsiz"

    tur = input("Tür (task/toplanti): ").strip().lower()
    if tur not in ["task", "toplanti"]:
        tur = "task"

    deadline = input("Tarih (YYYY-AA-GG, boş bırakılabilir): ").strip()

    yeni = {
        "id": len(tasklar) + 1,
        "baslik": baslik,
        "atanan": atanan,
        "tur": tur,
        "deadline": deadline if deadline else None,
        "durum": "bekliyor",
        "olusturma_tarihi": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    tasklar.append(yeni)
    taskları_kaydet(tasklar)
    print(f"\n'{baslik}' eklendi → {atanan} | {tur} | deadline: {deadline or 'yok'}")

def taskları_listele(tasklar):
    if not tasklar:
        print("Henüz hiç task/toplantı yok.")
        return
    for t in tasklar:
        durum_isareti = "✓" if t["durum"] == "tamamlandı" else "○"
        deadline_str = f" | Deadline: {t['deadline']}" if t["deadline"] else ""
        print(f"[{t['id']}] {durum_isareti} {t['baslik']} | {t['atanan']} | {t['tur']}{deadline_str}")

def tamamlandi_isaretle(tasklar):
    taskları_listele(tasklar)
    tid = input("\nTamamlandı olarak işaretlenecek task ID: ")
    if tid.strip().isdigit():
        for t in tasklar:
            if t["id"] == int(tid):
                t["durum"] = "tamamlandı"
                taskları_kaydet(tasklar)
                print(f"'{t['baslik']}' tamamlandı olarak işaretlendi.")
                return
    print("Bulunamadı.")

def ekip_yonet(ekip):
    print("\nMevcut ekip:", ", ".join(ekip) if ekip else "(boş)")
    print("1) Yeni kişi ekle")
    print("2) Kişi çıkar")
    print("3) Geri dön")
    secim = input("Seçim: ")

    if secim == "1":
        isim = input("Eklenecek kişinin adı: ").strip()
        if isim and isim not in ekip:
            ekip.append(isim)
            ekibi_kaydet(ekip)
            print(f"'{isim}' ekibe eklendi.")
    elif secim == "2":
        for i, kisi in enumerate(ekip):
            print(f"  [{i}] {kisi}")
        idx = input("Çıkarılacak kişinin numarası: ")
        if idx.strip().isdigit() and int(idx) < len(ekip):
            cikan = ekip.pop(int(idx))
            ekibi_kaydet(ekip)
            print(f"'{cikan}' ekipten çıkarıldı.")

def menu():
    tasklar = taskları_yukle()
    ekip = ekibi_yukle()

    print("\n=== SudoQu Task & Takvim ===")
    print("1) Yeni task/toplantı ekle")
    print("2) Tüm task/toplantıları listele")
    print("3) Task tamamlandı işaretle")
    print("4) Çıkış")
    print("5) Ekibi yönet (ekle/çıkar)")
    secim = input("Seçim: ")

    if secim == "1":
        yeni_task_ekle(tasklar, ekip)
    elif secim == "2":
        taskları_listele(tasklar)
    elif secim == "3":
        tamamlandi_isaretle(tasklar)
    elif secim == "4":
        return
    elif secim == "5":
        ekip_yonet(ekip)

    menu()

if __name__ == "__main__":
    menu()
