import sys
import os
from pathlib import Path

# Fix DPI pour le 4K / HD
if sys.platform == "win32":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

try:
    import customtkinter as ctk
    from bulkpdf.ui.app import BulkPDFApp
    
    # Mode sombre forcé pour le look "Pro"
    ctk.set_appearance_mode("dark")
    
    if __name__ == "__main__":
        app = BulkPDFApp()
        app.mainloop()
except Exception as e:
    print(f"Erreur fatale : {e}")
