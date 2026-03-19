import customtkinter as ctk
from .views.sidebar import Sidebar
from .views.topbar import Topbar
from .views.merge_page import MergePage
from .views.compress_page import CompressPage
from .views.protect_page import ProtectPage
from .views.unlock_page import UnlockPage
from .views.extract_page import ExtractPage
from .views.settings_page import SettingsPage
from .views.edit_page import EditPage  # <-- AJOUT

class BulkPDFApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("BulkPDF - Professional PDF Suite")
        self.geometry("1100x700")

        # Layout principal
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = Sidebar(self, selection_callback=self.show_page)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # Conteneur de pages
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # Initialisation des pages
        self.pages = {
            "merge": MergePage(self.main_container),
            "edit": EditPage(self.main_container),      # <-- AJOUT (Régle le KeyError)
            "compress": CompressPage(self.main_container),
            "protect": ProtectPage(self.main_container),
            "unlock": UnlockPage(self.main_container),
            "extract": ExtractPage(self.main_container),
            "settings": SettingsPage(self.main_container)
        }

        # Afficher la page par défaut
        self.show_page("merge")

    def show_page(self, page_id):
        # Cacher toutes les pages
        for page in self.pages.values():
            page.grid_forget()
        
        # Afficher la page demandée
        target_page = self.pages[page_id]
        target_page.grid(row=0, column=0, sticky="nsew")