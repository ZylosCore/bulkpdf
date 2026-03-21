import customtkinter as ctk
from ..theme import CARD_COLOR, BORDER_COLOR, TEXT_MAIN, TEXT_LOW, ACCENT_GREEN

class FileCard(ctk.CTkFrame):
    def __init__(self, master, file_path, remove_callback, **kwargs):
        super().__init__(master, fg_color=CARD_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=8, **kwargs)
        self.file_path = file_path
        
        self.status_label = ctk.CTkLabel(self, text="", font=("Segoe UI Variable Display", 12))
        self.status_label.pack(side="left", padx=(10, 0))

        self.name_label = ctk.CTkLabel(self, text=file_path.name, font=("Segoe UI Variable Display", 12, "bold"), text_color=TEXT_MAIN)
        self.name_label.pack(side="left", padx=10, pady=10)
        
        self.path_label = ctk.CTkLabel(self, text=str(file_path.parent)[:30] + "...", font=("Segoe UI Variable Display", 10), text_color=TEXT_LOW)
        self.path_label.pack(side="left", padx=10)

        self.del_btn = ctk.CTkButton(self, text="×", width=25, height=25, fg_color="transparent", 
                                    text_color="#e74c3c", hover_color=("#fee2e2", "#451a1a"),
                                    command=lambda: remove_callback(self))
        self.del_btn.pack(side="right", padx=10)

    def mark_success(self):
        """Affiche la pastille verte 🟢"""
        self.status_label.configure(text="🟢")
        self.configure(border_color=ACCENT_GREEN)