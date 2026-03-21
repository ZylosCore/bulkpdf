import customtkinter as ctk
import fitz 
from tkinter import filedialog, messagebox
import os
from ..i18n import t
from ..theme import (BG_COLOR, BORDER_COLOR, TEXT_TITLE, FONT_FAMILY, TEXT_LOW,
                     CORNER_RADIUS, BTN_PRIMARY, BTN_PRIMARY_HOVER, 
                     BTN_SUCCESS, BTN_SUCCESS_HOVER, BTN_SECONDARY, BTN_SECONDARY_HOVER,
                     SCROLLBAR_COLOR, SCROLLBAR_HOVER, SIZE_TITLE, SIZE_MAIN)

class MergePage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.pdf_list = []
        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Titre réduit avec SIZE_TITLE
        header = ctk.CTkLabel(self, text=t("merge_title"), font=(FONT_FAMILY, SIZE_TITLE, "bold"), text_color=TEXT_TITLE)
        header.grid(row=0, column=0, pady=(15, 10), padx=20, sticky="w")

        self.list_frame = ctk.CTkScrollableFrame(
            self, fg_color=BG_COLOR, border_width=1, border_color=BORDER_COLOR,
            corner_radius=CORNER_RADIUS, scrollbar_button_color=SCROLLBAR_COLOR,
            scrollbar_button_hover_color=SCROLLBAR_HOVER
        )
        self.list_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=0)
        
        # Texte vide réduit (SIZE_MAIN)
        self.files_label = ctk.CTkLabel(self.list_frame, text=t("no_file_selected"), text_color=TEXT_LOW, font=(FONT_FAMILY, SIZE_MAIN))
        self.files_label.pack(pady=60)

        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=15)
        
        # Boutons : Police SIZE_MAIN, hauteur 30
        btn_add = ctk.CTkButton(
            action_frame, text=t("btn_add_pdf"), 
            width=120, height=30, corner_radius=CORNER_RADIUS,
            font=(FONT_FAMILY, SIZE_MAIN, "bold"), fg_color=BTN_PRIMARY, hover_color=BTN_PRIMARY_HOVER,
            command=self._add_pdfs
        )
        btn_add.pack(side="left", padx=(0, 10))
        
        btn_clear = ctk.CTkButton(
            action_frame, text=t("btn_clear_list"), 
            width=120, height=30, corner_radius=CORNER_RADIUS,
            font=(FONT_FAMILY, SIZE_MAIN), text_color=TEXT_TITLE,
            fg_color=BTN_SECONDARY, hover_color=BTN_SECONDARY_HOVER, command=self._clear_list
        )
        btn_clear.pack(side="left")

        btn_merge = ctk.CTkButton(
            action_frame, text=t("btn_merge_save"), 
            width=130, height=30, corner_radius=CORNER_RADIUS,
            font=(FONT_FAMILY, SIZE_MAIN, "bold"), fg_color=BTN_SUCCESS, hover_color=BTN_SUCCESS_HOVER, 
            command=self._merge_pdfs
        )
        btn_merge.pack(side="right")

    def _add_pdfs(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF", "*.pdf")])
        if files:
            if not self.pdf_list:
                self.files_label.pack_forget()
            for file in files:
                if file not in self.pdf_list:
                    self.pdf_list.append(file)
                    # Textes dans la liste réduits (SIZE_MAIN)
                    lbl = ctk.CTkLabel(self.list_frame, text=f"📄 {os.path.basename(file)}", font=(FONT_FAMILY, SIZE_MAIN), anchor="w")
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