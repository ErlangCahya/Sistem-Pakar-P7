#!/usr/bin/env python3
# user_interface/app.py

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

# Import inference engine
current_dir = os.path.dirname(__file__)
base_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(os.path.join(base_dir, "inference_engine"))
from main import load_kb, forward_chain, pretty_results


def setup_style():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TButton", font=("Segoe UI", 11, "bold"), padding=10, background="#0078D7", foreground="white")
    style.map("TButton", background=[("active", "#005A9E")], foreground=[("active", "white")])
    style.configure("TCheckbutton", font=("Segoe UI", 10))


class OsteoporosisApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🩺 Sistem Pakar Diagnosa Osteoporosis")
        self.geometry("1200x750")
        self.minsize(1000, 700)
        setup_style()

        self.kb = load_kb()
        self.symptoms = self.kb["symptoms"]

        self.container = tk.Frame(self, bg="#f0f4f8")
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        for F in (HomePage, SymptomPage, ResultPage):
            frame = F(parent=self.container, controller=self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("HomePage")

    def show_frame(self, name):
        frame = self.frames[name]
        frame.tkraise()


# ==============================
# HALAMAN AWAL
# ==============================
class HomePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Header
        top_bar = tk.Frame(self, bg="#0078D7", height=200)
        top_bar.pack(fill="x")
        tk.Label(top_bar, text="🩺 SISTEM PAKAR DIAGNOSA OSTEOPOROSIS",
                 font=("Segoe UI", 26, "bold"), bg="#0078D7", fg="white").pack(pady=60)

        # Body
        body = tk.Frame(self, bg="white", bd=3, relief="ridge")
        body.pack(padx=80, pady=40, fill="both", expand=True)

        tk.Label(body, text="Selamat Datang 👋", font=("Segoe UI", 20, "bold"), bg="white", fg="#004C99").pack(pady=10)
        tk.Label(body,
                 text="Aplikasi ini membantu mendiagnosa risiko Osteoporosis berdasarkan gejala yang Anda alami.",
                 font=("Segoe UI", 13), bg="white", fg="#333", justify="center").pack(pady=30)

        ttk.Button(body, text="🧩 Mulai Diagnosa",
                   command=lambda: controller.show_frame("SymptomPage")).pack(pady=10)
        ttk.Button(body, text="❌ Keluar Aplikasi", command=self.quit_app).pack(pady=10)

        footer = tk.Label(self, text="© 2025 Sistem Pakar Osteoporosis | EKO & ERLANG",
                          font=("Segoe UI", 10), bg="#004C99", fg="white")
        footer.pack(side="bottom", fill="x")

    def quit_app(self):
        if messagebox.askyesno("Keluar", "Apakah Anda yakin ingin keluar dari aplikasi?"):
            self.controller.destroy()


# ==============================
# HALAMAN GEJALA (TANPA SCROLL)
class SymptomPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.controller = controller
        self.symptoms = controller.symptoms

        # Header
        top_bar = tk.Frame(self, bg="#0078D7", height=100)
        top_bar.pack(fill="x")
        tk.Label(top_bar, text="🧩 PILIH GEJALA YANG ANDA ALAMI",
                 font=("Segoe UI", 22, "bold"), bg="#0078D7", fg="white").pack(pady=25)

        # Konten utama
        body = tk.Frame(self, bg="#f0f4f8")
        body.pack(padx=60, pady=30, fill="both", expand=True)

        self.checkbox_vars = {}
        self.cards = {}

        # Grid 2 kolom biar rapi
        row, col = 0, 0
        for code, info in self.symptoms.items():
            var = tk.BooleanVar()
            self.checkbox_vars[code] = var

            # Card gejala
            card = tk.Frame(body, bg="white", bd=2, relief="ridge", cursor="hand2")
            card.grid(row=row, column=col, padx=15, pady=10, sticky="nsew")
            card.bind("<Button-1>", lambda e, c=code: self.toggle_card(c))
            card.bind("<Enter>", lambda e, c=card: c.config(bg="#E8F0FE"))
            card.bind("<Leave>", lambda e, c=card: self.reset_card_color(c))

            # Checkbutton dan label
            chk = ttk.Checkbutton(card, variable=var, style="TCheckbutton")
            chk.pack(side="left", padx=10, pady=10)
            lbl = tk.Label(card, text=info["label"], font=("Segoe UI", 11), bg="white", anchor="w", justify="left", wraplength=400)
            lbl.pack(side="left", fill="x", expand=True, padx=5)
            lbl.bind("<Button-1>", lambda e, c=code: self.toggle_card(c))

            self.cards[code] = card

            col += 1
            if col > 1:
                col = 0
                row += 1

        # Atur grid supaya rapi
        for i in range(2):
            body.grid_columnconfigure(i, weight=1)

        # Tombol bawah
        btn_frame = tk.Frame(self, bg="#f0f4f8")
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="🔍 Diagnosa Sekarang",
                   command=self.run_diagnosis).pack(side="left", padx=20)
        ttk.Button(btn_frame, text="🏠 Beranda",
                   command=lambda: controller.show_frame("HomePage")).pack(side="right", padx=20)

    def toggle_card(self, code):
        """Toggle pilihan dengan klik card mana saja"""
        var = self.checkbox_vars[code]
        card = self.cards[code]
        var.set(not var.get())
        if var.get():
            card.config(bg="#D6EAF8", bd=3, relief="solid")
        else:
            card.config(bg="white", bd=2, relief="ridge")

    def reset_card_color(self, card):
        """Kembalikan warna card saat mouse keluar"""
        for c, v in self.checkbox_vars.items():
            if self.cards[c] == card:
                if v.get():
                    card.config(bg="#D6EAF8")
                else:
                    card.config(bg="white")

    def run_diagnosis(self):
        user_presence = {code: var.get() for code, var in self.checkbox_vars.items()}
        selected = [info["label"] for code, info in self.symptoms.items() if user_presence.get(code)]
        known = forward_chain(self.controller.kb, user_presence)
        conclusions = pretty_results(known, self.controller.kb)
        self.controller.frames["ResultPage"].display_results(conclusions, selected)
        self.controller.show_frame("ResultPage")



