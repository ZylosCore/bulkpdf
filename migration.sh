#!/bin/bash

echo "[*] Harmonizing the Compress Page (Compact title, no green, normal case)..."

cat <<EOF > src/bulkpdf/ui/views/compress_page.py
import customtkinter as ctk
from .pdf_operations import PDFOperationsView
from ..theme import TEXT_TITLE, FONT_FAMILY, ACCENT_PURPLE

class CompressPage(PDFOperationsView):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Titre harmonisé : 16px, Normal Case (pas de MAJUSCULES), Couleur Standard
        self.label.configure(
            text="Optimize PDF size", 
            font=(FONT_FAMILY, 16, "bold"), 
            text_color=TEXT_TITLE
        )
        
        self.empty_label.configure(text="Select PDF files to reduce their weight")
        
        # Bouton harmonisé en Violet (Purple) au lieu de Vert
        self.run_btn.configure(
            text="Compress Now", 
            fg_color=ACCENT_PURPLE,
            hover_color="#664dff"
        )

    def execute_merge(self):
        from tkinter import filedialog
        from ...pdf_engine import PDFTask
        if not self.files_paths: return
        
        out = filedialog.asksaveasfilename(
            title="Save Compressed PDF", 
            defaultextension=".pdf"
        )
        if out:
            self.progress.pack(fill="x", pady=10)
            # Mode "compress" activé pour le moteur PDF
            task = PDFTask(self.files_paths, out, self.on_progress, self.on_done, mode="compress")
            task.start()
EOF

echo "[+] Compress page updated successfully."