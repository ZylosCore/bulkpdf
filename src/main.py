import customtkinter as ctk
import os
import sys
import ctypes
from pathlib import Path
from PIL import Image

# Configuration des chemins pour l'import des modules internes
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from bulkpdf.ui.app import BulkPDFApp

def update_icon_from_png():
    """
    Convertit automatiquement le logo.png en app_icon.ico 
    avec toutes les résolutions nécessaires pour Windows.
    """
    png_path = current_dir / "assets" / "logo.png"
    ico_path = current_dir / "assets" / "app_icon.ico"
    
    if png_path.exists():
        try:
            # On vérifie si l'ICO doit être mis à jour (si le PNG est plus récent)
            if not ico_path.exists() or os.path.getmtime(png_path) > os.path.getmtime(ico_path):
                img = Image.open(png_path)
                
                # Liste des tailles standards Windows pour un .ico haute définition
                # 256px est crucial pour que l'icône ne soit pas "petite" dans la barre des tâches
                icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
                
                img.save(ico_path, format='ICO', sizes=icon_sizes)
                print("[*] Icône .ico mise à jour avec succès.")
        except Exception as e:
            print(f"[!] Erreur lors de la génération de l'icône : {e}")
    else:
        print("[!] logo.png introuvable dans assets/, conversion impossible.")

def main():
    # 1. Mise à jour automatique de l'icône à partir du PNG
    update_icon_from_png()

    # 2. Fix pour l'ID de l'application (Barre des tâches Windows)
    if sys.platform == "win32":
        # Identifiant unique pour que Windows n'utilise pas l'icône de Python
        myappid = 'zyloscore.bulkpdf.v1' 
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    ctk.set_appearance_mode("dark")
    app = BulkPDFApp()
    
    # 3. Chargement de l'icône générée
    ico_path = current_dir / "assets" / "app_icon.ico"
    png_path = current_dir / "assets" / "logo.png"
    
    if ico_path.exists():
        try:
            # Définit l'icône de la fenêtre
            app.iconbitmap(str(ico_path))
            
            # Forcer l'affichage de l'image haute définition via wm_iconphoto
            # C'est souvent ce qui permet de remplir tout l'espace de la barre des tâches
            from tkinter import PhotoImage
            img_tk = PhotoImage(file=str(png_path))
            app.wm_iconphoto(True, img_tk)
                
        except Exception as e:
            print(f"[!] Erreur lors du chargement de l'icône : {e}")

    app.mainloop()

if __name__ == "__main__":
    main()