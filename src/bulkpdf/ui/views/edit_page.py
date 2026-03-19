import customtkinter as ctk
import fitz
from PIL import Image, ImageTk
from tkinter import Canvas, filedialog, colorchooser
import os

class EditPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # État du document
        self.pdf_doc = None
        self.current_page_idx = 0
        self.zoom_level = 1.3
        
        # Stockage des objets par page {page_num: [item_ids]}
        self.pages_objects = {}
        
        # État des outils
        self.tool_mode = "select"
        self.selected_item = None
        self.active_entry = None
        self.active_window = None
        self.drag_data = {"x": 0, "y": 0, "item": None}
        self.current_font_size = 14
        self.current_color = "#2c3e50" 
        
        self._setup_ui()
        self._setup_bindings()

    def _get_edit_icon(self, name, size=(18, 18)):
        """Charge l'icône et génère une version blanche pour le mode sombre"""
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            icon_path = os.path.join(base_path, "assets", "edit", f"{name}.png")
            
            if os.path.exists(icon_path):
                img_light = Image.open(icon_path).convert("RGBA")
                r, g, b, a = img_light.split()
                img_dark = Image.merge("RGBA", (r.point(lambda _: 255), g.point(lambda _: 255), b.point(lambda _: 255), a))
                return ctk.CTkImage(light_image=img_light, dark_image=img_dark, size=size)
            return None
        except: return None

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- TOOLBAR ---
        self.toolbar = ctk.CTkFrame(self, height=45, fg_color=("#ffffff", "#2b2b2b"), corner_radius=0)
        self.toolbar.grid(row=0, column=0, sticky="ew")
        self.toolbar.grid_propagate(False)

        container = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        container.pack(side="left", padx=10, fill="y")

        self._create_btn(container, "open", self._open_file_dialog)
        self._create_btn(container, "save", self.save_changes, is_accent=True)
        self._add_sep(container)

        self.tool_btns = {}
        for icon, mode in [("cursor", "select"), ("text", "text"), ("draw", "draw")]:
            btn = self._create_btn(container, icon, lambda m=mode: self.set_tool(m))
            self.tool_btns[mode] = btn
        
        self._add_sep(container)
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

        # --- STATUS BAR (Navigation & Zoom) ---
        self.status_bar = ctk.CTkFrame(self, height=35, fg_color=("#dbdbdb", "#252525"), corner_radius=0)
        self.status_bar.grid(row=2, column=0, sticky="ew")

        # Navigation Pages
        nav_cnt = ctk.CTkFrame(self.status_bar, fg_color="transparent")
        nav_cnt.pack(side="left", padx=20)
        ctk.CTkButton(nav_cnt, text="<", width=30, command=lambda: self._navigate(-1)).pack(side="left", padx=2)
        self.page_label = ctk.CTkLabel(nav_cnt, text="Page 0 / 0", font=("Arial", 11, "bold"))
        self.page_label.pack(side="left", padx=10)
        ctk.CTkButton(nav_cnt, text=">", width=30, command=lambda: self._navigate(1)).pack(side="left", padx=2)

        # Zoom
        zoom_cnt = ctk.CTkFrame(self.status_bar, fg_color="transparent")
        zoom_cnt.pack(side="right", padx=20)
        ctk.CTkButton(zoom_cnt, text="-", width=30, command=lambda: self._change_zoom(-0.1)).pack(side="left")
        self.zoom_label = ctk.CTkLabel(zoom_cnt, text=f"{int(self.zoom_level*100)}%", width=50)
        self.zoom_label.pack(side="left")
        ctk.CTkButton(zoom_cnt, text="+", width=30, command=lambda: self._change_zoom(0.1)).pack(side="left")

    def _setup_bindings(self):
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.master.bind("<Delete>", self._delete_selected)

    def _create_btn(self, parent, icon, cmd, is_accent=False):
        img = self._get_edit_icon(icon)
        color = "#2ecc71" if is_accent else "transparent"
        btn = ctk.CTkButton(parent, text="", image=img, width=34, height=34, fg_color=color, 
                            hover_color=("#e0e0e0", "#404040"), command=cmd)
        btn.pack(side="left", padx=2)
        return btn

    def _add_sep(self, parent):
        ctk.CTkFrame(parent, width=1, height=25, fg_color="gray").pack(side="left", padx=10)

    # --- NAVIGATION & ZOOM ---
    def set_tool(self, mode):
        self.tool_mode = mode
        for m, btn in self.tool_btns.items():
            btn.configure(fg_color=("#bbbbbb", "#555555") if m == mode else "transparent")
        self.canvas.config(cursor="xterm" if mode == "text" else "pencil" if mode == "draw" else "arrow")

    def _navigate(self, delta):
        if not self.pdf_doc: return
        self._toggle_page_objects(self.current_page_idx, False)
        new_idx = self.current_page_idx + delta
        if 0 <= new_idx < len(self.pdf_doc):
            self.current_page_idx = new_idx
            self._show_page()
            self._toggle_page_objects(self.current_page_idx, True)

    def _change_zoom(self, delta):
        if not self.pdf_doc: return
        old_zoom = self.zoom_level
        self.zoom_level = max(0.5, min(4.0, self.zoom_level + delta))
        self.zoom_label.configure(text=f"{int(self.zoom_level*100)}%")
        
        ratio = self.zoom_level / old_zoom
        self._show_page()
        
        # Mise à l'échelle de tous les objets (toutes pages)
        for p_idx in self.pages_objects:
            for item_id in self.pages_objects[p_idx]:
                self.canvas.scale(item_id, 0, 0, ratio, ratio)
                if "text_obj" in self.canvas.gettags(item_id):
                    new_size = int(self.current_font_size * self.zoom_level)
                    self.canvas.itemconfig(item_id, font=("Arial", new_size))

    def _toggle_page_objects(self, page_idx, visible):
        state = "normal" if visible else "hidden"
        for item_id in self.pages_objects.get(page_idx, []):
            self.canvas.itemconfigure(item_id, state=state)

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

    # --- ÉVÉNEMENTS CANVAS ---
    def _on_click(self, event):
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.canvas.focus_set()
        if self.active_entry: self._finalize_text()
        
        if self.tool_mode == "select":
            items = self.canvas.find_overlapping(cx-2, cy-2, cx+2, cy+2)
            editable_items = [i for i in items if "editable" in self.canvas.gettags(i)]
            if editable_items:
                item = editable_items[-1]
                self.selected_item = item
                self.drag_data = {"x": cx, "y": cy, "item": item}
            else:
                self.selected_item = None

        elif self.tool_mode == "text":
            self._create_text_input(cx, cy)
        
        elif self.tool_mode == "draw":
            self.last_x, self.last_y = cx, cy

    def _on_drag(self, event):
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        if self.tool_mode == "select" and self.drag_data["item"]:
            dx, dy = cx - self.drag_data["x"], cy - self.drag_data["y"]
            self.canvas.move(self.drag_data["item"], dx, dy)
            self.drag_data["x"], self.drag_data["y"] = cx, cy
        elif self.tool_mode == "draw":
            line = self.canvas.create_line(self.last_x, self.last_y, cx, cy, 
                                          fill=self.current_color, width=2, capstyle="round", 
                                          tags=("editable", "draw_line"))
            self._register_object(line)
            self.last_x, self.last_y = cx, cy

    def _on_release(self, event):
        self.drag_data["item"] = None

    def _on_double_click(self, event):
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        item = self.canvas.find_closest(cx, cy)
        if "text_obj" in self.canvas.gettags(item):
            existing_text = self.canvas.itemcget(item, "text")
            coords = self.canvas.coords(item)
            self.canvas.delete(item)
            self._create_text_input(coords[0], coords[1], existing_text)

    # --- TEXTE & REGISTRE ---
    def _create_text_input(self, x, y, initial=""):
        self.active_entry = ctk.CTkEntry(self.canvas, font=("Arial", int(self.current_font_size * self.zoom_level)))
        self.active_entry.insert(0, initial)
        self.active_window = self.canvas.create_window(x, y, window=self.active_entry, anchor="nw")
        self.active_entry.focus_set()
        self.active_entry.bind("<Return>", lambda e: self._finalize_text())

    def _finalize_text(self):
        if not self.active_entry: return
        txt = self.active_entry.get()
        pos = self.canvas.coords(self.active_window)
        if txt.strip():
            text_id = self.canvas.create_text(pos[0], pos[1], text=txt, fill=self.current_color, anchor="nw",
                                             font=("Arial", int(self.current_font_size * self.zoom_level)), 
                                             tags=("editable", "text_obj"))
            self._register_object(text_id)
        self.canvas.delete(self.active_window)
        self.active_entry = None
        self.active_window = None

    def _register_object(self, item_id):
        if self.current_page_idx not in self.pages_objects:
            self.pages_objects[self.current_page_idx] = []
        self.pages_objects[self.current_page_idx].append(item_id)

    def _delete_selected(self, event):
        if self.selected_item:
            for p in self.pages_objects:
                if self.selected_item in self.pages_objects[p]:
                    self.pages_objects[p].remove(self.selected_item)
            self.canvas.delete(self.selected_item)
            self.selected_item = None

    def _update_font_settings(self, s): self.current_font_size = int(s)
    
    def _choose_color(self):
        c = colorchooser.askcolor(color=self.current_color)[1]
        if c: 
            self.current_color = c
            self.color_btn.configure(fg_color=c)

    def _open_file_dialog(self):
        path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if path:
            self.pdf_doc = fitz.open(path)
            self.pages_objects = {}
            self.current_page_idx = 0
            self._show_page()

    def save_changes(self):
        # Pour l'instant, affiche juste une confirmation dans la console
        print("Exportation des modifications en cours...")