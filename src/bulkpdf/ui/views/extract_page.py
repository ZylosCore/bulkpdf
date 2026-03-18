import customtkinter as ctk
from tkinter import filedialog
from .pdf_operations import PDFOperationsView
from ..theme import TEXT_TITLE, FONT_FAMILY, ACCENT_PURPLE

class ExtractPage(PDFOperationsView):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.label.configure(text="Extract images from PDF", font=(FONT_FAMILY, 16, "bold"), text_color=TEXT_TITLE)
        self.run_btn.configure(text="Extract images", fg_color=ACCENT_PURPLE)

    def execute_merge(self):
        if not self.files_paths: return
        out_dir = filedialog.askdirectory(title="Select output folder for images")
        if out_dir:
            self.progress.pack(fill="x", pady=10)
            from ...pdf_engine import PDFTask
            task = PDFTask(self.files_paths, out_dir, self.on_progress, self.on_done, mode="extract")
            task.start()
