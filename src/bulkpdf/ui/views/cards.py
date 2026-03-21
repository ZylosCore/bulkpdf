import customtkinter as ctk
from ..theme import CARD_COLOR, BORDER_COLOR, TEXT_MAIN, TEXT_LOW, ACCENT_GREEN, FONT_FAMILY, CORNER_RADIUS, SIZE_MAIN, SIZE_SMALL

class FileCard(ctk.CTkFrame):
    def __init__(self, master, file_path, remove_callback, **kwargs):
        super().__init__(master, fg_color=CARD_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=CORNER_RADIUS, **kwargs)
        self.file_path = file_path
        
        self.status_label = ctk.CTkLabel(self, text="", font=(FONT_FAMILY, SIZE_SMALL))
        self.status_label.pack(side="left", padx=(10, 0))

        # Tailles réduites (SIZE_MAIN au lieu de 12/13, SIZE_SMALL au lieu de 10/11)
        self.name_label = ctk.CTkLabel(self, text=file_path.name, font=(FONT_FAMILY, SIZE_MAIN, "bold"), text_color=TEXT_MAIN)
        self.name_label.pack(side="left", padx=10, pady=8) # Padding réduit pour affiner la carte
        
        self.path_label = ctk.CTkLabel(self, text=str(file_path.parent)[:40] + "...", font=(FONT_FAMILY, SIZE_SMALL), text_color=TEXT_LOW)
        self.path_label.pack(side="left", padx=10)

        # Bouton supprimer très fin et petit
        self.del_btn = ctk.CTkButton(
            self, text="✕", width=24, height=24, corner_radius=4,
            font=(FONT_FAMILY, SIZE_MAIN),
            fg_color="transparent", text_color="#e74c3c", 
            hover_color=("#fee2e2", "#451a1a"),
            command=lambda: remove_callback(self)
        )
        self.del_btn.pack(side="right", padx=10)

    def mark_success(self):
        self.status_label.configure(text="🟢")
        self.configure(border_color=ACCENT_GREEN)