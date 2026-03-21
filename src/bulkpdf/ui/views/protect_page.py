import customtkinter as ctk
from tkinter import messagebox, filedialog
from .pdf_operations import PDFOperationsView
from ..theme import TEXT_TITLE, FONT_FAMILY, SIZE_TITLE, SIZE_MAIN, CORNER_RADIUS, BORDER_COLOR, BTN_PRIMARY

class ProtectPage(PDFOperationsView):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.mode_name = "encrypted"
        
        self.label.configure(text="password protection", font=(FONT_FAMILY, SIZE_TITLE, "bold"), text_color=TEXT_TITLE)
        
        self.password_entry = ctk.CTkEntry(
            self.action_bar, placeholder_text="set password...", 
            show="*", width=160, height=30, 
            corner_radius=CORNER_RADIUS, border_color=BORDER_COLOR, font=(FONT_FAMILY, SIZE_MAIN)
        )
        self.password_entry.pack(side="left", padx=10)
        
        self.run_btn.configure(text="Protect PDF", fg_color=BTN_PRIMARY)

    def execute_task(self):
        if not self.files_paths:
            messagebox.showwarning("Selection Error", "Please add a PDF file first.")
            return

        pw = self.password_entry.get().strip()
        if not pw:
            messagebox.showwarning("Security Required", "Password cannot be empty. Please set a password to encrypt the file.")
            return

        out = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=self.get_smart_filename())
        if out:
            self.progress.pack(fill="x", pady=10)
            from ...pdf_engine import PDFTask
            task = PDFTask(self.files_paths, out, self.on_progress, self.on_done, mode="encrypted", password=pw)
            task.start()