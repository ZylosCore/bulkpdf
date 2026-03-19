import customtkinter as ctk
import fitz
from PIL import Image, ImageTk
from tkinter import Canvas, filedialog, colorchooser
import os
import sys

class EditPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.pdf_doc = None
        self.current_page_idx = 0
        self.zoom_level = 1.3
        self.tool_mode = "select"
        self.selected_item = None
        self.active_entry = None
        self.drag_data = {"x": 0, "y": 0, "item": None}
        
        # Styles par défaut
        self.current_font_size = 14
        self.current_color = "#2c3e50" 
        
        self._setup_ui()

    def _get_edit_icon(self, name, size=(22, 22)):
        """Charge une icône depuis le dossier assets/edit/"""
        try:
            # Déterminer le chemin de base
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            icon_path = os.path.join(base_path, "assets", "edit", f"{name}.png")
            
            if os.path.exists(icon_path):
                img = Image.open(icon_path)
                return ctk.CTkImage(light_image=img, dark_image=img, size=size)
            return None
        except Exception as e:
            print(f"Erreur icône {name}: {e}")
            return None

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- LE RUBAN COMPACT (STYLE WORD SLIM) ---
        self.ribbon = ctk.CTkFrame(self, height=85, fg_color=("#ffffff", "#2b2b2b"), corner_radius=0)
        self.ribbon.grid(row=0, column=0, sticky="nsew")
        
        # Section 1 : DOC
        self.file_group = self._create_ribbon_group("DOC")
        self._create_btn(self.file_group, "open", "Ouvrir", self._open_file_dialog)
        self._create_btn(self.file_group, "save", "Sauver", self.save_changes, is_accent=True)

        self._add_separator(self.ribbon)

        # Section 2 : OUTILS
        self.tools_group = self._create_ribbon_group("OUTILS")
        self.tool_btns = {}
        tool_configs = [
            ("cursor", "select", "Sélect."),
            ("text", "text", "Texte"),
            ("draw", "draw", "Dessin")
        ]
        for icon_name, mode, lbl in tool_configs:
            btn = self._create_btn(self.tools_group, icon_name, lbl, lambda m=mode: self.set_tool(m))
            self.tool_btns[mode] = btn

        self._add_separator(self.ribbon)

        # Section 3 : FORMAT (TEXTE)
        self.font_group = self._create_ribbon_group("FORMAT")
        self.text_controls = ctk.CTkFrame(self.font_group, fg_color="transparent")
        self.text_controls.pack(side="left", padx=5)

        self.size_menu = ctk.CTkComboBox(self.text_controls, values=["12", "14", "16", "20", "24", "32"], 
                                        width=70, height=24, font=("Arial", 11), command=self._update_font_settings)
        self.size_menu.set("14")
        self.size_menu.pack(pady=2)
        
        self.color_preview = ctk.CTkButton(self.text_controls, text="Couleur", width=70, height=24, 
                                          font=("Arial", 10), fg_color=self.current_color, command=self._choose_color)
        self.color_preview.pack(pady=2)

        # --- ZONE DE TRAVAIL ---
        self.view_container = ctk.CTkScrollableFrame(self, fg_color=("#f0f0f0", "#1a1a1a"))
        self.view_container.grid(row=1, column=0, sticky="nsew")
        
        self.canvas = Canvas(self.view_container, bg="white", bd=0, highlightthickness=0)
        self.canvas.pack(pady=20)
        
        # Bindings
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)

        # --- BARRE DE STATUS ---
        self._setup_status_bar()

    def _setup_status_bar(self):
        self.status_bar = ctk.CTkFrame(self, height=28, fg_color=("#e0e0e0", "#202020"), corner_radius=0)
        self.status_bar.grid(row=2, column=0, sticky="ew")
        
        self.page_info = ctk.CTkLabel(self.status_bar, text="Prêt", font=("Arial", 10))
        self.page_info.pack(side="left", padx=15)
        
        self.zoom_info = ctk.CTkLabel(self.status_bar, text="130%", font=("Arial", 10))
        self.zoom_info.pack(side="right", padx=10)
        
        # Utilisation des icônes plus/minus pour le zoom
        plus_icon = self._get_edit_icon("plus", size=(12, 12))
        minus_icon = self._get_edit_icon("minus", size=(12, 12))
        
        ctk.CTkButton(self.status_bar, text="", image=plus_icon, width=28, height=20, 
                      fg_color="transparent", hover_color="#d0d0d0", 
                      command=lambda: self._change_zoom(0.1)).pack(side="right", padx=2)
        ctk.CTkButton(self.status_bar, text="", image=minus_icon, width=28, height=20, 
                      fg_color="transparent", hover_color="#d0d0d0", 
                      command=lambda: self._change_zoom(-0.1)).pack(side="right", padx=2)

    def _create_ribbon_group(self, label_text):
        group = ctk.CTkFrame(self.ribbon, fg_color="transparent")
        group.pack(side="left", padx=10, pady=2, fill="y")
        lbl = ctk.CTkLabel(group, text=label_text, font=("Segoe UI", 9, "bold"), text_color="gray")
        lbl.pack(side="bottom")
        return group

    def _create_btn(self, parent, icon_name, label, command, is_accent=False):
        icon_img = self._get_edit_icon(icon_name)
        bg_color = "#2ecc71" if is_accent else "transparent"
        
        btn = ctk.CTkButton(parent, text=label, image=icon_img, compound="top",
                            width=60, height=55, font=("Segoe UI", 10), 
                            fg_color=bg_color, 
                            text_color=("#1a1a1a", "#ffffff") if not is_accent else "white",
                            hover_color=("#e5e5e5", "#3d3d3d") if not is_accent else "#27ae60", 
                            command=command)
        btn.pack(side="left", padx=2)
        return btn

    def _add_separator(self, parent):
        sep = ctk.CTkFrame(parent, width=1, fg_color=("#d0d0d0", "#404040"))
        sep.pack(side="left", fill="y", padx=5, pady=12)

    # --- LOGIQUE D'INTERACTION ---
    def set_tool(self, mode):
        self.tool_mode = mode
        for m, btn in self.tool_btns.items():
            is_active = (m == mode)
            btn.configure(fg_color=("#d0d0d0", "#454545") if is_active else "transparent")
        
        cursor = "xterm" if mode == "text" else "pencil" if mode == "draw" else "arrow"
        self.canvas.config(cursor=cursor)

    def _on_click(self, event):
        if self.active_entry: self._finalize_text()
        if self.tool_mode == "text":
            self._create_inline_edit(event.x, event.y)
        elif self.tool_mode == "select":
            item = self.canvas.find_closest(event.x, event.y)
            if "draggable" in self.canvas.gettags(item):
                self.selected_item = item
                self.drag_data = {"x": event.x, "y": event.y, "item": item}
        elif self.tool_mode == "draw":
            self.last_x, self.last_y = event.x, event.y

    def _on_drag(self, event):
        if self.tool_mode == "select" and self.drag_data["item"]:
            dx, dy = event.x - self.drag_data["x"], event.y - self.drag_data["y"]
            self.canvas.move(self.drag_data["item"], dx, dy)
            self.drag_data["x"], self.drag_data["y"] = event.x, event.y
        elif self.tool_mode == "draw":
            self.canvas.create_line(self.last_x, self.last_y, event.x, event.y, 
                                   fill=self.current_color, width=2, capstyle="round",
                                   smooth=True, tags=("draggable",))
            self.last_x, self.last_y = event.x, event.y

    def _on_release(self, event):
        self.drag_data["item"] = None

    def _create_inline_edit(self, x, y, old_text=""):
        self.active_entry = ctk.CTkEntry(self.canvas, font=("Arial", int(self.current_font_size * self.zoom_level)),
                                        width=150, fg_color="white", text_color=self.current_color)
        self.active_entry.place(x=x, y=y)
        self.active_entry.insert(0, old_text)
        self.active_entry.focus_set()
        self.active_entry.bind("<Return>", lambda e: self._finalize_text())

    def _finalize_text(self):
        if not self.active_entry: return
        txt = self.active_entry.get()
        if txt.strip():
            self.canvas.create_text(self.active_entry.winfo_x(), self.active_entry.winfo_y(), 
                                   text=txt, fill=self.current_color, anchor="nw",
                                   font=("Arial", int(self.current_font_size * self.zoom_level)), 
                                   tags=("draggable", "text_obj"))
        self.active_entry.destroy()
        self.active_entry = None

    def _on_double_click(self, event):
        item = self.canvas.find_closest(event.x, event.y)
        if "text_obj" in self.canvas.gettags(item):
            t, c = self.canvas.itemcget(item, "text"), self.canvas.coords(item)
            self.canvas.delete(item)
            self._create_inline_edit(c[0], c[1], t)

    def _choose_color(self):
        c = colorchooser.askcolor(color=self.current_color, title="Palette de couleurs")[1]
        if c: 
            self.current_color = c
            self.color_preview.configure(fg_color=c)

    def _update_font_settings(self, s):
        self.current_font_size = int(s)

    def _open_file_dialog(self):
        p = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if p:
            self.pdf_doc = fitz.open(p)
            self.current_page_idx = 0
            self._show_page(0)

    def _show_page(self, n):
        if not self.pdf_doc: return
        page = self.pdf_doc[n]
        pix = page.get_pixmap(matrix=fitz.Matrix(self.zoom_level, self.zoom_level))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.tk_img = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.config(width=pix.width, height=pix.height)
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
        self.page_info.configure(text=f"Page {n+1} / {len(self.pdf_doc)}")

    def _change_zoom(self, d):
        self.zoom_level = max(0.5, min(3.0, self.zoom_level + d))
        self.zoom_info.configure(text=f"{int(self.zoom_level*100)}%")
        if self.pdf_doc: self._show_page(self.current_page_idx)

    def save_changes(self):
        print("Exportation en cours avec le moteur PyMuPDF...")