import customtkinter as ctk
import fitz
from PIL import Image, ImageTk, ImageOps
from tkinter import Canvas, filedialog, colorchooser
import os

class EditPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # État du document
        self.pdf_doc = None
        self.current_page_idx = 0
        self.zoom_level = 1.3
        
        # État des outils
        self.tool_mode = "select"
        self.selected_item = None
        self.active_entry = None
        self.drag_data = {"x": 0, "y": 0, "item": None}
        self.current_font_size = 14
        self.current_color = "#2c3e50" 
        
        self._setup_ui()
        self._setup_bindings()

    def _get_edit_icon(self, name, size=(18, 18)):
        """Charge l'icône et génère une version blanche pour le mode sombre"""
        try:
            # Ajustez le chemin selon votre structure de dossier
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            icon_path = os.path.join(base_path, "assets", "edit", f"{name}.png")
            
            if os.path.exists(icon_path):
                img_light = Image.open(icon_path).convert("RGBA")
                
                # Création de la version sombre (inversion de luminosité ou passage en blanc)
                r, g, b, a = img_light.split()
                img_dark = Image.merge("RGBA", (
                    r.point(lambda _: 255), 
                    g.point(lambda _: 255), 
                    b.point(lambda _: 255), 
                    a
                ))
                
                return ctk.CTkImage(light_image=img_light, dark_image=img_dark, size=size)
            return None
        except Exception as e:
            print(f"Erreur icône {name}: {e}")
            return None

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- TOOLBAR ---
        self.toolbar = ctk.CTkFrame(self, height=45, fg_color=("#ffffff", "#2b2b2b"), corner_radius=0)
        self.toolbar.grid(row=0, column=0, sticky="ew")
        self.toolbar.grid_propagate(False)

        container = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        container.pack(side="left", padx=10, fill="y")

        # Fichier
        self._create_btn(container, "open", self._open_file_dialog)
        self._create_btn(container, "save", self.save_changes, is_accent=True)
        self._add_sep(container)

        # Outils
        self.tool_btns = {}
        for icon, mode in [("cursor", "select"), ("text", "text"), ("draw", "draw")]:
            btn = self._create_btn(container, icon, lambda m=mode: self.set_tool(m))
            self.tool_btns[mode] = btn
        
        self._add_sep(container)

        # Format
        self.size_menu = ctk.CTkComboBox(container, values=["12", "14", "18", "24", "32"], width=65, height=28, command=self._update_font_settings)
        self.size_menu.set("14")
        self.size_menu.pack(side="left", padx=5)
        
        self.color_btn = ctk.CTkButton(container, text="", width=24, height=24, fg_color=self.current_color, command=self._choose_color, corner_radius=12, border_width=1, border_color="gray")
        self.color_btn.pack(side="left", padx=5)

        # --- ZONE CENTRALE ---
        self.scroll_canvas = ctk.CTkScrollableFrame(self, fg_color=("#ebebeb", "#1a1a1a"), corner_radius=0)
        self.scroll_canvas.grid(row=1, column=0, sticky="nsew")
        
        self.canvas = Canvas(self.scroll_canvas, bg="white", bd=0, highlightthickness=0)
        self.canvas.pack(pady=20)

        # --- STATUS BAR ---
        self.status_bar = ctk.CTkFrame(self, height=30, fg_color=("#dbdbdb", "#252525"), corner_radius=0)
        self.status_bar.grid(row=2, column=0, sticky="ew")

        nav_cnt = ctk.CTkFrame(self.status_bar, fg_color="transparent")
        nav_cnt.pack(side="left", padx=20)
        
        ctk.CTkButton(nav_cnt, text="<", width=30, command=lambda: self._navigate(-1)).pack(side="left", padx=2)
        self.page_label = ctk.CTkLabel(nav_cnt, text="Page 0 / 0", font=("Arial", 11, "bold"))
        self.page_label.pack(side="left", padx=10)
        ctk.CTkButton(nav_cnt, text=">", width=30, command=lambda: self._navigate(1)).pack(side="left", padx=2)

        zoom_cnt = ctk.CTkFrame(self.status_bar, fg_color="transparent")
        zoom_cnt.pack(side="right", padx=20)
        
        ctk.CTkButton(zoom_cnt, text="-", width=30, command=lambda: self._change_zoom(-0.1)).pack(side="left")
        self.zoom_label = ctk.CTkLabel(zoom_cnt, text="130%", width=50)
        self.zoom_label.pack(side="left")
        ctk.CTkButton(zoom_cnt, text="+", width=30, command=lambda: self._change_zoom(0.1)).pack(side="left")

    def _setup_bindings(self):
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.master.bind("<Delete>", self._delete_selected)
        self.master.bind("<Control-plus>", lambda e: self._change_zoom(0.1))
        self.master.bind("<Control-minus>", lambda e: self._change_zoom(-0.1))

    def _create_btn(self, parent, icon, cmd, is_accent=False):
        img = self._get_edit_icon(icon)
        color = "#2ecc71" if is_accent else "transparent"
        btn = ctk.CTkButton(parent, text="", image=img, width=34, height=34, fg_color=color, 
                            hover_color=("#e0e0e0", "#404040"), command=cmd)
        btn.pack(side="left", padx=2)
        return btn

    def _add_sep(self, parent):
        ctk.CTkFrame(parent, width=1, height=25, fg_color="gray").pack(side="left", padx=10)

    # --- LOGIQUE ---
    def set_tool(self, mode):
        self.tool_mode = mode
        for m, btn in self.tool_btns.items():
            btn.configure(fg_color=("#bbbbbb", "#555555") if m == mode else "transparent")
        self.canvas.config(cursor="xterm" if mode == "text" else "pencil" if mode == "draw" else "arrow")

    def _navigate(self, delta):
        if not self.pdf_doc: return
        new_idx = self.current_page_idx + delta
        if 0 <= new_idx < len(self.pdf_doc):
            self.current_page_idx = new_idx
            self._show_page()

    def _change_zoom(self, delta):
        self.zoom_level = max(0.5, min(4.0, self.zoom_level + delta))
        self.zoom_label.configure(text=f"{int(self.zoom_level*100)}%")
        self._show_page()

    def _show_page(self):
        if not self.pdf_doc: return
        page = self.pdf_doc[self.current_page_idx]
        pix = page.get_pixmap(matrix=fitz.Matrix(self.zoom_level, self.zoom_level))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.tk_img = ImageTk.PhotoImage(img)
        
        self.canvas.config(width=pix.width, height=pix.height)
        self.canvas.delete("pdf_bg") 
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img, tags="pdf_bg")
        self.canvas.tag_lower("pdf_bg")
        self.page_label.configure(text=f"Page {self.current_page_idx + 1} / {len(self.pdf_doc)}")

    def _on_click(self, event):
        self.canvas.focus_set()
        if self.active_entry: self._finalize_text()
        
        if self.tool_mode == "select":
            # On cherche l'objet sous le curseur
            items = self.canvas.find_overlapping(event.x-2, event.y-2, event.x+2, event.y+2)
            editable_items = [i for i in items if "editable" in self.canvas.gettags(i)]
            
            if editable_items:
                item = editable_items[-1] # Le plus haut
                self.selected_item = item
                self.drag_data = {"x": event.x, "y": event.y, "item": item}
                # Feedback visuel : on ne change que l'item sélectionné
                self.canvas.itemconfig("editable", stipple="") # Reset si besoin
            else:
                self.selected_item = None

        elif self.tool_mode == "text":
            self._create_text_input(event.x, event.y)
        
        elif self.tool_mode == "draw":
            self.last_x, self.last_y = event.x, event.y

    def _on_drag(self, event):
        if self.tool_mode == "select" and self.drag_data["item"]:
            dx, dy = event.x - self.drag_data["x"], event.y - self.drag_data["y"]
            self.canvas.move(self.drag_data["item"], dx, dy)
            self.drag_data["x"], self.drag_data["y"] = event.x, event.y
            self.canvas.update_idletasks() # Fluidité
            
        elif self.tool_mode == "draw":
            self.canvas.create_line(self.last_x, self.last_y, event.x, event.y, 
                                   fill=self.current_color, width=2, capstyle="round", 
                                   tags=("editable", "draw_line"))
            self.last_x, self.last_y = event.x, event.y

    def _on_release(self, event):
        self.drag_data["item"] = None

    def _on_double_click(self, event):
        item = self.canvas.find_closest(event.x, event.y)
        if "text_obj" in self.canvas.gettags(item):
            existing_text = self.canvas.itemcget(item, "text")
            coords = self.canvas.coords(item)
            self.canvas.delete(item)
            self._create_text_input(coords[0], coords[1], existing_text)

    def _create_text_input(self, x, y, initial=""):
        self.active_entry = ctk.CTkEntry(self.canvas, font=("Arial", int(self.current_font_size * self.zoom_level)))
        self.active_entry.insert(0, initial)
        self.active_entry.place(x=x, y=y)
        self.active_entry.focus_set()
        self.active_entry.bind("<Return>", lambda e: self._finalize_text())

    def _finalize_text(self):
        if not self.active_entry: return
        txt = self.active_entry.get()
        if txt.strip():
            # On applique la couleur actuelle à cet objet précis
            self.canvas.create_text(self.active_entry.winfo_x(), self.active_entry.winfo_y(), 
                                   text=txt, fill=self.current_color, anchor="nw",
                                   font=("Arial", int(self.current_font_size * self.zoom_level)), 
                                   tags=("editable", "text_obj"))
        self.active_entry.destroy()
        self.active_entry = None

    def _delete_selected(self, event):
        if self.selected_item:
            self.canvas.delete(self.selected_item)
            self.selected_item = None

    def _update_font_settings(self, s): 
        self.current_font_size = int(s)
    
    def _choose_color(self):
        c = colorchooser.askcolor(color=self.current_color)[1]
        if c: 
            self.current_color = c
            self.color_btn.configure(fg_color=c)

    def _open_file_dialog(self):
        path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if path:
            self.pdf_doc = fitz.open(path)
            self.current_page_idx = 0
            self._show_page()

    def save_changes(self):
        # Logique de sauvegarde
        print("Sauvegarde demandée...")
        pass