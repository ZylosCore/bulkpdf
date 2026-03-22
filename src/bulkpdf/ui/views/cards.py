import customtkinter as ctk
from ..theme import BG_COLOR, BORDER_COLOR, TEXT_MAIN, TEXT_LOW, ACCENT_SUCCESS, ACCENT_DANGER, FONT_FAMILY, CORNER_RADIUS, SIZE_MAIN, SIZE_SMALL

class FileCard(ctk.CTkFrame):
    def __init__(self, master, file_path, remove_callback, **kwargs):
        # Utilisation de BG_COLOR pour contraster avec la liste
        super().__init__(master, fg_color=BG_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=CORNER_RADIUS, **kwargs)
        self.file_path = file_path
        
        self.status_label = ctk.CTkLabel(self, text="", font=(FONT_FAMILY, SIZE_SMALL))
        self.status_label.pack(side="left", padx=(10, 0))

        self.name_label = ctk.CTkLabel(self, text=file_path.name, font=(FONT_FAMILY, SIZE_MAIN, "bold"), text_color=TEXT_MAIN)
        self.name_label.pack(side="left", padx=10, pady=8) 
        
        self.path_label = ctk.CTkLabel(self, text=str(file_path.parent)[:40] + "...", font=(FONT_FAMILY, SIZE_SMALL), text_color=TEXT_LOW)
        self.path_label.pack(side="left", padx=10)

        self.del_btn = ctk.CTkButton(
            self, text="✕", width=24, height=24, corner_radius=4,
            font=(FONT_FAMILY, SIZE_MAIN),
            fg_color="transparent", text_color=ACCENT_DANGER, 
            hover_color=("#FEE2E2", "#451A1A"),
            command=lambda: remove_callback(self)
        )
        self.del_btn.pack(side="right", padx=10)

    def mark_success(self):
        self.status_label.configure(text="🟢")
        self.configure(border_color=ACCENT_SUCCESS)