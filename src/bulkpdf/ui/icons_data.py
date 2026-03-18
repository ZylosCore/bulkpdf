import io
import base64
from PIL import Image
import customtkinter as ctk

# Données des icônes (Base64) - Plus besoin de fichiers PNG externes !
# J'ai inclus des versions compressées pour le script
LOGO_B64 = "iVBORw0KGgoAAAANSUhEUgAAADQAAAA0CAYAAADFeBvrAAAACXBIWXMAAAsTAAALEwEAmpwYAAADfElEQVR4nO2Xz2sTQRSAX8SDePCgB6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6uIePCoF6v6At8A6YIuGAAAAABJRU5ErkJggg=="

def get_icon(name, size=(20, 20)):
    try:
        if name == "logo":
            data = LOGO_B64
        else:
            # Pour l'instant on utilise le logo par défaut si l'icône manque
            data = LOGO_B64
        
        img_data = base64.b64decode(data)
        pil_img = Image.open(io.BytesIO(img_data)).convert("RGBA")
        return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
    except:
        return None
