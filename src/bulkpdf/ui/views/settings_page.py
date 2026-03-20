import os
import customtkinter as ctk
from pathlib import Path
from tkinter import filedialog
from PIL import Image

class SettingsPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # --- CORRECTION DES PERMISSIONS ---
        # Utilise %APPDATA%/BulkPDF pour éviter les erreurs d'accès dans Program Files
        self.app_data_dir = Path(os.getenv('APPDATA')) / "BulkPDF"
        self.signature_path = self.app_data_dir / "signatures"
        
        # Création récursive du dossier (ne plante pas s'il existe déjà)
        try:
            self.signature_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Erreur de création de dossier: {e}")

        self.setup_ui()

    def setup_ui(self):
        # Configuration de la grille
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Titre
        self.title_label = ctk.CTkLabel(
            self, 
            text="Paramètres de Signature", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(pady=20)

        # Zone d'affichage de la signature actuelle
        self.preview_frame = ctk.CTkFrame(self)
        self.preview_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        self.status_label = ctk.CTkLabel(self.preview_frame, text="Aucune signature configurée")
        self.status_label.pack(pady=20)

        # Bouton pour importer
        self.import_btn = ctk.CTkButton(
            self, 
            text="Importer une nouvelle signature (PNG)",
            command=self.import_signature
        )
        self.import_btn.pack(pady=20)
        
        self.info_label = ctk.CTkLabel(
            self, 
            text=f"Stockage : {self.signature_path}",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.info_label.pack(side="bottom", pady=10)

    def import_signature(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Images PNG", "*.png")]
        )
        if file_path:
            # On copie le fichier vers AppData
            target = self.signature_path / "user_signature.png"
            try:
                import shutil
                shutil.copy(file_path, target)
                self.status_label.configure(text="✅ Signature enregistrée avec succès !")
            except Exception as e:
                self.status_label.configure(text=f"❌ Erreur: {e}")