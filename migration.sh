#!/bin/bash

cat <<EOF > src/bulkpdf/ui/views/pdf_operations.py
import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from datetime import datetime
from .cards import FileCard
from ...pdf_engine import PDFTask
from ..theme import BG_COLOR, BORDER_COLOR, TEXT_LOW, ACCENT_PURPLE, TEXT_TITLE, FONT_FAMILY

class PDFOperationsView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.files_paths = []
        self.mode_name = "processed"
        
        self.label = ctk.CTkLabel(self, text="PDF Operation", font=(FONT_FAMILY, 16, "bold"), text_color=TEXT_TITLE)
        self.label.pack(pady=(0, 10), anchor="w")
        
        self.scroll = ctk.CTkScrollableFrame(self, fg_color=BG_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=10)
        self.scroll.pack(fill="both", expand=True)
        
        self.empty_label = ctk.CTkLabel(self.scroll, text="No files selected", font=(FONT_FAMILY, 12), text_color=TEXT_LOW)
        self.empty_label.pack(pady=60)

        self.progress = ctk.CTkProgressBar(self, progress_color=ACCENT_PURPLE, height=6)
        # On ne pack pas la progress bar de suite pour garder l'interface propre

        self.action_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.action_bar.pack(fill="x", pady=15)
        
        self.add_btn = ctk.CTkButton(self.action_bar, text="+ Add Files", height=32, fg_color=ACCENT_PURPLE, command=self.browse_files)
        self.add_btn.pack(side="left", padx=5)

        # BOUTON VERT : On s'assure qu'il appelle bien self.execute_task
        self.run_btn = ctk.CTkButton(self.action_bar, text="Run Task", height=32, fg_color=("#27ae60", "#2ecc71"), hover_color="#219150", command=self.execute_task)
        self.run_btn.pack(side="right", padx=5)

    def get_smart_filename(self):
        date_str = datetime.now().strftime("%Y-%m-%d")
        base = Path(self.files_paths[0]).stem if self.files_paths else "document"
        return f"{base}_{self.mode_name}_{date_str}.pdf"

    def browse_files(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
        if files:
            if self.empty_label.winfo_exists(): self.empty_label.pack_forget()
            for f in files:
                p = Path(f)
                if p not in self.files_paths:
                    self.files_paths.append(p)
                    FileCard(self.scroll, p, self.remove_file).pack(fill="x", padx=10, pady=4)

    def remove_file(self, card):
        if card.file_path in self.files_paths: self.files_paths.remove(card.file_path)
        card.destroy()

    def execute_task(self):
        # 1. Vérification des fichiers
        if not self.files_paths:
            messagebox.showwarning("Empty", "Please add files before running the task.")
            return
            
        # 2. Récupération dynamique du mot de passe
        pw = None
        if hasattr(self, "password_entry"):
            pw = self.password_entry.get().strip()
            if not pw and self.mode_name in ["encrypted", "unlocked"]:
                messagebox.showwarning("Missing Info", "Please enter a password.")
                return

        # 3. Fenêtre de sauvegarde
        out = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=self.get_smart_filename())
        if out:
            print(f"[DEBUG] Launching {self.mode_name} task...")
            self.progress.pack(fill="x", pady=(0, 10))
            self.progress.set(0.1) # Petit boost visuel au départ
            
            task = PDFTask(self.files_paths, out, self.on_progress, self.on_done, mode=self.mode_name, password=pw)
            task.start()

    def on_progress(self, v): 
        self.progress.set(v)
    
    def on_done(self, res):
        self.progress.pack_forget()
        if res and "Error" in str(res):
            messagebox.showerror("Task Failed", res)
        else:
            # Succès : On active la pastille verte 🟢 sur TOUTES les cartes
            for card in self.scroll.winfo_children():
                if hasattr(card, "mark_success"):
                    card.mark_success()
            messagebox.showinfo("Success", "Operation completed successfully!")
EOF