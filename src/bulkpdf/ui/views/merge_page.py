import customtkinter as ctk
import fitz  # PyMuPDF
from tkinter import filedialog, messagebox
import os
from ..i18n import t

class MergePage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.pdf_list = []
        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkLabel(self, text=t("merge_title"), font=("Arial", 24, "bold"))
        header.grid(row=0, column=0, pady=(20, 10), padx=20, sticky="w")

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color=("#ebebeb", "#1a1a1a"))
        self.list_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        
        self.files_label = ctk.CTkLabel(self.list_frame, text=t("no_file_selected"), text_color="gray")
        self.files_label.pack(pady=50)

        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=20)
        
        btn_add = ctk.CTkButton(action_frame, text=t("btn_add_pdf"), command=self._add_pdfs)
        btn_add.pack(side="left", padx=5)
        
        btn_clear = ctk.CTkButton(action_frame, text=t("btn_clear_list"), fg_color="#e74c3c", hover_color="#c0392b", command=self._clear_list)
        btn_clear.pack(side="left", padx=5)

        btn_merge = ctk.CTkButton(action_frame, text=t("btn_merge_save"), fg_color="#2ecc71", hover_color="#27ae60", command=self._merge_pdfs)
        btn_merge.pack(side="right", padx=5)

    def _add_pdfs(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF", "*.pdf")])
        if files:
            if not self.pdf_list:
                self.files_label.pack_forget()
            for file in files:
                if file not in self.pdf_list:
                    self.pdf_list.append(file)
                    lbl = ctk.CTkLabel(self.list_frame, text=f"📄 {os.path.basename(file)}", anchor="w")
                    lbl.pack(fill="x", pady=2, padx=10)

    def _clear_list(self):
        self.pdf_list.clear()
        for widget in self.list_frame.winfo_children():
            widget.pack_forget()
        self.files_label.pack(pady=50)

    def _merge_pdfs(self):
        if len(self.pdf_list) < 2:
            messagebox.showwarning(t("warning"), t("merge_min_files"))
            return

        save_path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile="PDF_Merged.pdf", filetypes=[("PDF", "*.pdf")])
        if not save_path: return

        try:
            merged_doc = fitz.open()
            for pdf_path in self.pdf_list:
                with fitz.open(pdf_path) as doc:
                    merged_doc.insert_pdf(doc)
            
            merged_doc.save(save_path)
            merged_doc.close()
            messagebox.showinfo(t("success"), t("merge_success"))
            self._clear_list()
        except Exception as e:
            messagebox.showerror(t("error"), str(e))