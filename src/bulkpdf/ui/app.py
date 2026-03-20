import os
import sys
from pathlib import Path
import customtkinter as ctk
from PIL import Image, ImageTk
from .i18n import t  
from .views.sidebar import Sidebar
from .views.topbar import Topbar
from .views.merge_page import MergePage
from .views.compress_page import CompressPage
from .views.protect_page import ProtectPage
from .views.unlock_page import UnlockPage
from .views.extract_page import ExtractPage
from .views.settings_page import SettingsPage
from .views.edit_page import EditPage

def get_resource_path(filename):
    """ Fonction infaillible pour trouver les assets (.py et .exe) """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, "assets", filename)
        
    current_dir = Path(__file__).resolve().parent
    for _ in range(5):
        p = current_dir / "assets" / filename
        if p.exists(): return str(p)
        current_dir = current_dir.parent
    return filename

class BulkPDFApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(t("app_title"))
        self.geometry("1100x700")
        
        # --- APPLICATION DE L'ICÔNE ---
        ico_path = get_resource_path("logo.ico")
        png_path = get_resource_path("logo.png")
        
        # 1. On applique le vrai fichier .ico pour Windows
        if os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except: pass
            
        # 2. Secours très puissant : on injecte l'icône via PIL pour la barre des tâches
        if os.path.exists(png_path):
            try:
                img = ImageTk.PhotoImage(Image.open(png_path))
                # Le paramètre 'True' force cette icône comme icône par défaut de la fenêtre
                self.iconphoto(True, img)
            except: pass

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self, selection_callback=self.show_page)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        self.pages = {
            "merge": MergePage(self.main_container),
            "extract": ExtractPage(self.main_container),
            "edit": EditPage(self.main_container),
            "compress": CompressPage(self.main_container),
            "protect": ProtectPage(self.main_container),
            "unlock": UnlockPage(self.main_container),
            "settings": SettingsPage(self.main_container)
        }

        self.show_page("merge")

    def show_page(self, page_id):
        for page in self.pages.values():
            page.grid_forget()
        target_page = self.pages[page_id]
        target_page.grid(row=0, column=0, sticky="nsew")