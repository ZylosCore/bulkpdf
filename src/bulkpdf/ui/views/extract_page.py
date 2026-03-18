import customtkinter as ctk
from .pdf_operations import PDFOperationsView
from ..theme import TEXT_TITLE, FONT_FAMILY, ACCENT_PURPLE

class ExtractPage(PDFOperationsView):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        # Titre harmonisé : 16px, sans majuscules forcées, couleur standard
        self.label.configure(text="Extract images from PDF", 
                             font=(FONT_FAMILY, 16, "bold"), 
                             text_color=TEXT_TITLE)
        
        self.empty_label.configure(text="Select PDF files to extract images")
        
        # Bouton harmonisé (Purple au lieu de Green/Pink)
        self.run_btn.configure(text="Extract Now", fg_color=ACCENT_PURPLE)

    def execute_merge(self):
        from tkinter import filedialog
        from ...pdf_engine import PDFTask
        if not self.files_paths: return
        
        out = filedialog.askdirectory(title="Select Output Folder")
        if out:
            self.progress.pack(fill="x", pady=10)
            task = PDFTask(self.files_paths, out, self.on_progress, self.on_done, mode="extract")
            task.start()
