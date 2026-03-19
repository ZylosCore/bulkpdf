import customtkinter as ctk
from .views.merge_page import MergePage
from .views.compress_page import CompressPage
from .views.protect_page import ProtectPage
from .views.unlock_page import UnlockPage
from .views.extract_page import ExtractPage
from .views.settings_page import SettingsPage
from .views.edit_page import EditPage # <--- Importation

class Navigation:
    def __init__(self, container):
        self.container = container
        self.pages = {}
        
        # Initialisation
        self.pages["merge"] = MergePage(self.container)
        self.pages["compress"] = CompressPage(self.container)
        self.pages["protect"] = ProtectPage(self.container)
        self.pages["unlock"] = UnlockPage(self.container)
        self.pages["extract"] = ExtractPage(self.container)
        self.pages["settings"] = SettingsPage(self.container)
        self.pages["edit"] = EditPage(self.container) # <--- Ajout au dictionnaire
        
        for page in self.pages.values():
            page.pack_forget()

    def show_page(self, page_id):
        for id, page in self.pages.items():
            if id == page_id:
                page.pack(fill="both", expand=True)
            else:
                page.pack_forget()