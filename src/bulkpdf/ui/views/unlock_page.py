import customtkinter as ctk
from .pdf_operations import PDFOperationsView
from ..theme import TEXT_TITLE, FONT_FAMILY, SIZE_TITLE, SIZE_MAIN, CORNER_RADIUS, BORDER_COLOR

class UnlockPage(PDFOperationsView):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.mode_name = "unlocked"
        
        self.label.configure(text="remove password", font=(FONT_FAMILY, SIZE_TITLE, "bold"), text_color=TEXT_TITLE)
        
        self.password_entry = ctk.CTkEntry(
            self.action_bar, placeholder_text="password...", 
            show="*", width=150, height=30,
            corner_radius=CORNER_RADIUS, border_color=BORDER_COLOR, font=(FONT_FAMILY, SIZE_MAIN)
        )
        self.password_entry.pack(side="left", padx=10)