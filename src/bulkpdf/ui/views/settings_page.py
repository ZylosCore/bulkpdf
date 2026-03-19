import customtkinter as ctk
import xml.etree.ElementTree as ET
import re
import os
import shutil
from pathlib import Path
from tkinter import filedialog, messagebox
from ..theme import BG_COLOR, TEXT_MAIN, ACCENT_PURPLE, FONT_FAMILY

class SettingsPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        # Get application version
        self.app_version = self.get_version()
        
        # Paths for signature management
        self.base_sig_dir = Path("src/assets/edit/signatures")
        self.default_sig_path = Path("src/assets/edit/user_signature.png")
        self.base_sig_dir.mkdir(parents=True, exist_ok=True)
        
        # --- HEADER ---
        self.label = ctk.CTkLabel(self, text="Paramètres de l'application", 
                                  font=(FONT_FAMILY, 20, "bold"), 
                                  text_color=TEXT_MAIN)
        self.label.pack(pady=(5, 20), anchor="w")
        
        # --- CONTAINER CARD ---
        self.card = ctk.CTkFrame(self, fg_color=("#ffffff", "#191a21"), 
                                  corner_radius=15, border_width=1, border_color=("#e0e0e0", "#44475a"))
        self.card.pack(fill="x", padx=2, pady=10)

        # --- THEME ROW ---
        self.row_theme = ctk.CTkFrame(self.card, fg_color="transparent")
        self.row_theme.pack(fill="x", padx=20, pady=(20, 10))

        self.mode_label = ctk.CTkLabel(self.row_theme, text="Thème de l'interface", 
                                       font=(FONT_FAMILY, 14), 
                                       text_color=TEXT_MAIN)
        self.mode_label.pack(side="left")

        self.mode_switch = ctk.CTkOptionMenu(self.row_theme, 
                                              values=["Dark", "Light", "System"],
                                              fg_color=ACCENT_PURPLE,
                                              button_color=ACCENT_PURPLE,
                                              button_hover_color="#664dff",
                                              font=(FONT_FAMILY, 12),
                                              command=self.change_appearance)
        self.mode_switch.pack(side="right")
        
        # --- SIGNATURE MANAGEMENT SECTION ---
        ctk.CTkLabel(self.card, text="Gestion des Signatures", font=(FONT_FAMILY, 16, "bold"), text_color=ACCENT_PURPLE).pack(padx=20, pady=(20, 10), anchor="w")
        
        # Add New Signature
        self.add_sig_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        self.add_sig_frame.pack(fill="x", padx=20, pady=10)
        
        self.sig_name_entry = ctk.CTkEntry(self.add_sig_frame, placeholder_text="Nom de la signature...", width=200)
        self.sig_name_entry.pack(side="left", padx=(0, 10))
        
        self.upload_btn = ctk.CTkButton(self.add_sig_frame, text="Ajouter PNG", 
                                        fg_color=ACCENT_PURPLE, command=self.upload_new_signature)
        self.upload_btn.pack(side="left")

        # Signature List & Default Selector
        self.list_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        self.list_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        self.sig_list_label = ctk.CTkLabel(self.list_frame, text="Signature par défaut :", font=(FONT_FAMILY, 14))
        self.sig_list_label.pack(side="left", padx=(0, 10))
        
        self.sig_selector = ctk.CTkOptionMenu(self.list_frame, values=["Aucune"], 
                                               command=self.set_default_signature,
                                               fg_color="#44475a", button_color="#6272a4")
        self.sig_selector.pack(side="left")
        
        self.refresh_signature_list()

        # --- INFO TEXT ---
        self.info = ctk.CTkLabel(self, 
                                 text=f"BulkPDF Pro v{self.app_version} - Build 2026", 
                                 font=(FONT_FAMILY, 11), 
                                 text_color=("#7f8c8d", "#6272a4"))
        self.info.pack(side="bottom", pady=20)

    def refresh_signature_list(self):
        """Scans the signature directory and updates the dropdown menu."""
        files = [f.stem for f in self.base_sig_dir.glob("*.png")]
        if not files:
            self.sig_selector.configure(values=["Aucune"])
            self.sig_selector.set("Aucune")
        else:
            self.sig_selector.configure(values=files)
            # Try to find which one is currently default by checking the 'user_signature.png' if possible
            # But simpler: just stay on current or pick first
            self.sig_selector.set(files[0])

    def upload_new_signature(self):
        """Uploads a new PNG file and saves it with the given name."""
        name = self.sig_name_entry.get().strip()
        if not name:
            messagebox.showwarning("Attention", "Veuillez donner un nom à votre signature.")
            return
            
        file_path = filedialog.askopenfilename(filetypes=[("Images PNG", "*.png")])
        if file_path:
            target_path = self.base_sig_dir / f"{name}.png"
            shutil.copy(file_path, target_path)
            self.sig_name_entry.delete(0, 'end')
            self.refresh_signature_list()
            messagebox.showinfo("Succès", f"Signature '{name}' ajoutée !")

    def set_default_signature(self, name):
        """Copies the selected signature file to the fixed path used by EditPage."""
        if name == "Aucune": return
        
        source = self.base_sig_dir / f"{name}.png"
        if source.exists():
            shutil.copy(source, self.default_sig_path)
            print(f"Default signature set to: {name}")

    def get_version(self):
        """Attempts to read version from project files."""
        xml_path = Path("project_info.xml")
        if xml_path.exists():
            try:
                tree = ET.parse(xml_path)
                return tree.getroot().find('version').text # type: ignore
            except: pass
        return "1.0.0"

    def change_appearance(self, new_mode):
        """Updates the application theme."""
        ctk.set_appearance_mode(new_mode)