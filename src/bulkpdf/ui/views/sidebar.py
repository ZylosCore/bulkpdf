import customtkinter as ctk
from PIL import Image
import os, sys
from pathlib import Path
from ..theme import SIDEBAR_COLOR, ACCENT_PURPLE, TEXT_MAIN, FONT_FAMILY

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, selection_callback, **kwargs):
        super().__init__(master, width=220, corner_radius=0, fg_color=SIDEBAR_COLOR, **kwargs)
        self.selection_callback = selection_callback
        
        base_path = Path(os.path.abspath(sys.argv[0])).parent
        self.icon_path = base_path / "src" / "assets" / "icons"
        
        ctk.CTkLabel(self, text="BULK PDF", font=(FONT_FAMILY, 22, "bold"), 
                     text_color=ACCENT_PURPLE).pack(pady=(40, 30))

        self.buttons = {}
        menu_items = [
            ("merge", "Merge PDF", "merge.png"),
            ("compress", "Compress", "compress.png"),
            ("protect", "Protect", "protect.png"),
            ("unlock", "Unlock", "unlock.png"),
            ("extract", "Images", "image.png"),
            ("settings", "Settings", "settings.png")
        ]
        for id, label, icon in menu_items:
            self.buttons[id] = self._create_nav_btn(label, id, icon)

    def _get_colored_icon(self, path, is_dark_mode=True):
        img = Image.open(path).convert("RGBA")
        data = img.getdata()
        rgb = (255, 255, 255) if is_dark_mode else (44, 62, 80)
        new_data = [(rgb[0], rgb[1], rgb[2], item[3]) for item in data]
        img.putdata(new_data)
        return img

    def _load_icon(self, icon_name):
        full_path = self.icon_path / icon_name
        if full_path.exists():
            img_light = self._get_colored_icon(full_path, is_dark_mode=False)
            img_dark = self._get_colored_icon(full_path, is_dark_mode=True)
            return ctk.CTkImage(light_image=img_light, dark_image=img_dark, size=(20, 20))
        return None

    def _create_nav_btn(self, text, page_id, icon_name):
        icon = self._load_icon(icon_name)
        btn = ctk.CTkButton(self, text=f"  {text}", image=icon, compound="left",
                           height=45, anchor="w", corner_radius=10,
                           fg_color="transparent", text_color=TEXT_MAIN,
                           font=(FONT_FAMILY, 13),
                           hover_color=("#e5e5e5", "#2d2f3b"),
                           command=lambda: self.select_btn(page_id))
        btn.pack(fill="x", padx=15, pady=3)
        return btn

    def select_btn(self, page_id):
        for p_id, btn in self.buttons.items():
            is_sel = (p_id == page_id)
            btn.configure(
                fg_color=("#dcdcdc", "#343746") if is_sel else "transparent",
                text_color=ACCENT_PURPLE if is_sel else TEXT_MAIN
            )
        self.selection_callback(page_id)
