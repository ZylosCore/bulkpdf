import customtkinter as ctk
from .pdf_operations import PDFOperationsView
class UnlockPage(PDFOperationsView):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.mode_name = "unlocked"
        self.label.configure(text="remove password")
        self.password_entry = ctk.CTkEntry(self.action_bar, placeholder_text="password...", show="*", width=150)
        self.password_entry.pack(side="left", padx=10)
