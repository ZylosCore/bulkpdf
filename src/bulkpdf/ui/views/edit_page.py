import customtkinter as ctk
import fitz
from PIL import Image, ImageTk
from tkinter import Canvas, filedialog, colorchooser, Entry, NW, ALL
import os
from datetime import datetime

class EditPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.pdf_doc = None
        self.pdf_path = None
        self.current_page_idx = 0
        self.zoom_level = 1.3
        
        self.tool_mode = "select"
        self.selected_items = []
        self.selection_rect_id = None 
        self.active_entry_window = None 
        
        self.drag_data = {"x": 0, "y": 0}
        self.current_font_size = 14
        self.current_color = "#2c3e50" 
        
        self._setup_ui()
        self._setup_bindings()

    def _get_edit_icon(self, name, size=(18, 18)):
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            paths = [os.path.join(base_path, "src", "assets", "edit", f"{name}.png"),
                     os.path.join(os.getcwd(), "src", "assets", "edit", f"{name}.png"),
                     os.path.join(os.getcwd(), "assets", "edit", f"{name}.png")]
            for p in paths:
                if os.path.exists(p):
                    img_light = Image.open(p).convert("RGBA")
                    r, g, b, a = img_light.split()
                    img_dark = Image.merge("RGBA", (r.point(lambda _: 255), g.point(lambda _: 255), b.point(lambda _: 255), a))
                    return ctk.CTkImage(light_image=img_light, dark_image=img_dark, size=size)
            return None
        except: return None

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.toolbar = ctk.CTkFrame(self, height=45, fg_color=("#ffffff", "#2b2b2b"), corner_radius=0)
        self.toolbar.grid(row=0, column=0, sticky="ew")
        self.toolbar.grid_propagate(False)

        container = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        container.pack(side="left", padx=10, fill="y")

        self._create_btn(container, "open", "Ouvrir", self._open_file_dialog)
        self._create_btn(container, "save", "Sauver", self.save_changes, is_accent=True)
        self._add_sep(container)

        self.tool_btns = {}
        for icon, mode in [("cursor", "select"), ("text", "text"), ("draw", "draw"), ("eraser", "erase")]:
            btn = self._create_btn(container, icon, mode, lambda m=mode: self.set_tool(m))
            self.tool_btns[mode] = btn
        
        self._add_sep(container)
        self._create_btn(container, "rotate", "Rot.", self._rotate_selected)
        self._create_btn(container, "plus", "A+", lambda: self._change_item_size(2))
        self._create_btn(container, "minus", "A-", lambda: self._change_item_size(-2))
        self._create_btn(container, "trash", "Suppr.", self._delete_selected)
        
        self._add_sep(container)
        self.size_menu = ctk.CTkComboBox(container, values=["12", "14", "18", "24", "32", "48"], width=65, height=28, command=self._update_font_settings)
        self.size_menu.set("14")
        self.size_menu.pack(side="left", padx=5)
        
        self.color_btn = ctk.CTkButton(container, text="", width=24, height=24, fg_color=self.current_color, command=self._choose_color, corner_radius=12)
        self.color_btn.pack(side="left", padx=5)

        self.scroll_canvas = ctk.CTkScrollableFrame(self, fg_color=("#ebebeb", "#1a1a1a"), corner_radius=0)
        self.scroll_canvas.grid(row=1, column=0, sticky="nsew")
        self.canvas = Canvas(self.scroll_canvas, bg="white", bd=0, highlightthickness=0)
        self.canvas.pack(pady=20)

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
        self.master.bind("<Control-plus>", lambda e: self._change_zoom(0.1))
        self.master.bind("<Control-minus>", lambda e: self._change_zoom(-0.1))
        self.master.bind("<Delete>", lambda e: self._delete_selected())

    def _create_text_input(self, x, y):
        entry = Entry(self.canvas, font=("Arial", self.current_font_size), fg=self.current_color, bd=1, relief="flat")
        entry.focus_set()
        window_id = self.canvas.create_window(x, y, window=entry, anchor=NW)
        self.active_entry_window = window_id

        def finalize(event=None):
            if not self.canvas.bbox(window_id): return
            content = entry.get().strip()
            self.canvas.delete(window_id)
            self.active_entry_window = None
            if content:
                txt_id = self.canvas.create_text(x, y, text=content, font=("Arial", self.current_font_size), 
                                                fill=self.current_color, anchor=NW, tags=("editable", "text_obj"))
                self.selected_items = [txt_id]
                self._draw_highlights()

        entry.bind("<Return>", finalize)
        entry.bind("<FocusOut>", lambda e: self.after(100, finalize))

    def _on_click(self, event):
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        if self.active_entry_window: return
        if self.tool_mode == "select":
            item = self.canvas.find_closest(cx, cy)
            if "editable" in self.canvas.gettags(item):
                if item not in self.selected_items: self.selected_items = [item]
            else:
                self.selected_items = []
                self.rect_start_x, self.rect_start_y = cx, cy
                self.selection_rect_id = self.canvas.create_rectangle(cx, cy, cx, cy, outline="#3498db", dash=(4,4))
            self.drag_data = {"x": cx, "y": cy}
            self._draw_highlights()
        elif self.tool_mode == "text": self._create_text_input(cx, cy)
        elif self.tool_mode == "draw": self.last_x, self.last_y = cx, cy

    def _on_drag(self, event):
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        if self.tool_mode == "select":
            if self.selection_rect_id:
                self.canvas.coords(self.selection_rect_id, self.rect_start_x, self.rect_start_y, cx, cy)
            elif self.selected_items:
                dx, dy = cx - self.drag_data["x"], cy - self.drag_data["y"]
                for item in self.selected_items: self.canvas.move(item, dx, dy)
                self.drag_data["x"], self.drag_data["y"] = cx, cy
                self._draw_highlights()
        elif self.tool_mode == "draw":
            self.canvas.create_line(self.last_x, self.last_y, cx, cy, fill=self.current_color, width=2, capstyle="round", tags=("editable", "draw_line"))
            self.last_x, self.last_y = cx, cy
        elif self.tool_mode == "erase":
            items = self.canvas.find_overlapping(cx-5, cy-5, cx+5, cy+5)
            for it in items:
                if "draw_line" in self.canvas.gettags(it): self.canvas.delete(it)

    def _on_release(self, event):
        if self.selection_rect_id:
            coords = self.canvas.coords(self.selection_rect_id)
            found = self.canvas.find_enclosed(coords[0], coords[1], coords[2], coords[3])
            self.selected_items = [it for it in found if "editable" in self.canvas.gettags(it)]
            self.canvas.delete(self.selection_rect_id)
            self.selection_rect_id = None
            self._draw_highlights()

    def _draw_highlights(self):
        self.canvas.delete("highlighter")
        for item in self.selected_items:
            bbox = self.canvas.bbox(item)
            if bbox: self.canvas.create_rectangle(bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2, outline="#3498db", width=1, tags="highlighter")

    def _delete_selected(self):
        for item in self.selected_items: self.canvas.delete(item)
        self.selected_items = []; self.canvas.delete("highlighter")

    def _rotate_selected(self):
        for item in self.selected_items:
            if "text_obj" in self.canvas.gettags(item):
                anchors = [NW, "n", "ne", "e", "se", "s", "sw", "w"]
                curr = self.canvas.itemcget(item, "anchor")
                nxt = anchors[(anchors.index(curr) + 2) % len(anchors)]
                self.canvas.itemconfig(item, anchor=nxt)
        self._draw_highlights()

    def _change_item_size(self, delta):
        for item in self.selected_items:
            if "text_obj" in self.canvas.gettags(item):
                f = self.canvas.itemcget(item, "font").split()
                sz = max(6, int(f[-1]) + delta)
                self.canvas.itemconfig(item, font=("Arial", sz))
        self._draw_highlights()

    def _show_page(self):
        if not self.pdf_doc: return
        page = self.pdf_doc[self.current_page_idx]
        pix = page.get_pixmap(matrix=fitz.Matrix(self.zoom_level, self.zoom_level))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.tk_img = ImageTk.PhotoImage(img)
        self.canvas.config(width=pix.width, height=pix.height)
        self.canvas.delete(ALL)
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
        self.page_label.configure(text=f"Page {self.current_page_idx + 1} / {len(self.pdf_doc)}")
        self.selected_items = []

    def _navigate(self, delta):
        if not self.pdf_doc: return
        new_idx = self.current_page_idx + delta
        if 0 <= new_idx < len(self.pdf_doc):
            self.current_page_idx = new_idx; self._show_page()

    def _change_zoom(self, delta):
        self.zoom_level = max(0.5, min(4.0, self.zoom_level + delta))
        self.zoom_label.configure(text=f"{int(self.zoom_level*100)}%")
        self._show_page()

    def _open_file_dialog(self):
        p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if p: 
            self.pdf_path = p
            self.pdf_doc = fitz.open(p)
            self.current_page_idx = 0
            self._show_page()

    def save_changes(self):
        """Migre les éléments du Canvas vers le document PDF avant sauvegarde"""
        if not self.pdf_doc: return
        
        # On récupère la page PDF actuelle pour y dessiner
        page = self.pdf_doc[self.current_page_idx]
        
        # Ratio pour convertir les coordonnées Canvas -> PDF (car zoom_level affecte le canvas)
        # Les coordonnées PDF sont en points (1/72 inch). 
        # On divise par le zoom pour revenir à la taille réelle du PDF.
        ratio = 1 / self.zoom_level

        # Parcourir tous les éléments créés sur le canvas
        for item in self.canvas.find_withtag("editable"):
            tags = self.canvas.gettags(item)
            
            if "text_obj" in tags:
                coords = self.canvas.coords(item)
                text = self.canvas.itemcget(item, "text")
                fill = self.canvas.itemcget(item, "fill")
                font_info = self.canvas.itemcget(item, "font").split()
                font_size = float(font_info[-1]) * ratio
                
                # Conversion couleur Hex -> RGB (0.0 à 1.0)
                rgb = [int(fill[i:i+2], 16)/255 for i in (1, 3, 5)]
                
                # Insertion dans le PDF
                page.insert_text((coords[0]*ratio, coords[1]*ratio + font_size), 
                                 text, fontsize=font_size, color=rgb)

            elif "draw_line" in tags:
                coords = self.canvas.coords(item) # x1, y1, x2, y2
                fill = self.canvas.itemcget(item, "fill")
                rgb = [int(fill[i:i+2], 16)/255 for i in (1, 3, 5)]
                
                # Dessiner le trait dans le PDF
                p1 = fitz.Point(coords[0]*ratio, coords[1]*ratio)
                p2 = fitz.Point(coords[2]*ratio, coords[3]*ratio)
                page.draw_line(p1, p2, color=rgb, width=2*ratio)

        # Génération du nom de fichier
        dir_name = os.path.dirname(self.pdf_path) if self.pdf_path else ""
        base_name = os.path.splitext(os.path.basename(self.pdf_path))[0] if self.pdf_path else "doc"
        current_date = datetime.now().strftime("%Y-%m-%d_%H-%M")
        new_name = f"{base_name}_edited_{current_date}.pdf"
        
        save_path = filedialog.asksaveasfilename(
            initialfile=new_name,
            initialdir=dir_name,
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")]
        )
        
        if save_path:
            self.pdf_doc.save(save_path)
            # Recharger pour nettoyer le canvas des objets migrés (facultatif)
            self._show_page()

    def _create_btn(self, parent, icon, alt, cmd, is_accent=False):
        img = self._get_edit_icon(icon)
        btn = ctk.CTkButton(parent, text="" if img else alt, image=img, width=34, height=34,
                             fg_color="#2ecc71" if is_accent else "transparent", command=cmd)
        btn.pack(side="left", padx=2); return btn

    def _create_nav_btn(self, parent, icon, cmd):
        img = self._get_edit_icon(icon, (16,16))
        ctk.CTkButton(parent, text="" if img else icon, image=img, width=30, fg_color="transparent", command=cmd).pack(side="left")

    def set_tool(self, mode):
        self.tool_mode = mode; self.selected_items = []; self.canvas.delete("highlighter")
        for m, btn in self.tool_btns.items(): btn.configure(fg_color=("#bbbbbb", "#555555") if m == mode else "transparent")

    def _update_font_settings(self, v): 
        self.current_font_size = int(v)
        for item in self.selected_items:
            if "text_obj" in self.canvas.gettags(item): self.canvas.itemconfig(item, font=("Arial", v))

    def _choose_color(self):
        c = colorchooser.askcolor()[1]
        if c: 
            self.current_color = c; self.color_btn.configure(fg_color=c)
            for item in self.selected_items: self.canvas.itemconfig(item, fill=c)

    def _add_sep(self, parent): ctk.CTkFrame(parent, width=1, height=25, fg_color="gray").pack(side="left", padx=10)