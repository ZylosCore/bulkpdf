import customtkinter as ctk
from .pdf_operations import PDFOperationsView
from ..theme import TEXT_TITLE, FONT_FAMILY, ACCENT_PURPLE

class UnlockPage(PDFOperationsView):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.label.configure(text="Remove PDF password", font=(FONT_FAMILY, 16, "bold"), text_color=TEXT_TITLE)
        self.run_btn.configure(text="Unlock PDF", fg_color=ACCENT_PURPLE)
