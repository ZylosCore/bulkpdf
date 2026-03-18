import customtkinter as ctk
from PIL import Image
import os
from .theme import BG_COLOR, TEXT_MAIN # Assure-toi que theme.py existe

class NavigationView(ctk.CTkFrame):
    def __init__(self, master, current_page_callback, **kwargs):
        super().__init__(master, width=220, fg_color="#1a1a2e", **kwargs)
        self.current_page_callback = current_page_callback
        
        # --- CHARGEMENT DU LOGO ---
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        logo_path = os.path.join(base_dir, "assets", "logo.png")
        
        try:
            img_pil = Image.open(logo_path).convert("RGBA")
            self.logo_img = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(45, 45))
            self.logo_label = ctk.CTkLabel(self, text="  BULK PDF", image=self.logo_img, 
                                           compound="left", font=("Segoe UI", 24, "bold"),
                                           text_color="#8a55d1")
            self.logo_label.pack(pady=35, padx=20, anchor="w")
        except:
            self.logo_label = ctk.CTkLabel(self, text="BULK PDF", font=("Segoe UI", 24, "bold"))
            self.logo_label.pack(pady=35, padx=20, anchor="w")

        # --- MENU DE NAVIGATION ---
        self.create_nav_button("Merge PDF", "merge")
        self.create_nav_button("Compress", "compress")
        self.create_nav_button("Protect", "protect")
        self.create_nav_button("Unlock", "unlock")
        self.create_nav_button("Images", "images")
        self.create_nav_button("Settings", "settings")

    def create_nav_button(self, text, page_name):
        # On peut ajouter des icônes ici plus tard
        btn = ctk.CTkButton(self, text=text, fg_color="transparent", 
                            text_color="white", anchor="w", height=45,
                            hover_color="#2d2d44",
                            command=lambda: self.current_page_callback(page_name))
        btn.pack(fill="x", padx=10, pady=2)