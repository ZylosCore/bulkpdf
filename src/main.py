import customtkinter as ctk
import os
import sys
import ctypes
from pathlib import Path
from PIL import Image, ImageChops

# 1. FONCTION CRUCIALE POUR PYINSTALLER
def resource_path(relative_path):
    """ Récupère le chemin absolu vers la ressource, compatible dev et PyInstaller """
    try:
        # Si exécuté via PyInstaller
        base_path = Path(sys._MEIPASS)
    except Exception:
        # Si exécuté en mode développement
        base_path = Path(__file__).parent
    return base_path / relative_path

def trim_and_make_ico(png_path, ico_path):
    """
    Nettoie le PNG et génère un ICO haute définition.
    """
    if not png_path.exists():
        return False

    try:
        img = Image.open(png_path).convert("RGBA")
        
        # --- Recadrage automatique ---
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)
        
        # On redimensionne en carré parfait
        size = max(img.size)
        new_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        new_img.paste(img, ((size - img.width) // 2, (size - img.height) // 2))
        
        # Sauvegarde de l'ICO
        icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        new_img.save(ico_path, format='ICO', sizes=icon_sizes)
        return True
    except Exception as e:
        print(f"Erreur conversion : {e}")
        return False

def main():
    # Définition des chemins dynamiques
    # Note : 'assets' est le nom du dossier tel que défini dans le --add-data de PyInstaller
    assets_dir = resource_path("assets")
    png_path = assets_dir / "logo.png"
    ico_path = assets_dir / "logo.ico"

    # 1. On essaie de régénérer l'icône (seulement si on a les droits d'écriture)
    # Note: Dans Program Files, cela peut échouer, donc on utilise un bloc try
    try:
        trim_and_make_ico(png_path, ico_path)
    except:
        pass # Si on n'a pas les droits, on utilisera l'ICO existant

    # 2. Fix barre des tâches Windows
    if sys.platform == "win32":
        try:
            myappid = 'zyloscore.bulkpdf.v2_max_size' 
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass

    # Importation de l'App (après le setup des chemins)
    from bulkpdf.ui.app import BulkPDFApp
    
    ctk.set_appearance_mode("dark")
    app = BulkPDFApp()
    
    # 3. Application de l'icône à la fenêtre
    if ico_path.exists():
        try:
            # On définit l'icône de la fenêtre
            app.iconbitmap(str(ico_path))
            
            # Pour Windows 10/11, wm_iconphoto avec le PNG donne souvent un meilleur résultat
            if png_path.exists():
                from tkinter import PhotoImage
                img_tk = PhotoImage(file=str(png_path))
                app.wm_iconphoto(True, img_tk)
        except Exception as e:
            print(f"Erreur affichage icône : {e}")

    app.mainloop()

if __name__ == "__main__":
    main()