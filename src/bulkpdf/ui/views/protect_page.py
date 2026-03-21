import customtkinter as ctk
from tkinter import messagebox, filedialog
from .pdf_operations import PDFOperationsView
from ..theme import TEXT_TITLE, FONT_FAMILY, ACCENT_BLUE

class ProtectPage(PDFOperationsView):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.mode_name = "encrypted"
        self.label.configure(text="password protection", font=(FONT_FAMILY, 16, "bold"))
        
        # Champ mot de passe avec placeholder clair
        self.password_entry = ctk.CTkEntry(self.action_bar, placeholder_text="set password...", 
                                           show="*", width=160, height=32)
        self.password_entry.pack(side="left", padx=10)
        
        # Correction de la couleur ici
        self.run_btn.configure(text="Protect PDF", fg_color=ACCENT_BLUE)

    def execute_task(self):
        if not self.files_paths:
            messagebox.showwarning("Selection Error", "Please add a PDF file first.")
            return

        # VALIDATION : On vérifie que le mot de passe n'est pas vide
        pw = self.password_entry.get().strip()
        if not pw:
            messagebox.showwarning("Security Required", "Password cannot be empty. Please set a password to encrypt the file.")
            return

        out = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=self.get_smart_filename())
        if out:
            self.progress.pack(fill="x", pady=10)
            from ...pdf_engine import PDFTask
            task = PDFTask(self.files_paths, out, self.on_progress, self.on_done, mode="encrypted", password=pw)
            task.start()