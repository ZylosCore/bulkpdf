import customtkinter as ctk
import os
import sys
from pathlib import Path

# Ajouter le dossier 'src' au chemin de recherche de Python
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from bulkpdf.ui.app import BulkPDFApp

def main():
    ctk.set_appearance_mode("dark")
    app = BulkPDFApp()
    
    # Chemin vers l'icône de l'application (.ico)
    icon_path = current_dir / "assets" / "app_icon.ico"
    
    if icon_path.exists():
        if sys.platform.startswith('win'):
            app.iconbitmap(str(icon_path))
        else:
            # Sur Linux/Mac, on utilise souvent un PNG pour l'icône de fenêtre
            pass
    else:
        print(f"Attention: Icone de fenêtre introuvable à {icon_path}")

    app.mainloop()

if __name__ == "__main__":
    main()