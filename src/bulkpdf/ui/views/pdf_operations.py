import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from .cards import FileCard
from ...pdf_engine import PDFTask
from ..theme import BG_COLOR, BORDER_COLOR, TEXT_LOW, ACCENT_PURPLE, TEXT_TITLE, FONT_FAMILY

class PDFOperationsView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.files_paths = []
        
        # Titre normal et petit (16px)
        self.label = ctk.CTkLabel(self, text="Merge PDF Documents", 
                                 font=(FONT_FAMILY, 16, "bold"), 
                                 text_color=TEXT_TITLE)
        self.label.pack(pady=(0, 10), anchor="w")
        
        self.scroll = ctk.CTkScrollableFrame(self, fg_color=BG_COLOR, 
                                             border_width=1, border_color=BORDER_COLOR,
                                             corner_radius=10)
        self.scroll.pack(fill="both", expand=True)
        
        self.empty_label = ctk.CTkLabel(self.scroll, text="No files selected", 
                                       font=(FONT_FAMILY, 12), text_color=TEXT_LOW)
        self.empty_label.pack(pady=60)

        self.progress = ctk.CTkProgressBar(self, progress_color=ACCENT_PURPLE, height=6)
        self.progress.set(0)

        self.action_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.action_bar.pack(fill="x", pady=15)
        
        self.add_btn = ctk.CTkButton(self.action_bar, text="+ Add Files", 
                                    font=(FONT_FAMILY, 12, "bold"),
                                    fg_color=ACCENT_PURPLE, hover_color="#664dff",
                                    height=32, command=self.browse_files)
        self.add_btn.pack(side="left", padx=5)

        self.clear_btn = ctk.CTkButton(self.action_bar, text="Clear", 
                                      font=(FONT_FAMILY, 12),
                                      fg_color="transparent", border_width=1,
                                      border_color=BORDER_COLOR,
                                      text_color=TEXT_LOW,
                                      height=32, command=self.clear_list)
        self.clear_btn.pack(side="left", padx=5)

        self.run_btn = ctk.CTkButton(self.action_bar, text="Process Files", 
                                    fg_color=("#27ae60", "#2ecc71"), text_color="white", 
                                    font=(FONT_FAMILY, 12, "bold"), 
                                    height=32, command=self.execute_merge)
        self.run_btn.pack(side="right", padx=5)

    def browse_files(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
        if files:
            if self.empty_label.winfo_exists(): self.empty_label.pack_forget()
            for f in files:
                p = Path(f)
                if p not in self.files_paths:
                    self.files_paths.append(p)
                    FileCard(self.scroll, p, self.remove_file).pack(fill="x", padx=10, pady=4)

    def clear_list(self):
        for child in self.scroll.winfo_children():
            child.destroy()
        self.files_paths = []
        self.empty_label = ctk.CTkLabel(self.scroll, text="No files selected", 
                                       font=(FONT_FAMILY, 12), text_color=TEXT_LOW)
        self.empty_label.pack(pady=60)

    def remove_file(self, card):
        if card.file_path in self.files_paths:
            self.files_paths.remove(card.file_path)
        card.destroy()
        if not self.files_paths:
            self.clear_list()

    def execute_merge(self):
        if not self.files_paths: return
        out = filedialog.asksaveasfilename(defaultextension=".pdf")
        if out:
            self.progress.pack(fill="x", pady=10)
            task = PDFTask(self.files_paths, out, self.on_progress, self.on_done)
            task.start()

    def on_progress(self, v): self.progress.set(v)
    def on_done(self, res):
        self.progress.pack_forget()
        messagebox.showinfo("Success", "Files processed successfully!")
