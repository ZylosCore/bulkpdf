import customtkinter as ctk
from tkinter import filedialog, messagebox
import fitz
import os
from ..theme import (BG_COLOR, CARD_COLOR, BORDER_COLOR, TEXT_TITLE, FONT_FAMILY, TEXT_MAIN,
                     CORNER_RADIUS, BTN_PRIMARY, BTN_PRIMARY_HOVER, BTN_SUCCESS, BTN_SUCCESS_HOVER,
                     SIZE_TITLE, SIZE_MAIN, SIZE_SUBTITLE, CHECKBOX_KWARGS, TABVIEW_KWARGS)

class SecurityPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.pdf_path = None
        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkLabel(self, text="Security & Protection", font=(FONT_FAMILY, SIZE_TITLE, "bold"), text_color=TEXT_TITLE)
        header.grid(row=0, column=0, pady=(20, 10), padx=40, sticky="w")

        self.tabs = ctk.CTkTabview(self, **TABVIEW_KWARGS)
        self.tabs.grid(row=1, column=0, sticky="nsew", padx=40, pady=(0, 20))
        
        self.tabs.add("Protect PDF")
        self.tabs.add("Unlock PDF")

        self._build_protect_tab()
        self._build_unlock_tab()

    def _build_protect_tab(self):
        tab = self.tabs.tab("Protect PDF")
        tab.grid_columnconfigure(0, weight=1)

        file_frame = ctk.CTkFrame(tab, fg_color=CARD_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=CORNER_RADIUS)
        file_frame.pack(fill="x", pady=(10, 15), padx=20)
        self.prot_file_lbl = ctk.CTkLabel(file_frame, text="No file selected", font=(FONT_FAMILY, SIZE_MAIN), text_color=TEXT_MAIN)
        self.prot_file_lbl.pack(side="left", padx=15, pady=10)
        # MODIF: Reduced height
        btn_sel = ctk.CTkButton(file_frame, text="Select PDF", width=100, height=28, fg_color=BTN_PRIMARY, hover_color=BTN_PRIMARY_HOVER, font=(FONT_FAMILY, SIZE_MAIN, "bold"), command=lambda: self._select_file(self.prot_file_lbl))
        btn_sel.pack(side="right", padx=15)

        pw_frame = ctk.CTkFrame(tab, fg_color="transparent")
        pw_frame.pack(fill="x", pady=10, padx=20)
        ctk.CTkLabel(pw_frame, text="Set Password:", font=(FONT_FAMILY, SIZE_MAIN, "bold"), text_color=TEXT_TITLE).pack(anchor="w")
        # MODIF: Reduced height and width
        self.prot_pw = ctk.CTkEntry(pw_frame, show="*", width=200, height=30, corner_radius=CORNER_RADIUS, font=(FONT_FAMILY, SIZE_MAIN))
        self.prot_pw.pack(anchor="w", pady=5)

        perm_frame = ctk.CTkFrame(tab, fg_color="transparent")
        perm_frame.pack(fill="x", pady=15, padx=20)
        ctk.CTkLabel(perm_frame, text="Permissions:", font=(FONT_FAMILY, SIZE_MAIN, "bold"), text_color=TEXT_TITLE).pack(anchor="w", pady=(0, 10))
        
        self.allow_print = ctk.CTkCheckBox(perm_frame, text="Allow Printing", **CHECKBOX_KWARGS)
        self.allow_print.pack(anchor="w", pady=6)
        
        self.allow_copy = ctk.CTkCheckBox(perm_frame, text="Allow Copying Content", **CHECKBOX_KWARGS)
        self.allow_copy.pack(anchor="w", pady=6)

        # MODIF: Reduced height
        btn_run = ctk.CTkButton(tab, text="Encrypt and Save", width=160, height=30, text_color="#FFFFFF", fg_color=BTN_SUCCESS, hover_color=BTN_SUCCESS_HOVER, font=(FONT_FAMILY, SIZE_MAIN, "bold"), command=self._protect_pdf)
        btn_run.pack(pady=(30, 10))

    def _build_unlock_tab(self):
        tab = self.tabs.tab("Unlock PDF")
        tab.grid_columnconfigure(0, weight=1)

        file_frame = ctk.CTkFrame(tab, fg_color=CARD_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=CORNER_RADIUS)
        file_frame.pack(fill="x", pady=(10, 15), padx=20)
        self.unl_file_lbl = ctk.CTkLabel(file_frame, text="No file selected", font=(FONT_FAMILY, SIZE_MAIN), text_color=TEXT_MAIN)
        self.unl_file_lbl.pack(side="left", padx=15, pady=10)
        # MODIF: Reduced height
        btn_sel = ctk.CTkButton(file_frame, text="Select Locked PDF", width=130, height=28, fg_color=BTN_PRIMARY, hover_color=BTN_PRIMARY_HOVER, font=(FONT_FAMILY, SIZE_MAIN, "bold"), command=lambda: self._select_file(self.unl_file_lbl))
        btn_sel.pack(side="right", padx=15)

        pw_frame = ctk.CTkFrame(tab, fg_color="transparent")
        pw_frame.pack(fill="x", pady=10, padx=20)
        ctk.CTkLabel(pw_frame, text="Current Password (required):", font=(FONT_FAMILY, SIZE_MAIN, "bold"), text_color=TEXT_TITLE).pack(anchor="w")
        # MODIF: Reduced height
        self.unl_pw = ctk.CTkEntry(pw_frame, show="*", width=200, height=30, corner_radius=CORNER_RADIUS, font=(FONT_FAMILY, SIZE_MAIN))
        self.unl_pw.pack(anchor="w", pady=5)

        # MODIF: Reduced height
        btn_run = ctk.CTkButton(tab, text="Unlock and Save", width=160, height=30, text_color="#FFFFFF", fg_color=BTN_SUCCESS, hover_color=BTN_SUCCESS_HOVER, font=(FONT_FAMILY, SIZE_MAIN, "bold"), command=self._unlock_pdf)
        btn_run.pack(pady=(30, 10))

    def _select_file(self, label_widget):
        path = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if path:
            self.pdf_path = path
            label_widget.configure(text=os.path.basename(path))

    def _protect_pdf(self):
        if not self.pdf_path:
            messagebox.showwarning("Warning", "Select a PDF first.")
            return
        pw = self.prot_pw.get()
        if not pw:
            messagebox.showwarning("Warning", "Password cannot be empty.")
            return

        out = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile="Protected.pdf")
        if not out: return

        try:
            doc = fitz.open(self.pdf_path)
            perms = fitz.PDF_PERM_ACCESSIBILITY
            if self.allow_print.get(): perms |= fitz.PDF_PERM_PRINT
            if self.allow_copy.get(): perms |= fitz.PDF_PERM_COPY
            
            doc.save(out, encryption=fitz.PDF_ENCRYPT_AES_256, user_pw=pw, owner_pw=pw, permissions=perms)
            doc.close()
            messagebox.showinfo("Success", "PDF Protected Successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _unlock_pdf(self):
        if not self.pdf_path: return
        pw = self.unl_pw.get()
        try:
            doc = fitz.open(self.pdf_path)
            if doc.needs_pass:
                if not doc.authenticate(pw):
                    messagebox.showerror("Error", "Incorrect Password.")
                    return
            out = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile="Unlocked.pdf")
            if out:
                doc.save(out) 
                messagebox.showinfo("Success", "PDF Unlocked Successfully!")
            doc.close()
        except Exception as e:
            messagebox.showerror("Error", str(e))