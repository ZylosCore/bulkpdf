import os
import sys
import multiprocessing
from pathlib import Path
import customtkinter as ctk
from PIL import Image

# --- FIX 4K / HIGH DPI & BARRE DES TACHES (Windows) ---
if os.name == 'nt':
    try:
        import ctypes
        # Forcer la netteté parfaite sur les écrans 4K (DPI Awareness v2)
        ctypes.windll.shcore.SetProcessDpiAwareness(2) 
        # Identifiant pour la barre des tâches
        myappid = 'zyloscore.bulkpdf.app.1.0' 
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

# Force l'UI à utiliser l'échelle native de l'OS (Fluidité 4K)
ctk.set_window_scaling(1.0)
ctk.set_widget_scaling(1.0)

def resource_path(relative_path):
    try:
        base_path = Path(sys._MEIPASS)
    except Exception:
        base_path = Path(__file__).parent.resolve()
    paths_to_check = [
        base_path / relative_path,
        base_path.parent / relative_path,
        base_path / "assets" / Path(relative_path).name
    ]
    for p in paths_to_check:
        if p.exists(): return p
    return base_path / relative_path

class SplashScreen(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Style Adobe Splash (Petit, rectangulaire, sans bordure)
        self.overrideredirect(True)  
        width, height = 450, 250
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        self.configure(fg_color="#1e1e1e") # Gris foncé Pro

        icon_path = resource_path("logo.ico")
        png_path = resource_path("logo.png")
        if icon_path.exists():
            try: self.iconbitmap(str(icon_path))
            except: pass

        self.after(10, self._show_in_taskbar)

        # Conteneur central
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(expand=True)

        if png_path.exists():
            try:
                img = Image.open(str(png_path)).convert("RGBA")
                self.logo = ctk.CTkImage(light_image=img, dark_image=img, size=(60, 60))
                ctk.CTkLabel(container, text="", image=self.logo).pack(pady=(0, 10))
            except: pass
        
        # Titre façon Adobe
        ctk.CTkLabel(container, text="BULK PDF", font=("Segoe UI Variable Display", 28, "bold"), text_color="#ffffff").pack()
        ctk.CTkLabel(container, text="Workspace Edition", font=("Segoe UI", 12), text_color="#eb0000").pack(pady=(0, 20))
        
        # Barre de progression très fine (minimaliste)
        self.progressbar = ctk.CTkProgressBar(self, width=250, height=2, progress_color="#eb0000", fg_color="#3e3e42", mode="indeterminate")
        self.progressbar.pack(side="bottom", pady=20)
        self.progressbar.start()
        
        self.after(2500, self._finish_loading) 

    def _show_in_taskbar(self):
        if os.name == 'nt':
            try:
                import ctypes
                hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
                style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
                style = style & ~0x00000080
                style = style | 0x00040000
                ctypes.windll.user32.SetWindowLongW(hwnd, -20, style)
                self.wm_withdraw()
                self.wm_deiconify()
            except: pass

    def _finish_loading(self):
        self.progressbar.stop()
        self.destroy()

def main():
    splash = SplashScreen()
    splash.mainloop()
    
    from bulkpdf.ui.app import BulkPDFApp
    app = BulkPDFApp()
    
    icon_path = resource_path("logo.ico")
    if icon_path.exists():
        try: app.iconbitmap(str(icon_path))
        except: pass
        
    app.mainloop()

if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()