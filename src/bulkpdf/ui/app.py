import customtkinter as ctk
from .theme import BG_COLOR
from .views.sidebar import Sidebar
from .views.topbar import Topbar
from .views.pdf_operations import PDFOperationsView
from .views.compress_page import CompressPage
from .views.protect_page import ProtectPage
from .views.unlock_page import UnlockPage
from .views.extract_page import ExtractPage
from .views.settings_page import SettingsPage

class BulkPDFApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BulkPDF Pro - 4K Edition")
        self.geometry("1300x700")
        self.configure(fg_color=BG_COLOR)

        # Layout Configuration
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Main Content Container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=1, column=1, sticky="nsew", padx=30, pady=20)

        # Initialize Pages
        self.pages = {
            "merge": PDFOperationsView(self.container),
            "compress": CompressPage(self.container),
            "protect": ProtectPage(self.container),
            "unlock": UnlockPage(self.container),
            "extract": ExtractPage(self.container),
            "settings": SettingsPage(self.container)
        }

        # UI Components
        self.topbar = Topbar(self)
        self.topbar.grid(row=0, column=1, sticky="ew")

        self.sidebar = Sidebar(self, self.show_page)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        
        # Default Page
        self.show_page("merge")

    def show_page(self, page_id):
        """Displays page with a simple alpha-fade simulation"""
        if hasattr(self, 'pages'):
            # Hide all pages
            for p in self.pages.values():
                p.pack_forget()
            
            # Show selected page
            target_page = self.pages[page_id]
            target_page.pack(fill="both", expand=True)
            
            # Small animation effect: flash the background slightly 
            # to simulate a professional transition
            original_color = target_page.cget("fg_color")
            target_page.configure(fg_color="#2d2f3b")
            self.after(50, lambda: target_page.configure(fg_color="transparent"))

