import customtkinter as ctk
import fitz  
from tkinter import filedialog, messagebox
import os
import zipfile
from ..i18n import t
from ..theme import (BG_COLOR, CARD_COLOR, BORDER_COLOR, TEXT_TITLE, FONT_FAMILY, TEXT_LOW,
                     CORNER_RADIUS, BTN_PRIMARY, BTN_PRIMARY_HOVER, 
                     BTN_SUCCESS, BTN_SUCCESS_HOVER, SIZE_TITLE, SIZE_MAIN, TEXT_MAIN, TABVIEW_KWARGS)

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

        header = ctk.CTkLabel(self, text="Split & Extract PDF", font=(FONT_FAMILY, SIZE_TITLE, "bold"), text_color=TEXT_TITLE)
        header.grid(row=0, column=0, pady=(20, 10), padx=40, sticky="w")

        self.tabs = ctk.CTkTabview(self, **TABVIEW_KWARGS)
        self.tabs.grid(row=1, column=0, sticky="nsew", padx=40, pady=(0, 20))
        
        self.tabs.add("Extract Ranges")
        self.tabs.add("Split PDF")

        self._build_header_info()
        self._build_extract_tab()
        self._build_split_tab()

    def _build_header_info(self):
        file_frame = ctk.CTkFrame(self, fg_color="transparent")
        file_frame.grid(row=0, column=0, sticky="e", padx=40, pady=(20, 10))
        
        self.file_label = ctk.CTkLabel(file_frame, text="No PDF loaded", text_color=TEXT_LOW, font=(FONT_FAMILY, SIZE_MAIN))
        self.file_label.pack(side="left", padx=15)
        
        # MODIF: Reduced height
        btn_select = ctk.CTkButton(
            file_frame, text="Browse File", width=100, height=28, corner_radius=CORNER_RADIUS,
            font=(FONT_FAMILY, SIZE_MAIN, "bold"), fg_color=BTN_PRIMARY, hover_color=BTN_PRIMARY_HOVER,
            command=self._select_pdf
        )
        btn_select.pack(side="right")

    def _build_extract_tab(self):
        tab = self.tabs.tab("Extract Ranges")
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="Pages to extract (e.g., 1, 3, 5-10):", font=(FONT_FAMILY, SIZE_MAIN, "bold"), text_color=TEXT_TITLE).pack(anchor="w", pady=(20, 5), padx=20)
        # MODIF: Reduced entry box size
        self.entry_ranges = ctk.CTkEntry(tab, placeholder_text="1-5, 8, 11-13", width=250, height=30, corner_radius=CORNER_RADIUS, font=(FONT_FAMILY, SIZE_MAIN))
        self.entry_ranges.pack(anchor="w", padx=20)

        ctk.CTkLabel(tab, text="Format:", font=(FONT_FAMILY, SIZE_MAIN, "bold"), text_color=TEXT_TITLE).pack(anchor="w", pady=(20, 5), padx=20)
        ctk.CTkRadioButton(tab, text="Save as single PDF", variable=self.output_mode, value="pdf", font=(FONT_FAMILY, SIZE_MAIN)).pack(anchor="w", padx=20, pady=5)
        ctk.CTkRadioButton(tab, text="Save as ZIP (Individual pages)", variable=self.output_mode, value="zip", font=(FONT_FAMILY, SIZE_MAIN)).pack(anchor="w", padx=20, pady=5)

        # MODIF: Reduced button size
        btn_run = ctk.CTkButton(tab, text="Extract Pages", width=150, height=30, text_color="#FFFFFF", fg_color=BTN_SUCCESS, hover_color=BTN_SUCCESS_HOVER, font=(FONT_FAMILY, SIZE_MAIN, "bold"), command=self._extract_custom)
        btn_run.pack(pady=(30, 10))

    def _build_split_tab(self):
        tab = self.tabs.tab("Split PDF")
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="Split document into multiple files", font=(FONT_FAMILY, SIZE_MAIN, "bold"), text_color=TEXT_TITLE).pack(anchor="w", pady=(20, 5), padx=20)
        
        split_opts = ctk.CTkFrame(tab, fg_color="transparent")
        split_opts.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(split_opts, text="Split every", font=(FONT_FAMILY, SIZE_MAIN), text_color=TEXT_MAIN).pack(side="left")
        self.split_every_entry = ctk.CTkEntry(split_opts, width=50, height=28, justify="center", font=(FONT_FAMILY, SIZE_MAIN))
        self.split_every_entry.insert(0, "1")
        self.split_every_entry.pack(side="left", padx=15)
        ctk.CTkLabel(split_opts, text="pages.", font=(FONT_FAMILY, SIZE_MAIN), text_color=TEXT_MAIN).pack(side="left")

        # MODIF: Reduced button size
        btn_run = ctk.CTkButton(tab, text="Split Document", width=150, height=30, text_color="#FFFFFF", fg_color=BTN_SUCCESS, hover_color=BTN_SUCCESS_HOVER, font=(FONT_FAMILY, SIZE_MAIN, "bold"), command=self._split_pdf)
        btn_run.pack(pady=(30, 10))

    def _select_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if path:
            try:
                doc = fitz.open(path)
                self.total_pages = len(doc)
                doc.close()
                self.pdf_path = path
                self.file_label.configure(text=f"📄 {os.path.basename(path)} ({self.total_pages} pages)")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _parse_ranges(self, text):
        pages = set()
        for part in text.split(','):
            part = part.strip()
            if not part: continue
            if '-' in part:
                start, end = part.split('-')
                pages.update(range(int(start)-1, int(end)))
            else:
                pages.add(int(part)-1)
        return sorted(list(pages))

    def _extract_custom(self):
        if not self.pdf_path: return
        try:
            pages_to_extract = self._parse_ranges(self.entry_ranges.get())
            if not pages_to_extract: raise ValueError("Invalid range.")
        except Exception:
            messagebox.showwarning("Warning", "Invalid format. Use something like: 1, 3-5")
            return

        mode = self.output_mode.get()
        if mode == "pdf":
            out = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile="Extracted.pdf")
            if out:
                doc = fitz.open(self.pdf_path)
                new_doc = fitz.open()
                for p in pages_to_extract:
                    if 0 <= p < self.total_pages:
                        new_doc.insert_pdf(doc, from_page=p, to_page=p)
                new_doc.save(out)
                new_doc.close(); doc.close()
                messagebox.showinfo("Success", "Pages extracted successfully!")
        else:
            out = filedialog.asksaveasfilename(defaultextension=".zip", initialfile="Pages.zip")
            if out:
                doc = fitz.open(self.pdf_path)
                with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for p in pages_to_extract:
                        if 0 <= p < self.total_pages:
                            new_doc = fitz.open()
                            new_doc.insert_pdf(doc, from_page=p, to_page=p)
                            zf.writestr(f"Page_{p+1}.pdf", new_doc.tobytes())
                            new_doc.close()
                doc.close()
                messagebox.showinfo("Success", "ZIP created successfully!")

    def _split_pdf(self):
        if not self.pdf_path: return
        try:
            step = int(self.split_every_entry.get())
            if step < 1: raise ValueError
        except:
            messagebox.showwarning("Warning", "Please enter a valid positive number.")
            return

        out_dir = filedialog.askdirectory(title="Select Output Folder")
        if not out_dir: return

        try:
            doc = fitz.open(self.pdf_path)
            base_name = os.path.splitext(os.path.basename(self.pdf_path))[0]
            
            for start in range(0, self.total_pages, step):
                end = min(start + step - 1, self.total_pages - 1)
                new_doc = fitz.open()
                new_doc.insert_pdf(doc, from_page=start, to_page=end)
                new_doc.save(os.path.join(out_dir, f"{base_name}_{start+1}-{end+1}.pdf"))
                new_doc.close()
            
            doc.close()
            messagebox.showinfo("Success", "Document split successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))