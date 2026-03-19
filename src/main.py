import customtkinter as ctk
import os
import sys
import ctypes
from pathlib import Path
from PIL import Image, ImageChops

# --- FONCTION DE GESTION DES RESSOURCES POUR PYINSTALLER ---
def resource_path(relative_path):
    """ Retourne le chemin absolu vers la ressource, compatible dev et PyInstaller """
    try:
        # PyInstaller crée un dossier temporaire et stocke le chemin dans _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Configuration des chemins pour le mode développement
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from bulkpdf.ui.app import BulkPDFApp

def trim_and_make_ico():
    """ Supprime les bordures transparentes et génère un ICO HD """
    # Utilisation de resource_path pour les chemins d'assets
    png_path = Path(resource_path(os.path.join("assets", "logo.png")))
    ico_path = Path(resource_path(os.path.join("assets", "logo.ico")))
    
    if not png_path.exists():
        return False

    try:
        img = Image.open(png_path).convert("RGBA")
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)
        
        # Redimensionnement carré
        size = max(img.size)
        new_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        new_img.paste(img, ((size - img.size[0]) // 2, (size - img.size[1]) // 2))
        
        # Sauvegarde ICO
        icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        new_img.save(ico_path, format="ICO", sizes=icon_sizes)
        return True
    except Exception as e:
        print(f"Erreur génération icône : {e}")
        return False

def main():
    trim_and_make_ico()
    
    if sys.platform == "win32":
        myappid = 'zyloscore.bulkpdf.v2'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = BulkPDFApp()
    
    # Application de l'icône à la fenêtre
    ico_path = resource_path(os.path.join("assets", "logo.ico"))
    if os.path.exists(ico_path):
        app.iconbitmap(ico_path)
    
    app.mainloop()

if __name__ == "__main__":
    main()