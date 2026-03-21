import customtkinter as ctk
import fitz  
from tkinter import filedialog, messagebox
import os
import zipfile
from ..i18n import t
from ..theme import (BG_COLOR, CARD_COLOR, BORDER_COLOR, TEXT_TITLE, FONT_FAMILY, TEXT_LOW,
                     CORNER_RADIUS, BTN_PRIMARY, BTN_PRIMARY_HOVER, 
                     BTN_SUCCESS, BTN_SUCCESS_HOVER, SCROLLBAR_COLOR, SCROLLBAR_HOVER, 
                     SIZE_TITLE, SIZE_MAIN, TEXT_MAIN)

class ExtractPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.pdf_path = None
        self.total_pages = 0
        self.output_mode = ctk.StringVar(value="pdf") 
        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkLabel(self, text=t("extract_title"), font=(FONT_FAMILY, SIZE_TITLE, "bold"), text_color=TEXT_TITLE)
        header.grid(row=0, column=0, pady=(20, 10), padx=20, sticky="w")

        self.main_scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=SCROLLBAR_COLOR,
            scrollbar_button_hover_color=SCROLLBAR_HOVER
        )
        self.main_scroll.grid(row=1, column=0, sticky="nsew", padx=20)
        self.main_scroll.grid_columnconfigure(0, weight=1)

        # CARTE 1 : Fichier
        card_file = ctk.CTkFrame(self.main_scroll, fg_color=CARD_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=CORNER_RADIUS)
        card_file.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        card_file.grid_columnconfigure(0, weight=1)

        self.file_label = ctk.CTkLabel(card_file, text=t("extract_no_file"), font=(FONT_FAMILY, SIZE_MAIN, "bold"), text_color=TEXT_MAIN)
        self.file_label.grid(row=0, column=0, pady=(20, 5))

        self.info_label = ctk.CTkLabel(card_file, text="", text_color=TEXT_LOW, font=(FONT_FAMILY, SIZE_MAIN))
        self.info_label.grid(row=1, column=0, pady=(0, 15))

        btn_select = ctk.CTkButton(
            card_file, text=t("btn_choose_pdf"), width=150, height=32, corner_radius=CORNER_RADIUS,
            font=(FONT_FAMILY, SIZE_MAIN, "bold"), fg_color=BTN_PRIMARY, hover_color=BTN_PRIMARY_HOVER,
            command=self._select_pdf
        )
        btn_select.grid(row=2, column=0, pady=(0, 20))

        # CARTE 2 : Paramètres
        self.card_options = ctk.CTkFrame(self.main_scroll, fg_color=CARD_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=CORNER_RADIUS)
        self.card_options.grid(row=1, column=0, sticky="ew", pady=0)
        self.card_options.grid_columnconfigure(0, weight=1)
        
        range_frame = ctk.CTkFrame(self.card_options, fg_color="transparent")
        range_frame.pack(pady=(20, 15))

        ctk.CTkLabel(range_frame, text=t("extract_from"), font=(FONT_FAMILY, SIZE_MAIN), text_color=TEXT_MAIN).grid(row=0, column=0, padx=5)
        self.entry_start = ctk.CTkEntry(range_frame, width=60, height=28, corner_radius=CORNER_RADIUS, border_color=BORDER_COLOR, justify="center")
        self.entry_start.grid(row=0, column=1, padx=5)
        
        ctk.CTkLabel(range_frame, text=t("extract_to"), font=(FONT_FAMILY, SIZE_MAIN), text_color=TEXT_MAIN).grid(row=0, column=2, padx=5)
        self.entry_end = ctk.CTkEntry(range_frame, width=60, height=28, corner_radius=CORNER_RADIUS, border_color=BORDER_COLOR, justify="center")
        self.entry_end.grid(row=0, column=3, padx=5)

        mode_frame = ctk.CTkFrame(self.card_options, fg_color="transparent")
        mode_frame.pack(pady=(0, 20))

        ctk.CTkLabel(mode_frame, text=t("extract_format"), font=(FONT_FAMILY, SIZE_MAIN, "bold"), text_color=TEXT_MAIN).pack(anchor="w", pady=(0, 10))
        ctk.CTkRadioButton(mode_frame, text=t("format_pdf"), variable=self.output_mode, value="pdf", font=(FONT_FAMILY, SIZE_MAIN)).pack(anchor="w", pady=5)
        ctk.CTkRadioButton(mode_frame, text=t("format_zip"), variable=self.output_mode, value="zip", font=(FONT_FAMILY, SIZE_MAIN)).pack(anchor="w", pady=5)

        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=20)
        action_frame.grid_columnconfigure(0, weight=1)

        self.btn_extract = ctk.CTkButton(
            action_frame, text=t("btn_extract_save"), 
            fg_color=BTN_SUCCESS, hover_color=BTN_SUCCESS_HOVER, 
            width=200, height=36, corner_radius=CORNER_RADIUS, font=(FONT_FAMILY, SIZE_MAIN, "bold"),
            state="disabled", command=self._extract_pdf
        )
        self.btn_extract.grid(row=0, column=0)

    def _select_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if path:
            try:
                doc = fitz.open(path)
                self.total_pages = len(doc)
                doc.close()
                self.pdf_path = path
                self.file_label.configure(text=f"📄 {os.path.basename(path)}")
                self.info_label.configure(text=t("extract_ready").format(self.total_pages))
                self.entry_start.delete(0, 'end'); self.entry_start.insert(0, "1")
                self.entry_end.delete(0, 'end'); self.entry_end.insert(0, str(self.total_pages))
                self.btn_extract.configure(state="normal")
            except Exception as e:
                messagebox.showerror(t("error"), str(e))

    def _extract_pdf(self):
        if not self.pdf_path: return

        try:
            start_page = int(self.entry_start.get())
            end_page = int(self.entry_end.get())
        except ValueError:
            messagebox.showwarning(t("warning"), t("extract_err_num"))
            return
            
        if start_page < 1 or end_page > self.total_pages or start_page > end_page:
            messagebox.showwarning(t("warning"), t("extract_err_range").format(self.total_pages))
            return

        mode = self.output_mode.get()
        original_name = os.path.splitext(os.path.basename(self.pdf_path))[0]

        if mode == "pdf":
            save_path = filedialog.asksaveasfilename(initialfile=f"{original_name}_extrait.pdf", defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
            if not save_path: return
            try:
                doc = fitz.open(self.pdf_path)
                new_doc = fitz.open() 
                new_doc.insert_pdf(doc, from_page=start_page - 1, to_page=end_page - 1)
                new_doc.save(save_path)
                new_doc.close(); doc.close()
                messagebox.showinfo(t("success"), t("extract_success_pdf"))
            except Exception as e:
                messagebox.showerror(t("error"), str(e))

        elif mode == "zip":
            save_path = filedialog.asksaveasfilename(initialfile=f"{original_name}_pages.zip", defaultextension=".zip", filetypes=[("ZIP", "*.zip")])
            if not save_path: return
            try:
                doc = fitz.open(self.pdf_path)
                with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for i in range(start_page - 1, end_page):
                        new_doc = fitz.open()
                        new_doc.insert_pdf(doc, from_page=i, to_page=i)
                        zf.writestr(f"{original_name}_Page_{i+1}.pdf", new_doc.tobytes())
                        new_doc.close()
                doc.close()
                messagebox.showinfo(t("success"), t("extract_success_zip"))
            except Exception as e:
                messagebox.showerror(t("error"), str(e))