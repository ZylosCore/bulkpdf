import customtkinter as ctk
from ..i18n import t  
# Remplacement de ACCENT_BLUE par ACCENT_PRIMARY
from ..theme import SIDEBAR_COLOR, ACCENT_PRIMARY, TEXT_MAIN, FONT_FAMILY, SIZE_TITLE, SIZE_MAIN, LOGO_FONT, LOGO_COLOR
from ..icons_data import get_icon

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, selection_callback, **kwargs):
        super().__init__(master, width=220, corner_radius=0, fg_color=SIDEBAR_COLOR, **kwargs)
        self.selection_callback = selection_callback
        
        # Logo stylisé avec la couleur et police Neo-Productivity
        logo_img = get_icon("logo", size=(40, 40)) 
        self.logo_label = ctk.CTkLabel(
            self, text="BULK PDF", image=logo_img,
            compound="top", font=(LOGO_FONT, 18, "bold"), 
            text_color=LOGO_COLOR
        )
        self.logo_label.pack(pady=(25, 20), padx=20)

        self.buttons = {}
        
        # Menu combiné
        menu_items = [
            ("merge", t("menu_merge"), "merge"),
            ("extract", "Split & Extract", "image"), 
            ("edit", t("menu_edit"), "edit"),
            ("compress", t("menu_compress"), "compress"),
            ("security", "Security", "protect") 
        ]
        
        for id, label, icon_name in menu_items:
            self.buttons[id] = self._create_nav_btn(label, id, icon_name)
            self.buttons[id].pack(fill="x", padx=15, pady=2)

        # Bouton Paramètres en bas
        self.settings_btn = self._create_nav_btn(t("menu_settings"), "settings", "settings")
        self.settings_btn.pack(side="bottom", fill="x", padx=15, pady=(0, 20))
        self.buttons["settings"] = self.settings_btn

    def _create_nav_btn(self, text, page_id, icon_name):
        icon = get_icon(icon_name, size=(18, 18))
        btn = ctk.CTkButton(
            self, text=f"  {text}", image=icon, compound="left",
            height=36, anchor="w", corner_radius=6, 
            fg_color="transparent", text_color=TEXT_MAIN,
            font=(FONT_FAMILY, SIZE_MAIN), 
            # Couleurs de survol adaptées au thème Zinc
            hover_color=("#E4E4E7", "#27272A"),
            command=lambda p=page_id: self.select_btn(p)
        )
        return btn

    def select_btn(self, page_id):
        for p_id, btn in self.buttons.items():
            is_sel = (p_id == page_id)
            btn.configure(
                # Fond de l'élément sélectionné
                fg_color=("#E4E4E7", "#27272A") if is_sel else "transparent",
                # Texte en ACCENT_PRIMARY si sélectionné
                text_color=ACCENT_PRIMARY if is_sel else TEXT_MAIN
            )
        self.selection_callback(page_id)