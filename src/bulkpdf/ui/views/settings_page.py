import customtkinter as ctk
import xml.etree.ElementTree as ET
import re
from pathlib import Path
from ..theme import BG_COLOR, TEXT_MAIN, ACCENT_PURPLE, FONT_FAMILY

class SettingsPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        # --- RÉCUPÉRATION DE LA VERSION ---
        self.app_version = self.get_version()
        
        # Header
        self.label = ctk.CTkLabel(self, text="Application Settings", 
                                  font=(FONT_FAMILY, 20, "bold"), 
                                  text_color=TEXT_MAIN)
        self.label.pack(pady=(5, 20), anchor="w")
        
        # Container Card
        self.card = ctk.CTkFrame(self, fg_color=("#ffffff", "#191a21"), 
                                  corner_radius=15, border_width=1, border_color=("#e0e0e0", "#44475a"))
        self.card.pack(fill="x", padx=2, pady=10)

        # Appearance Row
        self.row = ctk.CTkFrame(self.card, fg_color="transparent")
        self.row.pack(fill="x", padx=20, pady=20)

        self.mode_label = ctk.CTkLabel(self.row, text="Interface Theme", 
                                       font=(FONT_FAMILY, 14), 
                                       text_color=TEXT_MAIN)
        self.mode_label.pack(side="left")

        self.mode_switch = ctk.CTkOptionMenu(self.row, 
                                              values=["Dark", "Light", "System"],
                                              fg_color=ACCENT_PURPLE,
                                              button_color=ACCENT_PURPLE,
                                              button_hover_color="#664dff",
                                              font=(FONT_FAMILY, 12),
                                              command=self.change_appearance)
        self.mode_switch.pack(side="right")
        
        # Info Text (Affiche maintenant la version dynamique)
        self.info = ctk.CTkLabel(self, 
                                 text=f"BulkPDF Pro v{self.app_version} - Build 2026", 
                                 font=(FONT_FAMILY, 11), 
                                 text_color=("#7f8c8d", "#6272a4"))
        self.info.pack(side="bottom", pady=20)

    def get_version(self):
        """Tente de lire la version depuis XML, sinon TXT, sinon renvoie défaut."""
        # 1. Tentative via XML (Le plus propre)
        xml_path = Path("project_info.xml")
        if xml_path.exists():
            try:
                tree = ET.parse(xml_path)
                return tree.getroot().find('version').text
            except:
                pass

        # 2. Tentative via version_info.txt (PyInstaller)
        txt_path = Path("version_info.txt")
        if txt_path.exists():
            try:
                content = txt_path.read_text(encoding="utf-8")
                match = re.search(r"StringStruct\(u'ProductVersion', u'([\d.]+)'\)", content)
                if match:
                    return match.group(1)
            except:
                pass

        return "1.0.0" # Valeur par défaut

    def change_appearance(self, new_mode):
        ctk.set_appearance_mode(new_mode)