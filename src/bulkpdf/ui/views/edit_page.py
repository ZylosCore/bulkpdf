import customtkinter as ctk
import fitz
from PIL import Image, ImageTk
from tkinter import Canvas, filedialog, colorchooser, Entry, NW
import os

class EditPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.pdf_doc = None
        self.current_page_idx = 0
        self.zoom_level = 1.3
        
        # État des outils et sélection
        self.tool_mode = "select"
        self.selected_item = None
        self.selection_rect = None  # Le cadre de sélection bleu
        self.drag_data = {"x": 0, "y": 0, "item": None}
        
        self.current_font_size = 14
        self.current_color = "#2c3e50" 
        
        self._setup_ui()
        self._setup_bindings()

    def _get_edit_icon(self, name, size=(18, 18)):
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            icon_path = os.path.join(base_path, "src", "assets", "edit", f"{name}.png")
            if not os.path.exists(icon_path):
                icon_path = os.path.join(os.getcwd(), "src", "assets", "edit", f"{name}.png")

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

        self._create_btn(container, "open", "Ouvrir", self._open_file_dialog)
        self._create_btn(container, "save", "Sauver", self.save_changes, is_accent=True)
        self._add_sep(container)

        self.tool_btns = {}
        tools = [("cursor", "select"), ("text", "text"), ("draw", "draw"), ("eraser", "erase")]
        for icon, mode in tools:
            btn = self._create_btn(container, icon, mode, lambda m=mode: self.set_tool(m))
            self.tool_btns[mode] = btn
        
        self._add_sep(container)
        
        # Bouton TRASH pour supprimer la sélection
        self.btn_trash = self._create_btn(container, "trash", "Suppr.", self._delete_selected)
        
        self._add_sep(container)
        self.size_menu = ctk.CTkComboBox(container, values=["12", "14", "18", "24", "32", "48"], width=65, height=28, command=self._update_font_settings)
        self.size_menu.set("14")
        self.size_menu.pack(side="left", padx=5)
        
        self.color_btn = ctk.CTkButton(container, text="", width=24, height=24, fg_color=self.current_color, command=self._choose_color, corner_radius=12)
        self.color_btn.pack(side="left", padx=5)

        # --- ZONE CENTRALE ---
        self.scroll_canvas = ctk.CTkScrollableFrame(self, fg_color=("#ebebeb", "#1a1a1a"), corner_radius=0)
        self.scroll_canvas.grid(row=1, column=0, sticky="nsew")
        
        self.canvas = Canvas(self.scroll_canvas, bg="white", bd=0, highlightthickness=0)
        self.canvas.pack(pady=20)

        # --- STATUS BAR ---
        self.status_bar = ctk.CTkFrame(self, height=35, fg_color=("#dbdbdb", "#252525"), corner_radius=0)
        self.status_bar.grid(row=2, column=0, sticky="ew")

        nav_cnt = ctk.CTkFrame(self.status_bar, fg_color="transparent")
        nav_cnt.pack(side="left", padx=20)
        self._create_nav_btn(nav_cnt, "left", lambda: self._navigate(-1))
        self.page_label = ctk.CTkLabel(nav_cnt, text="Page 0 / 0", font=("Arial", 11, "bold"))
        self.page_label.pack(side="left", padx=10)
        self._create_nav_btn(nav_cnt, "right", lambda: self._navigate(1))

        zoom_cnt = ctk.CTkFrame(self.status_bar, fg_color="transparent")
        zoom_cnt.pack(side="right", padx=20)
        self._create_nav_btn(zoom_cnt, "minus", lambda: self._change_zoom(-0.1))
        self.zoom_label = ctk.CTkLabel(zoom_cnt, text=f"{int(self.zoom_level*100)}%", width=50)
        self.zoom_label.pack(side="left")
        self._create_nav_btn(zoom_cnt, "plus", lambda: self._change_zoom(0.1))

    def _setup_bindings(self):
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.master.bind("<Delete>", self._delete_selected)
        self.master.bind("<BackSpace>", self._delete_selected)

    def _update_selection_highlight(self):
        """Affiche le cadre de sélection autour de l'objet"""
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
            self.selection_rect = None
            
        if self.selected_item:
            bbox = self.canvas.bbox(self.selected_item)
            if bbox:
                self.selection_rect = self.canvas.create_rectangle(
                    bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2,
                    outline="#3498db", width=2, dash=(4, 4), tags="ui_element"
                )

    def _on_click(self, event):
        self.canvas.focus_set()
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        
        if self.tool_mode == "select":
            # On cherche l'objet sous le clic (en ignorant les éléments d'UI comme le cadre)
            items = self.canvas.find_overlapping(cx-2, cy-2, cx+2, cy+2)
            found = None
            for it in reversed(items):
                if "editable" in self.canvas.gettags(it):
                    found = it
                    break
            
            self.selected_item = found
            if self.selected_item:
                self.drag_data = {"item": self.selected_item, "x": cx, "y": cy}
            self._update_selection_highlight()

        elif self.tool_mode == "erase":
            item = self.canvas.find_closest(cx, cy)
            if "editable" in self.canvas.gettags(item):
                self.canvas.delete(item)
                if self.selected_item == item: self.selected_item = None
                self._update_selection_highlight()

        elif self.tool_mode == "text":
            self._create_text_input(cx, cy)
            
        elif self.tool_mode == "draw":
            self.last_x, self.last_y = cx, cy

    def _on_drag(self, event):
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        
        if self.tool_mode == "select" and self.drag_data["item"]:
            dx, dy = cx - self.drag_data["x"], cy - self.drag_data["y"]
            self.canvas.move(self.drag_data["item"], dx, dy)
            if self.selection_rect:
                self.canvas.move(self.selection_rect, dx, dy)
            self.drag_data["x"], self.drag_data["y"] = cx, cy
            
        elif self.tool_mode == "draw":
            self.canvas.create_line(self.last_x, self.last_y, cx, cy, 
                                    fill=self.current_color, width=2, 
                                    capstyle="round", tags=("editable", "draw_line"))
            self.last_x, self.last_y = cx, cy

    def _delete_selected(self, event=None):
        if self.selected_item:
            self.canvas.delete(self.selected_item)
            if self.selection_rect:
                self.canvas.delete(self.selection_rect)
            self.selected_item = None
            self.selection_rect = None

    def _on_double_click(self, event):
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        item = self.canvas.find_closest(cx, cy)
        if "text_obj" in self.canvas.gettags(item):
            text = self.canvas.itemcget(item, "text")
            coords = self.canvas.coords(item)
            self.canvas.delete(item)
            if self.selection_rect: self.canvas.delete(self.selection_rect)
            self._create_text_input(coords[0], coords[1], initial_text=text)

    def _create_text_input(self, x, y, initial_text=""):
        # Désélectionner avant de créer un nouveau texte
        self.selected_item = None
        self._update_selection_highlight()

        entry = Entry(self.canvas, font=("Arial", self.current_font_size), 
                      fg=self.current_color, bd=0, highlightthickness=0)
        entry.insert(0, initial_text)
        entry.focus_set()
        window = self.canvas.create_window(x, y, window=entry, anchor=NW)
        
        def finalize(e=None):
            val = entry.get()
            self.canvas.delete(window) # On détruit l'input AVANT de créer le texte définitif
            if val.strip():
                txt_id = self.canvas.create_text(x, y, text=val, 
                                        font=("Arial", self.current_font_size), 
                                        fill=self.current_color, anchor=NW, 
                                        tags=("editable", "text_obj"))
                # Sélectionner automatiquement le nouveau texte
                self.selected_item = txt_id
                self._update_selection_highlight()

        entry.bind("<Return>", finalize)
        entry.bind("<FocusOut>", finalize)

    # --- NAVIGATION & ZOOM ---
    def _show_page(self):
        if not self.pdf_doc: return
        page = self.pdf_doc[self.current_page_idx]
        mat = fitz.Matrix(self.zoom_level, self.zoom_level)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.tk_img = ImageTk.PhotoImage(img)
        self.canvas.config(width=pix.width, height=pix.height)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
        self.page_label.configure(text=f"Page {self.current_page_idx + 1} / {len(self.pdf_doc)}")
        self.selected_item = None
        self.selection_rect = None

    def _navigate(self, delta):
        if not self.pdf_doc: return
        new_idx = self.current_page_idx + delta
        if 0 <= new_idx < len(self.pdf_doc):
            self.current_page_idx = new_idx
            self._show_page()
            self.scroll_canvas._parent_canvas.yview_moveto(0 if delta > 0 else 1)

    def _change_zoom(self, delta):
        self.zoom_level = max(0.5, min(3.0, self.zoom_level + delta))
        self.zoom_label.configure(text=f"{int(self.zoom_level*100)}%")
        self._show_page()

    # --- HELPERS UI ---
    def _create_btn(self, parent, icon, alt, cmd, is_accent=False):
        img = self._get_edit_icon(icon)
        btn = ctk.CTkButton(parent, text="" if img else alt, image=img, width=34, height=34,
                             fg_color="#2ecc71" if is_accent else "transparent", 
                             hover_color=("#e0e0e0", "#404040"), command=cmd)
        btn.pack(side="left", padx=2)
        return btn

    def _create_nav_btn(self, parent, icon, cmd):
        img = self._get_edit_icon(icon, (16,16))
        ctk.CTkButton(parent, text="" if img else icon, image=img, width=30, 
                      fg_color="transparent", hover_color=("#e0e0e0", "#404040"), 
                      command=cmd).pack(side="left")

    def set_tool(self, mode):
        self.tool_mode = mode
        if mode != "select":
            self.selected_item = None
            self._update_selection_highlight()
        for m, btn in self.tool_btns.items():
            btn.configure(fg_color=("#bbbbbb", "#555555") if m == mode else "transparent")

    def _update_font_settings(self, value): self.current_font_size = int(value)
    def _add_sep(self, parent): ctk.CTkFrame(parent, width=1, height=25, fg_color="gray").pack(side="left", padx=10)
    def _choose_color(self):
        c = colorchooser.askcolor()[1]
        if c: self.current_color = c; self.color_btn.configure(fg_color=c)
    def _on_release(self, event): self.drag_data["item"] = None
    def _on_mouse_zoom(self, event): self._change_zoom(0.1 if event.delta > 0 else -0.1)
    def _handle_scroll_navigation(self, event):
        if not self.pdf_doc: return
        scroll_pos = self.scroll_canvas._parent_canvas.yview()
        if event.delta < 0 and scroll_pos[1] >= 0.99: self._navigate(1)
        elif event.delta > 0 and scroll_pos[0] <= 0.01: self._navigate(-1)
    def _open_file_dialog(self):
        path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if path: self.pdf_doc = fitz.open(path); self.current_page_idx = 0; self._show_page()
    def save_changes(self):
        if not self.pdf_doc: return
        p = filedialog.asksaveasfilename(defaultextension=".pdf")
        if p: self.pdf_doc.save(p)