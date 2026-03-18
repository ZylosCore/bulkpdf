import customtkinter as ctk
import sys
import os

# Ajout du chemin pour trouver les modules bulkpdf
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from bulkpdf.ui.app import BulkPDFApp

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    app = BulkPDFApp()
    app.mainloop()
