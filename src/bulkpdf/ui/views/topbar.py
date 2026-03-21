import customtkinter as ctk
from ..theme import TOPBAR_COLOR, TEXT_LOW, FONT_FAMILY, SIZE_MAIN

class Topbar(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, height=40, corner_radius=0, fg_color=TOPBAR_COLOR, **kwargs)
        
        self.title_label = ctk.CTkLabel(
            self, text="BulkPDF Engine v2.0", 
            font=(FONT_FAMILY, SIZE_MAIN, "bold"), 
            text_color=TEXT_LOW
        )
        self.title_label.pack(side="left", padx=20)
        
        self.status = ctk.CTkLabel(
            self, text="● System Ready", 
            font=(FONT_FAMILY, SIZE_MAIN), 
            text_color="#27ae60" 
        )
        self.status.pack(side="right", padx=20)