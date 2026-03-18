import customtkinter as ctk
from PIL import Image
import os

class NavigationView(ctk.CTkFrame):
    def __init__(self, master, current_page_callback, **kwargs):
        # On force une couleur de fond différente pour voir si le logo est "invisible"
        super().__init__(master, fg_color="#2b2b2b", width=220, **kwargs)
        
        # Chemin dynamique absolu
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        logo_path = os.path.join(base_path, "assets", "logo.png")
        
        print(f"--- DIAGNOSTIC IMAGE ---")
        print(f"Recherche logo ici : {logo_path}")
        
        if os.path.exists(logo_path):
            try:
                img_pil = Image.open(logo_path).convert("RGBA")
                # CTkImage a besoin d'être gardé en mémoire (self.logo_img)
                self.logo_img = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(50, 50))
                
                self.logo_label = ctk.CTkLabel(
                    self, 
                    text="  BULK PDF", 
                    image=self.logo_img, 
                    compound="left", 
                    font=("Segoe UI", 20, "bold"),
                    text_color="white" # On force le texte en blanc
                )
                self.logo_label.pack(pady=40, padx=20, anchor="w")
                print("[OK] L'objet image a été créé et packé.")
            except Exception as e:
                print(f"[!] Erreur PIL : {e}")
        else:
            print("[!] Le fichier logo.png est physiquement introuvable à cette adresse.")
