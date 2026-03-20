import os
import sys
import multiprocessing
from pathlib import Path
import customtkinter as ctk
from PIL import Image

# --- FIX LOGO BARRE DES TACHES (Windows) ---
if os.name == 'nt':
    try:
        import ctypes
        # On définit un identifiant unique pour ton application
        myappid = 'zyloscore.bulkpdf.app.1.0' 
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

def resource_path(relative_path):
    """ Gestion des ressources pour trouver le logo (.py et .exe) """
    try:
        base_path = Path(sys._MEIPASS)
    except Exception:
        base_path = Path(__file__).parent.resolve()
    
    # Recherche dans src/assets ou assets
    paths_to_check = [
        base_path / relative_path,
        base_path.parent / relative_path,
        base_path / "assets" / Path(relative_path).name
    ]
    for p in paths_to_check:
        if p.exists():
            return p
    return base_path / relative_path

class SplashScreen(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 1. Supprime les bordures
        self.overrideredirect(True)  
        
        # 2. Dimensions et centrage
        width, height = 500, 300
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        self.configure(fg_color="#1E1E2E")

        # --- CHARGEMENT DES ICONES ---
        # On charge le .ico pour la barre des tâches et le .png pour le visuel
        icon_path = resource_path("logo.ico")
        png_path = resource_path("logo.png")
        
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except: pass

        # Hack pour forcer l'apparition dans la barre des tâches (indispensable avec overrideredirect)
        self.after(10, self._show_in_taskbar)

        # --- LOGO VISUEL ---
        self.logo = None
        if png_path.exists():
            try:
                img = Image.open(str(png_path)).convert("RGBA")
                self.logo = ctk.CTkImage(light_image=img, dark_image=img, size=(100, 100))
            except: pass

        if self.logo:
            self.logo_lbl = ctk.CTkLabel(self, text="", image=self.logo)
            self.logo_lbl.pack(pady=(40, 10))
        
        # --- TITRE & CHARGEMENT ---
        self.title_lbl = ctk.CTkLabel(self, text="BULK PDF", font=("Segoe UI", 32, "bold"), text_color="#BD93F9")
        self.title_lbl.pack()
        
        self.loading_lbl = ctk.CTkLabel(self, text="Initialisation...", font=("Segoe UI", 12), text_color="#A9A9B3")
        self.loading_lbl.pack(pady=(20, 5))
        
        self.progressbar = ctk.CTkProgressBar(self, width=300, height=4, progress_color="#BD93F9", fg_color="#44475A", mode="indeterminate")
        self.progressbar.pack(pady=5)
        self.progressbar.start() # Animation infinie plus "sophistiquée"
        
        self.progress = 0
        self.after(3000, self._finish_loading) # Simulation de chargement de 3s

    def _show_in_taskbar(self):
        """ Hack Windows pour forcer l'affichage dans la barre des tâches """
        if os.name == 'nt':
            try:
                import ctypes
                # GWL_EXSTYLE = -20, WS_EX_APPWINDOW = 0x00040000
                hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
                style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
                style = style & ~0x00000080 # Enlever WS_EX_TOOLWINDOW
                style = style | 0x00040000  # Ajouter WS_EX_APPWINDOW
                ctypes.windll.user32.SetWindowLongW(hwnd, -20, style)
                # On redessine la barre des tâches
                self.wm_withdraw()
                self.wm_deiconify()
            except: pass

    def _finish_loading(self):
        self.progressbar.stop()
        self.destroy()

def main():
    splash = SplashScreen()
    splash.mainloop()
    
    # Importation après le splash pour la performance
    from bulkpdf.ui.app import BulkPDFApp
    app = BulkPDFApp()
    
    # On remet l'icône sur l'application principale aussi
    icon_path = resource_path("logo.ico")
    if icon_path.exists():
        try: app.iconbitmap(str(icon_path))
        except: pass
        
    app.mainloop()

if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()