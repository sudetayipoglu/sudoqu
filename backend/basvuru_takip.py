import json
import os

FIRSATLAR_DOSYA = "firsatlar.json"
BASVURULAR_DOSYA = "basvurular.json"

def firsatlari_yukle():
    with open(FIRSATLAR_DOSYA, encoding="utf-8") as f:
        return json.load(f)

def basvurulari_yukle():
    if os.path.exists(BASVURULAR_DOSYA):
        with open(BASVURULAR_DOSYA, encoding="utf-8") as f:
            return json.load(f)
    return {}

def basvurulari_kaydet(basvurular):
    with open(BASVURULAR_DOSYA, "w", encoding="utf-8") as f:
        json.dump(basvurular, f, ensure_ascii=False, indent=2)

def menu():
    firsatlar = firsatlari_yukle()
    basvurular = basvurulari_yukle()

    print("\n=== SudoQu Başvuru Takip ===")
    print("1) Fırsatları listele ve başvuru işaretle")
    print("2) Başvurularımı görüntüle")
    print("3) Çıkış")
    secim = input("Seçim: ")

    if secim == "1":
        for i, f in enumerate(firsatlar):
            durum = basvurular.get(f["link"], {}).get("durum", "—")
            print(f"[{i}] {f['baslik']} | Durum: {durum}")
        idx = input("\nBaşvuru işaretlemek istediğin fırsatın numarasını gir (boş bırak = iptal): ")
        if idx.strip().isdigit():
            secilen = firsatlar[int(idx)]
            basvurular[secilen["link"]] = {
                "baslik": secilen["baslik"],
                "link": secilen["link"],
                "durum": "beklemede"
            }
            basvurulari_kaydet(basvurular)
            print(f"'{secilen['baslik']}' başvurulara eklendi (durum: beklemede).")

    elif secim == "2":
        if not basvurular:
            print("Henüz hiç başvuru yok.")
        else:
            for link, veri in basvurular.items():
                print(f"{veri['baslik']} | Durum: {veri['durum']}")

    elif secim == "3":
        return

    menu()

if __name__ == "__main__":
    menu()
