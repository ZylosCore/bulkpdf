import customtkinter as ctk
import os
import sys
import ctypes
from pathlib import Path
from PIL import Image, ImageChops

# Configuration des chemins
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from bulkpdf.ui.app import BulkPDFApp

def trim_and_make_ico():
    """
    Supprime les bordures transparentes inutiles du PNG 
    et génère un ICO haute définition.
    """
    png_path = current_dir / "assets" / "logo.png"
    ico_path = current_dir / "assets" / "app_icon.ico"
    
    if not png_path.exists():
        return

    try:
        img = Image.open(png_path).convert("RGBA")
        
        # --- ÉTAPE CRUCIALE : CROP (Recadrage automatique) ---
        # On détecte la partie non-vide de l'image pour que le logo touche les bords
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)
        
        # On redimensionne en carré parfait (padding si nécessaire)
        size = max(img.size)
        new_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        new_img.paste(img, ((size - img.width) // 2, (size - img.height) // 2))
        
        # Sauvegarde de l'ICO avec le format 256px (taille max Windows)
        icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        new_img.save(ico_path, format='ICO', sizes=icon_sizes)
        return True
    except Exception as e:
        print(f"Erreur conversion : {e}")
        return False

def main():
    # 1. Régénérer l'icône proprement (sans bordures)
    update_success = trim_and_make_ico()

    # 2. FIX BARRE DES TÂCHES (On change l'ID à 'v2' pour forcer Windows à oublier le cache)
    if sys.platform == "win32":
        myappid = 'zyloscore.bulkpdf.v2_max_size' 
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    ctk.set_appearance_mode("dark")
    app = BulkPDFApp()
    
    ico_path = current_dir / "assets" / "app_icon.ico"
    png_path = current_dir / "assets" / "logo.png"
    
    if ico_path.exists():
        try:
            # Méthode 1 : L'icône standard
            app.iconbitmap(str(ico_path))
            
            # Méthode 2 : Forcer via PhotoImage (souvent plus grand sur Win10/11)
            # On utilise le PNG car Tkinter gère mieux la transparence directe
            from tkinter import PhotoImage
            img_tk = PhotoImage(file=str(png_path))
            app.wm_iconphoto(True, img_tk)
                
        except Exception as e:
            print(f"Erreur icône : {e}")

    app.mainloop()

if __name__ == "__main__":
    main()