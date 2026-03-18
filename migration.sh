#!/bin/bash

# 1. On définit le chemin absolu du projet
BASE_PATH=$(cygpath -w "$(pwd)")
ASSETS_PATH="${BASE_PATH}\\src\\assets"

echo "[*] Application de la logique BulkFolder..."
echo "[*] Chemin des ressources : $ASSETS_PATH"

# 2. Réécriture de NAVIGATION.PY
cat <<EOF > "src/bulkpdf/ui/navigation.py"
import customtkinter as ctk
from PIL import Image
import os

class NavigationView(ctk.CTkFrame):
    def __init__(self, master, current_page_callback, **kwargs):
        super().__init__(master, fg_color="#1a1a2e", width=220, **kwargs)
        self.current_page_callback = current_page_callback
        
        # Le secret de BulkFolder : Garder une référence forte dans un dictionnaire
        self.icons = {}
        assets_dir = r"$ASSETS_PATH"

        # --- CHARGEMENT DU LOGO ---
        logo_path = os.path.join(assets_dir, "logo.png")
        if os.path.exists(logo_path):
            try:
                img_pil = Image.open(logo_path).convert("RGBA")
                self.icons["logo"] = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(45, 45))
                
                self.logo_label = ctk.CTkLabel(
                    self, 
                    text="  BULK PDF", 
                    image=self.icons["logo"],
                    compound="left",
                    font=("Segoe UI", 22, "bold"),
                    text_color="#8a55d1"
                )
                self.logo_label.pack(pady=35, padx=20, anchor="w")
            except Exception as e:
                print(f"Erreur Logo: {e}")
        
        # --- MENU ---
        # On définit les boutons comme dans ton projet fonctionnel
        menu_items = [
            ("Merge PDF", "merge", "merge.png"),
            ("Compress", "compress", "compress.png"),
            ("Settings", "settings", "settings.png")
        ]

        for text, page, icon_name in menu_items:
            icon_path = os.path.join(assets_dir, "icons", icon_name)
            current_icon = None
            
            if os.path.exists(icon_path):
                try:
                    p_img = Image.open(icon_path).convert("RGBA")
                    self.icons[page] = ctk.CTkImage(light_image=p_img, dark_image=p_img, size=(20, 20))
                    current_icon = self.icons[page]
                except:
                    pass
            
            btn = ctk.CTkButton(
                self, 
                text=text, 
                image=current_icon,
                fg_color="transparent",
                text_color="white",
                anchor="w",
                height=45,
                hover_color="#2d2d44",
                compound="left",
                command=lambda p=page: self.current_page_callback(p)
            )
            btn.pack(fill="x", padx=10, pady=2)

EOF

# 3. Lancement forcé avec le bon PYTHONPATH
export PYTHONPATH="${BASE_PATH}\\src"
echo "[+] Terminé. Lancement de l'application..."
python3 src/main.py