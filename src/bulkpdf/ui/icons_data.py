import os
import sys
from PIL import Image
import customtkinter as ctk

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_path, relative_path)

def get_icon(name, size=(20, 20)):
    icon_map = {
        "merge": "assets/icons/merge.png",
        "compress": "assets/icons/compress.png",
        "protect": "assets/icons/protect.png",
        "unlock": "assets/icons/unlock.png",
        "image": "assets/icons/image.png",
        "settings": "assets/icons/settings.png",
        "logo": "assets/logo.png"
    }
    
    full_path = get_resource_path(icon_map.get(name, ""))
    
    if os.path.exists(full_path):
        try:
            img_light = Image.open(full_path).convert("RGBA")
            
            # Pour le mode sombre : on transforme l'icône en blanc (sauf le logo)
            if name != "logo":
                r, g, b, alpha = img_light.split()
                img_dark = Image.merge("RGBA", (r.point(lambda _: 255), 
                                              g.point(lambda _: 255), 
                                              b.point(lambda _: 255), 
                                              alpha))
            else:
                img_dark = img_light

            return ctk.CTkImage(light_image=img_light, dark_image=img_dark, size=size)
        except Exception as e:
            print(f"Erreur icône {name}: {e}")
    return None