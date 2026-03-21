import customtkinter as ctk
from ..i18n import t  
from ..theme import SIDEBAR_COLOR, ACCENT_BLUE, TEXT_MAIN, FONT_FAMILY, SIZE_TITLE, SIZE_MAIN
from ..icons_data import get_icon

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, selection_callback, **kwargs):
        super().__init__(master, width=220, corner_radius=0, fg_color=SIDEBAR_COLOR, **kwargs) # Menu un peu moins large
        self.selection_callback = selection_callback
        
        logo_img = get_icon("logo", size=(40, 40)) # Logo réduit
        self.logo_label = ctk.CTkLabel(
            self, text="BULK PDF", image=logo_img,
            compound="top", font=(FONT_FAMILY, SIZE_TITLE, "bold"), # Police réduite
            text_color=ACCENT_BLUE
        )
        self.logo_label.pack(pady=(25, 20), padx=20)

        self.buttons = {}
        
        menu_items = [
            ("merge", t("menu_merge"), "merge"),
            ("extract", t("menu_extract"), "image"), 
            ("edit", t("menu_edit"), "edit"),
            ("compress", t("menu_compress"), "compress"),
            ("protect", t("menu_protect"), "protect"),
            ("unlock", t("menu_unlock"), "unlock"),
            ("settings", t("menu_settings"), "settings")
        ]
        
        for id, label, icon_name in menu_items:
            self.buttons[id] = self._create_nav_btn(label, id, icon_name)

    def _create_nav_btn(self, text, page_id, icon_name):
        icon = get_icon(icon_name, size=(18, 18)) # Icônes réduites
        btn = ctk.CTkButton(
            self, text=f"  {text}", image=icon, compound="left",
            height=36, anchor="w", corner_radius=6, # Boutons moins hauts
            fg_color="transparent", text_color=TEXT_MAIN,
            font=(FONT_FAMILY, SIZE_MAIN), # Police réduite
            hover_color=("#e5e5e5", "#2d2f3b"),
            command=lambda p=page_id: self.select_btn(p)
        )
        btn.pack(fill="x", padx=15, pady=2) # Espacement réduit
        return btn

    def select_btn(self, page_id):
        for p_id, btn in self.buttons.items():
            is_sel = (p_id == page_id)
            btn.configure(
                fg_color=("#dcdcdc", "#343746") if is_sel else "transparent",
                text_color=ACCENT_BLUE if is_sel else TEXT_MAIN
            )
        self.selection_callback(page_id)