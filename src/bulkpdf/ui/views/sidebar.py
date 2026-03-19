import customtkinter as ctk
from ..theme import SIDEBAR_COLOR, ACCENT_PURPLE, TEXT_MAIN, FONT_FAMILY
from ..icons_data import get_icon

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, selection_callback, **kwargs):
        super().__init__(master, width=260, corner_radius=0, fg_color=SIDEBAR_COLOR, **kwargs)
        self.selection_callback = selection_callback
        
        logo_img = get_icon("logo", size=(80, 80))
        self.logo_label = ctk.CTkLabel(self, text="BULK PDF", image=logo_img,
                                     compound="top", font=(FONT_FAMILY, 22, "bold"), 
                                     text_color=ACCENT_PURPLE)
        self.logo_label.pack(pady=(30, 25), padx=20)

        self.buttons = {}
        menu_items = [
            ("merge", "Fusionner", "merge"),
            ("edit", "Éditeur PDF", "edit"),      # <--- Nouveau bouton
            ("compress", "Compresser", "compress"),
            ("protect", "Protéger", "protect"),
            ("unlock", "Déverrouiller", "unlock"),
            ("extract", "Images", "image"),
            ("settings", "Paramètres", "settings")
        ]
        
        for id, label, icon_name in menu_items:
            self.buttons[id] = self._create_nav_btn(label, id, icon_name)

    def _create_nav_btn(self, text, page_id, icon_name):
        icon = get_icon(icon_name, size=(24, 24))
        btn = ctk.CTkButton(self, text=f"  {text}", image=icon, compound="left",
                           height=50, anchor="w", corner_radius=12,
                           fg_color="transparent", text_color=TEXT_MAIN,
                           font=(FONT_FAMILY, 14),
                           hover_color=("#e5e5e5", "#2d2f3b"),
                           command=lambda p=page_id: self.select_btn(p))
        btn.pack(fill="x", padx=20, pady=5)
        return btn

    def select_btn(self, page_id):
        for p_id, btn in self.buttons.items():
            is_sel = (p_id == page_id)
            btn.configure(
                fg_color=("#dcdcdc", "#343746") if is_sel else "transparent",
                text_color=ACCENT_PURPLE if is_sel else TEXT_MAIN
            )
        self.selection_callback(page_id)