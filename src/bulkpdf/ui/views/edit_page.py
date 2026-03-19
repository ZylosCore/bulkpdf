import customtkinter as ctk
import fitz  # PyMuPDF
from PIL import Image, ImageTk
from tkinter import Canvas, filedialog
import os

class EditPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.pdf_doc = None
        self.current_page_idx = 0
        self.tool_mode = "select"
        self.zoom_level = 1.5  # Zoom par défaut (150%)
        self.tk_img = None
        self.pdf_path = None
        
        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- BARRE D'OUTILS SUPÉRIEURE ---
        self.toolbar = ctk.CTkFrame(self, height=60)
        self.toolbar.grid(row=0, column=0, padx=20, pady=(10, 0), sticky="nsew")
        
        self.open_btn = ctk.CTkButton(self.toolbar, text="📁 Ouvrir", width=80, command=self._open_file_dialog)
        self.open_btn.pack(side="left", padx=10)

        tools = [("🖱️", "select"), ("🔤", "text"), ("🖊️", "draw"), ("🖍️", "highlight")]
        for icon, mode in tools:
            btn = ctk.CTkButton(self.toolbar, text=icon, width=45, height=45, fg_color="transparent",
                               command=lambda m=mode: self.set_tool(m))
            btn.pack(side="left", padx=2)

        self.save_btn = ctk.CTkButton(self.toolbar, text="💾 Enregistrer", fg_color="#2ecc71", width=100, command=self.save_changes)
        self.save_btn.pack(side="right", padx=10)

        # --- ZONE CENTRALE (CANVAS) ---
        self.view_container = ctk.CTkScrollableFrame(self, fg_color=("#d1d1d1", "#1a1a1a"))
        self.view_container.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        self.canvas = Canvas(self.view_container, bg="white", bd=0, highlightthickness=0)
        self.canvas.pack(pady=20)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)

        # --- BARRE DE NAVIGATION INFÉRIEURE ---
        self.nav_bar = ctk.CTkFrame(self, height=50, fg_color="transparent")
        self.nav_bar.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        # Sous-groupe Zoom
        self.zoom_frame = ctk.CTkFrame(self.nav_bar, fg_color="transparent")
        self.zoom_frame.pack(side="left", padx=20)
        ctk.CTkButton(self.zoom_frame, text="-", width=30, command=lambda: self.change_zoom(-0.2)).pack(side="left", padx=2)
        self.zoom_label = ctk.CTkLabel(self.zoom_frame, text="150%")
        self.zoom_label.pack(side="left", padx=5)
        ctk.CTkButton(self.zoom_frame, text="+", width=30, command=lambda: self.change_zoom(0.2)).pack(side="left", padx=2)

        # Sous-groupe Pages
        self.page_frame = ctk.CTkFrame(self.nav_bar, fg_color="transparent")
        self.page_frame.pack(side="right", padx=20)
        ctk.CTkButton(self.page_frame, text="◀", width=30, command=self.prev_page).pack(side="left", padx=2)
        self.page_label = ctk.CTkLabel(self.page_frame, text="Page 0 / 0")
        self.page_label.pack(side="left", padx=10)
        ctk.CTkButton(self.page_frame, text="▶", width=30, command=self.next_page).pack(side="left", padx=2)

    def _open_file_dialog(self):
        path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if path:
            self.pdf_path = path
            self.load_pdf(path)

    def load_pdf(self, path):
        self.pdf_doc = fitz.open(path)
        self.current_page_idx = 0
        self.update_page_display()

    def update_page_display(self):
        if not self.pdf_doc: return
        total_pages = len(self.pdf_doc)
        self.page_label.configure(text=f"Page {self.current_page_idx + 1} / {total_pages}")
        self.zoom_label.configure(text=f"{int(self.zoom_level * 100)}%")
        self.show_page(self.current_page_idx)

    def show_page(self, page_num):
        page = self.pdf_doc[page_num]
        # Recalcul de la matrice avec le niveau de zoom actuel
        mat = fitz.Matrix(self.zoom_level, self.zoom_level)
        pix = page.get_pixmap(matrix=mat)
        
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.tk_img = ImageTk.PhotoImage(img)
        
        self.canvas.delete("all")  # On vide le canvas avant de changer de page/zoom
        self.canvas.config(width=pix.width, height=pix.height)
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)

    def change_zoom(self, delta):
        new_zoom = self.zoom_level + delta
        if 0.5 <= new_zoom <= 4.0:  # Limites de zoom (50% à 400%)
            self.zoom_level = new_zoom
            self.update_page_display()

    def next_page(self):
        if self.pdf_doc and self.current_page_idx < len(self.pdf_doc) - 1:
            self.current_page_idx += 1
            self.update_page_display()

    def prev_page(self):
        if self.pdf_doc and self.current_page_idx > 0:
            self.current_page_idx -= 1
            self.update_page_display()

    # --- LOGIQUE D'ÉDITION ---
    def set_tool(self, mode):
        self.tool_mode = mode
        cursor_map = {"select": "arrow", "text": "xterm", "draw": "pencil", "highlight": "plus"}
        self.canvas.config(cursor=cursor_map.get(mode, "arrow"))

    def _on_click(self, event):
        if self.tool_mode == "text":
            text = ctk.CTkInputDialog(text="Texte :", title="Ajouter").get_input()
            if text:
                self.canvas.create_text(event.x, event.y, text=text, fill="red", font=("Arial", int(14 * self.zoom_level)), anchor="nw")
        elif self.tool_mode == "draw":
            self.last_x, self.last_y = event.x, event.y

    def _on_drag(self, event):
        if self.tool_mode == "draw":
            self.canvas.create_line(self.last_x, self.last_y, event.x, event.y, fill="black", width=2 * self.zoom_level)
            self.last_x, self.last_y = event.x, event.y

    def save_changes(self):
        # On garde ça pour la fin, c'est le "Final Boss"
        print("Sauvegarde en cours de préparation...")