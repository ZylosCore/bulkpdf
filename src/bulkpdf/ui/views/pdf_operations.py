import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from datetime import datetime
from .cards import FileCard
from ...pdf_engine import PDFTask
from ..theme import (CARD_COLOR, BORDER_COLOR, TEXT_LOW, TEXT_TITLE, FONT_FAMILY,
                     CORNER_RADIUS, BTN_PRIMARY, BTN_PRIMARY_HOVER, 
                     BTN_SUCCESS, BTN_SUCCESS_HOVER, SIZE_TITLE, SIZE_MAIN)

class PDFOperationsView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.files_paths = []
        self.mode_name = "processed"
        
        self.label = ctk.CTkLabel(self, text="PDF Operation", font=(FONT_FAMILY, SIZE_TITLE, "bold"), text_color=TEXT_TITLE)
        self.label.pack(pady=(20, 10), padx=40, anchor="w")
        
        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color=CARD_COLOR, border_width=1, border_color=BORDER_COLOR, 
            corner_radius=CORNER_RADIUS
        )
        self.scroll.pack(fill="both", expand=True, padx=40, pady=(0, 10))
        
        self.empty_label = ctk.CTkLabel(self.scroll, text="No files selected", font=(FONT_FAMILY, SIZE_MAIN), text_color=TEXT_LOW)
        self.empty_label.pack(pady=60)

        self.progress = ctk.CTkProgressBar(self, progress_color=BTN_PRIMARY, height=4, corner_radius=2)

        self.action_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.action_bar.pack(fill="x", pady=(0, 20), padx=40)
        
        # MODIF: Reduced height to 30, width to 100
        self.add_btn = ctk.CTkButton(
            self.action_bar, text="+ Add Files", width=100, height=30, 
            corner_radius=CORNER_RADIUS, font=(FONT_FAMILY, SIZE_MAIN, "bold"),
            fg_color=BTN_PRIMARY, hover_color=BTN_PRIMARY_HOVER, command=self.browse_files
        )
        self.add_btn.pack(side="left")

        # MODIF: Reduced height to 30, width to 120, forced white text
        self.run_btn = ctk.CTkButton(
            self.action_bar, text="Run Task", width=120, height=30, text_color="#FFFFFF",
            corner_radius=CORNER_RADIUS, font=(FONT_FAMILY, SIZE_MAIN, "bold"),
            fg_color=BTN_SUCCESS, hover_color=BTN_SUCCESS_HOVER, command=self.execute_task
        )
        self.run_btn.pack(side="right")

    def get_smart_filename(self):
        date_str = datetime.now().strftime("%Y-%m-%d")
        base = Path(self.files_paths[0]).stem if self.files_paths else "document"
        return f"{base}_{self.mode_name}_{date_str}.pdf"

    def browse_files(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
        if files:
            if self.empty_label.winfo_exists(): self.empty_label.pack_forget()
            for f in files:
                p = Path(f)
                if p not in self.files_paths:
                    self.files_paths.append(p)
                    FileCard(self.scroll, p, self.remove_file).pack(fill="x", padx=10, pady=4)

    def remove_file(self, card):
        if card.file_path in self.files_paths: 
            self.files_paths.remove(card.file_path)
        card.destroy()
        
        if not self.files_paths:
            self.empty_label = ctk.CTkLabel(self.scroll, text="No files selected", font=(FONT_FAMILY, SIZE_MAIN), text_color=TEXT_LOW)
            self.empty_label.pack(pady=60)

    def execute_task(self):
        if not self.files_paths:
            messagebox.showwarning("Empty", "Please add files before running the task.")
            return
            
        pw = None
        if hasattr(self, "password_entry"):
            pw = self.password_entry.get().strip()
            if not pw and self.mode_name in ["encrypted", "unlocked"]:
                messagebox.showwarning("Missing Info", "Please enter a password.")
                return

        out = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=self.get_smart_filename())
        if out:
            self.progress.pack(fill="x", pady=(0, 10), padx=40)
            self.progress.set(0.1) 
            task = PDFTask(self.files_paths, out, self.on_progress, self.on_done, mode=self.mode_name, password=pw)
            task.start()

    def on_progress(self, v): 
        self.progress.set(v)
    
    def on_done(self, res):
        self.progress.pack_forget()
        if res and "Error" in str(res):
            messagebox.showerror("Task Failed", res)
        else:
            for card in self.scroll.winfo_children():
                if hasattr(card, "mark_success"): card.mark_success()
            messagebox.showinfo("Success", "Operation completed successfully!")