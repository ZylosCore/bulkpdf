#!/bin/bash

# 1. On crée l'arborescence complète au cas où
mkdir -p src/assets
mkdir -p src/bulkpdf/ui/views
touch src/__init__.py
touch src/bulkpdf/__init__.py
touch src/bulkpdf/ui/__init__.py
touch src/bulkpdf/ui/views/__init__.py

# 2. On répare MERGE_PAGE (Le contenu central)
cat <<EOF > "src/bulkpdf/ui/views/merge_page.py"
import customtkinter as ctk

class MergePage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#242424", **kwargs)
        self.label = ctk.CTkLabel(self, text="BIENVENUE DANS MERGE PDF", 
                                   font=("Segoe UI", 24, "bold"), text_color="#8a55d1")
        self.label.pack(pady=50, padx=20)
        
        self.btn = ctk.CTkButton(self, text="+ Ajouter des fichiers", fg_color="#8a55d1")
        self.btn.pack(pady=20)
EOF

# 3. On répare NAVIGATION (La Sidebar avec Logo)
cat <<EOF > "src/bulkpdf/ui/navigation.py"
import customtkinter as ctk
from PIL import Image
import os

class NavigationView(ctk.CTkFrame):
    def __init__(self, master, current_page_callback, **kwargs):
        super().__init__(master, width=220, fg_color="#1a1a2e", **kwargs)
        
        # Chemin du logo
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        logo_path = os.path.join(base_dir, "assets", "logo.png")
        
        # Logo + Titre
        try:
            img_pil = Image.open(logo_path).convert("RGBA")
            self.logo_img = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(40, 40))
            self.logo_label = ctk.CTkLabel(self, text=" BULK PDF", image=self.logo_img, 
                                           compound="left", font=("Segoe UI", 20, "bold"))
        except:
            self.logo_label = ctk.CTkLabel(self, text="BULK PDF", font=("Segoe UI", 20, "bold"))
        
        self.logo_label.pack(pady=30, padx=20, anchor="w")

        # Bouton Navigation
        self.btn = ctk.CTkButton(self, text="Merge PDF", fg_color="transparent", 
                                 anchor="w", command=lambda: current_page_callback("merge"))
        self.btn.pack(fill="x", padx=10, pady=5)
EOF

# 4. On répare MAIN (L'assemblage)
cat <<EOF > "src/main.py"
import customtkinter as ctk
import sys
import os

# Important : On dit à Python où chercher les modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from bulkpdf.ui.navigation import NavigationView
from bulkpdf.ui.views.merge_page import MergePage

class BulkPDFApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BulkPDF Pro v2.0")
        self.geometry("1100x700")
        
        # Layout principal : 2 colonnes
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Ajouter la Sidebar
        self.navigation = NavigationView(self, self.show_page)
        self.navigation.grid(row=0, column=0, sticky="nsew")

        # 2. Ajouter le conteneur de pages
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        # 3. Charger les pages
        self.pages = {
            "merge": MergePage(self.container)
        }
        self.show_page("merge")

    def show_page(self, page_name):
        for page in self.pages.values():
            page.grid_forget()
        if page_name in self.pages:
            self.pages[page_name].grid(row=0, column=0, sticky="nsew")

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    app = BulkPDFApp()
    app.mainloop()
EOF

echo "[+] Reconstruction terminée."