# ==============================
# HALAMAN HASIL
# ==============================
class ResultPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.kb = controller.kb

        top_bar = tk.Frame(self, bg="#004C99", height=100)
        top_bar.pack(fill="x")
        tk.Label(top_bar, text="📋 HASIL DIAGNOSA", font=("Segoe UI", 20, "bold"), bg="#004C99", fg="white").pack(pady=20)

        body = tk.Frame(self, bg="white", bd=2, relief="groove")
        body.pack(padx=80, pady=30, fill="both", expand=True)

        self.result_text = tk.Text(body, wrap="word", height=20, font=("Segoe UI", 12),
                                   bg="white", fg="#333", relief="flat", padx=20, pady=15)
        self.result_text.pack(fill="both", expand=True)

        btn_frame = tk.Frame(self, bg="#e6eef5")
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="🔁 Ulangi Diagnosa",
                   command=lambda: controller.show_frame("SymptomPage")).pack(side="left", padx=20)
        ttk.Button(btn_frame, text="🏠 Beranda",
                   command=lambda: controller.show_frame("HomePage")).pack(side="left", padx=20)
        ttk.Button(btn_frame, text="❌ Keluar",
                   command=self.quit_app).pack(side="right", padx=20)

    def display_results(self, conclusions, selected_symptoms):
        self.result_text.delete(1.0, tk.END)
        diagnosis_info = self.kb.get("diagnosis", {})

        self.result_text.insert(tk.END, "🧾 Gejala yang Anda pilih:\n", "header")
        if selected_symptoms:
            for g in selected_symptoms:
                self.result_text.insert(tk.END, f"   • {g}\n")
        else:
            self.result_text.insert(tk.END, "   (Tidak ada gejala yang dipilih)\n")

        self.result_text.insert(tk.END, "\n============================\n\n")

        if not conclusions:
            self.result_text.insert(tk.END, "❌ Tidak ditemukan hasil diagnosa.\n\nSilakan pilih gejala lain.")
        else:
            self.result_text.insert(tk.END, "🧠 Hasil Analisis:\n\n", "header")
            for code, label, cf in conclusions:
                desc = diagnosis_info.get(code, {}).get("description", "")
                title = diagnosis_info.get(code, {}).get("label", label)
                self.result_text.insert(tk.END, f"🔸 {title}\n", "title")
                self.result_text.insert(tk.END, f"   Nilai CF: {cf:.2f}\n")
                self.result_text.insert(tk.END, f"   Penjelasan: {desc}\n\n")

        self.result_text.tag_configure("header", font=("Segoe UI", 14, "bold"), foreground="#004C99")
        self.result_text.tag_configure("title", font=("Segoe UI", 12, "bold"), foreground="#0078D7")

    def quit_app(self):
        if messagebox.askyesno("Keluar", "Apakah Anda yakin ingin keluar dari aplikasi?"):
            self.controller.destroy()


# ==============================
# RUN APP
# ==============================
if __name__ == "__main__":
    app = OsteoporosisApp()
    app.mainloop()
