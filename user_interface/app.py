# user_interface/app.py
import os
import sys

current_dir = os.path.dirname(__file__)
base_dir = os.path.abspath(os.path.join(current_dir, ".."))
inference_path = os.path.join(base_dir, "inference_engine")
sys.path.append(inference_path)

from main import load_kb, forward_chain, pretty_results


def run_app(kb_path=None):
    """
    Antarmuka pengguna berbasis teks (CLI).
    Menanyakan gejala kepada pengguna dan menampilkan hasil inferensi.
    """
    kb = load_kb(kb_path) if kb_path else load_kb()
    symptoms = kb["symptoms"]

    print("=" * 60)
    print(" SISTEM PAKAR DIAGNOSA OSTEOPOROSIS ".center(60, "="))
    print("=" * 60)
    print("Jawab 'Y' jika Anda mengalami gejala tersebut, atau 'N' jika tidak.\n")

    user_presence = {}
    for code, info in symptoms.items():
        while True:
            ans = input(f"{code} - {info['label']} ? (Y/N): ").strip().lower()
            if ans in ("y", "n"):
                user_presence[code] = (ans == "y")
                break
            else:
                print("❗ Masukkan hanya Y atau N.")

    known = forward_chain(kb, user_presence)
    conclusions = pretty_results(known, kb)

    print("\n" + "=" * 60)
    print(" HASIL DIAGNOSA ".center(60))
    print("=" * 60)

    if not conclusions:
        print("Tidak ada kesimpulan yang dapat ditarik berdasarkan gejala yang Anda masukkan.")
    else:
        for code, label, cf in conclusions:
            print(f"- {label} ({code}) : Tingkat keyakinan {cf*100:.2f}%")

    print("\nTerima kasih telah menggunakan sistem pakar ini.")
    print("=" * 60)


if __name__ == "__main__":
    run_app()
