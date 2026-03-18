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
