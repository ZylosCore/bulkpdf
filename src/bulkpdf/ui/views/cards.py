import customtkinter as ctk
from ..theme import CARD_COLOR, BORDER_COLOR, TEXT_MAIN, TEXT_LOW, FONT_FAMILY

class FileCard(ctk.CTkFrame):
    def __init__(self, master, file_path, remove_callback, **kwargs):
        super().__init__(master, fg_color=CARD_COLOR, border_width=1, 
                         border_color=BORDER_COLOR, corner_radius=10, **kwargs)
        self.file_path = file_path
        
        # Nom du fichier
        self.name_label = ctk.CTkLabel(self, text=file_path.name, 
                                       font=(FONT_FAMILY, 13, "bold"),
                                       text_color=TEXT_MAIN)
        self.name_label.pack(side="left", padx=15, pady=10)
        
        # Bouton supprimer (Rouge discret)
        self.del_btn = ctk.CTkButton(self, text="×", width=30, height=30,
                                     fg_color="transparent", text_color="#e74c3c",
                                     hover_color=("#fee2e2", "#3d2b2b"),
                                     command=lambda: remove_callback(self))
        self.del_btn.pack(side="right", padx=10)

        # Chemin du dossier (Petit texte)
        self.path_label = ctk.CTkLabel(self, text=str(file_path.parent)[:50] + "...", 
                                       font=(FONT_FAMILY, 11),
                                       text_color=TEXT_LOW)
        self.path_label.pack(side="right", padx=20)
