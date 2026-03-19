import os
import sys
from PIL import Image, ImageOps
import customtkinter as ctk

def get_resource_path(relative_path):
    try:
        # Pour PyInstaller
        base_path = sys._MEIPASS
    except Exception:
        # Chemin de développement (remonte de 3 niveaux depuis ui/icons_data.py vers src/)
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_path, relative_path)

def get_icon(name, size=(20, 20)):
    icon_map = {
        "merge": "assets/icons/merge.png",
        "edit": "assets/icons/edit.png",
        "compress": "assets/icons/compress.png",
        "protect": "assets/icons/protect.png",
        "unlock": "assets/icons/unlock.png",
        "image": "assets/icons/image.png",
        "settings": "assets/icons/settings.png",
        "logo": "assets/logo.png"
    }
    
    relative_path = icon_map.get(name)
    if not relative_path:
        return None

    full_path = get_resource_path(relative_path)
    
    if os.path.exists(full_path):
        try:
            img_original = Image.open(full_path).convert("RGBA")
            
            # --- LOGIQUE D'INVERSION (BLANC POUR DARK MODE) ---
            if name != "logo":
                # On sépare les canaux pour ne travailler que sur le RGB en gardant l'Alpha (transparence)
                r, g, b, alpha = img_original.split()
                # On crée une version blanche : r, g, b deviennent 255
                img_white = Image.merge("RGBA", (
                    r.point(lambda _: 255), 
                    g.point(lambda _: 255), 
                    b.point(lambda _: 255), 
                    alpha
                ))
                # light_image = original (noir), dark_image = blanc
                return ctk.CTkImage(light_image=img_original, dark_image=img_white, size=size)
            else:
                # Le logo reste tel quel
                return ctk.CTkImage(light_image=img_original, dark_image=img_original, size=size)
        except Exception as e:
            print(f"Erreur chargement icône {name}: {e}")
            return None
            
    return None