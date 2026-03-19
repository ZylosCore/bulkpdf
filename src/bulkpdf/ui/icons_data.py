import os
import sys
from PIL import Image
import customtkinter as ctk

def get_resource_path(relative_path):
    """ Récupère le chemin absolu vers la ressource, fonctionne pour dev et pour PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        # On remonte de 3 niveaux depuis ce fichier pour arriver à la racine 'src'
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    return os.path.join(base_path, relative_path)

def get_icon(name, size=(20, 20)):
    """
    Charge une icône depuis src/assets/icons/name.png
    """
    # Mapping des noms vers les fichiers réels
    icon_map = {
        "merge": "assets/icons/merge.png",
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
            img = Image.open(full_path)
            return ctk.CTkImage(light_image=img, dark_image=img, size=size)
        except Exception as e:
            print(f"Erreur lors de la lecture du fichier {full_path}: {e}")
            return None
    else:
        print(f"Fichier icon introuvable: {full_path}")
        return None