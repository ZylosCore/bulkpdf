import customtkinter as ctk
import os
import sys
import ctypes
from pathlib import Path
from PIL import Image

def resource_path(relative_path):
    """ Retourne le chemin absolu vers la ressource, compatible dev et PyInstaller """
    try:
        # PyInstaller crée un dossier temporaire et stocke le chemin dans _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Ajout du dossier src au chemin de recherche des modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bulkpdf.ui.app import BulkPDFApp

def main():
    # Correction de l'ID pour la barre des tâches Windows
    if sys.platform == "win32":
        myappid = 'zyloscore.bulkpdf.v1'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = BulkPDFApp()
    
    # Chargement de l'icône de la fenêtre
    ico_path = resource_path(os.path.join("assets", "logo.ico"))
    if os.path.exists(ico_path):
        app.iconbitmap(ico_path)
    
    app.mainloop()

if __name__ == "__main__":
    main()