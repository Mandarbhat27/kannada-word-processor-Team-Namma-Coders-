# code/gui.py
import tkinter as tk
from tkinter import ttk, messagebox
from code.word_joiner import WordJoiner

class WordJoinerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Kannada Word Processor — Sandhi | Reverse Sandhi | Samāsa | Vibhakti")
        self.root.state("zoomed")
        self.root.configure(bg="#e8eef3")

        self.wj = WordJoiner()

        # Center card
        self.card = tk.Frame(self.root, bg="white", bd=0, relief="flat")
        self.card.place(relx=0.5, rely=0.5, anchor="center", width=950, height=650)

        tk.Label(
            self.card, text="Kannada Word Processor",
            font=("Nirmala UI", 28, "bold"), bg="white", fg="#0b3948"
        ).pack(pady=15)

        # Mode selector
        mode_frame = tk.Frame(self.card, bg="white")
        mode_frame.pack(pady=6)

        tk.Label(mode_frame, text="Mode:", font=("Nirmala UI", 15), bg="white").pack(side="left", padx=6)

        self.mode = tk.StringVar(value="sandhi")
        modes = [
            ("Sandhi", "sandhi"),
            ("Reverse Sandhi", "reverse_sandhi"),
            ("Samāsa (dict+fuzzy)", "samasa"),
            ("Vibhakti", "vibhakti")
        ]

        for txt,val in modes:
            ttk.Radiobutton(
                mode_frame, text=txt, variable=self.mode, value=val,
                command=self.adjust_inputs
            ).pack(side="left", padx=8)

        # Input area
        inp = tk.Frame(self.card, bg="white")
        inp.pack(pady=8)

        self.lbl1 = tk.Label(inp, text="Word 1:", font=("Nirmala UI", 15), bg="white")
        self.lbl1.grid(row=0, column=0, padx=8, pady=6, sticky="e")
        self.e1 = ttk.Entry(inp, font=("Nirmala UI", 15), width=32)
        self.e1.grid(row=0, column=1, padx=6, pady=6)

        self.lbl2 = tk.Label(inp, text="Word 2:", font=("Nirmala UI", 15), bg="white")
        self.lbl2.grid(row=1, column=0, padx=8, pady=6, sticky="e")
        self.e2 = ttk.Entry(inp, font=("Nirmala UI", 15), width=32)
        self.e2.grid(row=1, column=1, padx=6, pady=6)

        # Buttons
        btnf = tk.Frame(self.card, bg="white")
        btnf.pack(pady=10)

        ttk.Button(btnf, text="Process", command=self.process, width=18).grid(row=0, column=0, padx=8)
        ttk.Button(btnf, text="Fuzzy Test", command=self.fuzzy_test, width=14).grid(row=0, column=1, padx=8)
        ttk.Button(btnf, text="Clear", command=self.clear_all, width=12).grid(row=0, column=2, padx=8)
        ttk.Button(btnf, text="Copy Result", command=self.copy_result, width=14).grid(row=0, column=3, padx=8)

        # Output
        tk.Label(self.card, text="Result:", font=("Nirmala UI", 15), bg="white").pack()

        self.out = tk.Text(
            self.card, height=9, width=95,
            font=("Nirmala UI", 15),
            bg="#f6f9fc", relief="flat"
        )
        self.out.pack(padx=12, pady=6)

        # History
        tk.Label(self.card, text="History:", font=("Nirmala UI", 13), bg="white").pack()

        self.hist = tk.Text(
            self.card, height=6, width=95,
            font=("Nirmala UI", 11),
            bg="#ffffff", relief="sunken"
        )
        self.hist.pack(padx=12, pady=(0,12))

        self.adjust_inputs()

    # =============================================================
    # Input adjustment
    # =============================================================
    def adjust_inputs(self):
        mode = self.mode.get()
        if mode == "sandhi":
            self.lbl1.config(text="Word 1:")
            self.lbl2.config(text="Word 2:")
            self.lbl2.grid(); self.e2.grid()

        elif mode == "reverse_sandhi":
            self.lbl1.config(text="Combined word:")
            self.lbl2.grid_remove(); self.e2.grid_remove()

        elif mode == "samasa":
            self.lbl1.config(text="Combined word:")
            self.lbl2.grid_remove(); self.e2.grid_remove()

        elif mode == "vibhakti":
            self.lbl1.config(text="Word:")
            self.lbl2.grid_remove(); self.e2.grid_remove()

    # =============================================================
    # PROCESS
    # =============================================================
    def process(self):
        mode = self.mode.get()
        w1 = self.e1.get().strip()
        w2 = self.e2.get().strip()

        # ---------------- SANDHI ----------------
        if mode == "sandhi":
            if not w1 or not w2:
                messagebox.showwarning("Input", "Enter both words")
                return
            res = self.wj.apply_sandhi(w1, w2)
            out_text = f"ಸಂಧಿ ಫಲಿತಾಂಶ:\n{res}"

        # ---------------- REVERSE SANDHI ----------------
        elif mode == "reverse_sandhi":
            if not w1:
                messagebox.showwarning("Input", "Enter combined word")
                return

            cands = self.wj.reverse_sandhi(w1)
            if not cands:
                out_text = "ಯಾವುದೇ ಸಂಧಿ ವಿಭಾಗ ಸಿಕ್ಕಿಲ್ಲ."
            else:
                lines = ["Reverse Sandhi candidates:\n"]
                for i,(a,b) in enumerate(cands[:10], start=1):
                    lines.append(f"{i}) ಪದ 1: {a}\n    ಪದ 2: {b}\n")
                out_text = "\n".join(lines)

        # ---------------- SAMĀSA ----------------
        elif mode == "samasa":
            if not w1:
                messagebox.showwarning("Input", "Enter compound word")
                return

            sp = self.wj.validate_compound(w1)
            if sp:
                a,b = sp
                out_text = f"ಸಮಾಸ ವಿಚ್ಛೇದ:\nಪದ 1: {a}\nಪದ 2: {b}"
            else:
                sugg = self.wj.get_suggestions(w1, 8)
                if sugg:
                    out_text = "ಸಮಾಸ ಸಿಕ್ಕಿಲ್ಲ.\nಸೂചനೆಗಳು:\n" + ", ".join(sugg)
                else:
                    out_text = "ಸಮಾಸ ಸಿಕ್ಕಿಲ್ಲ."

        # ---------------- VIBHAKTI ----------------
        elif mode == "vibhakti":
            if not w1:
                messagebox.showwarning("Input", "Enter word")
                return

            out, vid = self.wj.apply_vibhakti_single(w1)
            det_id, _ = self.wj.detect_vibhakti(out)
            final_id = vid or det_id or "unknown"

            out_text = f"ವಿಭಕ್ತಿ ರೂಪ: {out}\nವಿಭಕ್ತಿ ಸಂಖ್ಯೆ: {final_id}"

        else:
            out_text = "Unknown mode."

        # Show & Log
        self.out.delete("1.0", tk.END)
        self.out.insert(tk.END, out_text)

        self.hist.insert(tk.END, f"{mode}: {w1} {(w2 if w2 else '')} -> {out_text.splitlines()[0]}\n")

    # =============================================================
    # OTHER BUTTONS
    # =============================================================
    def fuzzy_test(self):
        lines = []

        lines.append("Sandhi Test:\n" +
                     self.wj.apply_sandhi("shakthi", "abhimaana"))

        vb, _ = self.wj.apply_vibhakti_single("raama")
        lines.append("\nVibhakti Test:\n" + vb)

        sm = self.wj.validate_compound("ಲಕ್ಷ್ಮೀನಾರಾಯಣ")
        lines.append("\nSamāsa Test:\n" + str(sm))

        self.out.delete("1.0", tk.END)
        self.out.insert(tk.END, "\n\n".join(lines))

    def clear_all(self):
        self.e1.delete(0, tk.END)
        self.e2.delete(0, tk.END)
        self.out.delete("1.0", tk.END)

    def copy_result(self):
        tx = self.out.get("1.0", tk.END).strip()
        if tx:
            self.root.clipboard_clear()
            self.root.clipboard_append(tx)
            messagebox.showinfo("Copied", "Copied to clipboard.")

if __name__ == "__main__":
    root = tk.Tk()
    app = WordJoinerGUI(root)
    root.mainloop()
