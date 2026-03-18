import customtkinter as ctk
import os
import ctypes
from bulkpdf.ui.navigation import NavigationView

class BulkPDFApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Force l'ID pour l'icône Windows
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('bulk.pdf.pro.unique.id')
        except:
            pass

        self.title("BulkPDF Pro")
        self.geometry("1100x700")

        # Icône de la fenêtre
        base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_dir, "assets", "app_icon.ico")
        
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
            self.after(200, lambda: self.wm_iconbitmap(icon_path))

        # Setup Layout
        self.nav = NavigationView(self, lambda p: print(f"Nav: {p}"))
        self.nav.pack(side="left", fill="y")

if __name__ == "__main__":
    app = BulkPDFApp()
    app.mainloop()
