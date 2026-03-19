import customtkinter as ctk
import fitz
from PIL import Image, ImageTk
from tkinter import Canvas, filedialog, colorchooser, Entry, NW, ALL
import os
from datetime import datetime
from pathlib import Path

class EditPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # --- PDF DOCUMENT STATE ---
        self.pdf_doc = None
        self.pdf_path = None
        self.current_page_idx = 0
        self.zoom_level = 1.3
        
        # --- INTERACTION STATE ---
        self.tool_mode = "select"
        self.selected_items = []
        self.drag_data = {"x": 0, "y": 0}
        self.active_entry_window = None 
        self.selection_rect_id = None
        self.rect_start_x = 0
        self.rect_start_y = 0
        
        # --- DRAWING & TEXT SETTINGS ---
        self.current_font_size = 14
        self.current_color = "#2c3e50" 
        self.last_x, self.last_y = 0, 0
        
        # --- SIGNATURE SETTINGS ---
        # Fixed path for the default signature (managed by SettingsPage)
        self.signature_img_path = Path("src/assets/edit/user_signature.png")
        
        # Dictionary to store references for images to handle scaling and prevent garbage collection
        # Format: {item_id: {"photo": PhotoImage, "original": PIL.Image, "current_w": int, "current_h": int}}
        self.image_refs = {}
        
        self._setup_ui()
        self._setup_bindings()

    def _get_edit_icon(self, name, size=(18, 18)):
        """Loads icons with support for both light and dark themes."""
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            paths = [
                os.path.join(base_path, "src", "assets", "edit", f"{name}.png"),
                os.path.join(os.getcwd(), "src", "assets", "edit", f"{name}.png")
            ]
            for p in paths:
                if os.path.exists(p):
                    img_light = Image.open(p).convert("RGBA")
                    # Create a white version for dark mode
                    r, g, b, a = img_light.split()
                    img_dark = Image.merge("RGBA", (r.point(lambda _: 255), g.point(lambda _: 255), b.point(lambda _: 255), a))
                    return ctk.CTkImage(light_image=img_light, dark_image=img_dark, size=size)
            return None
        except: return None

    def _setup_ui(self):
        """Initializes the layout components: Toolbar, Canvas, and Status bar."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- TOOLBAR SECTION ---
        self.toolbar = ctk.CTkFrame(self, height=45, fg_color=("#ffffff", "#2b2b2b"), corner_radius=0)
        self.toolbar.grid(row=0, column=0, sticky="ew")
        self.toolbar.grid_propagate(False)

        container = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        container.pack(side="left", padx=10, fill="y")

        # Basic Actions
        self._create_btn(container, "open", "Ouvrir", self._open_file_dialog)
        self._create_btn(container, "save", "Enregistrer", self.save_changes, is_accent=True)
        self._add_sep(container)

        # Tool Modes
        self.tool_btns = {}
        tools = [
            ("cursor", "select"), 
            ("text", "text"), 
            ("draw", "draw"), 
            ("eraser", "erase"), 
            ("protect", "signature")
        ]
        for icon, mode in tools:
            btn = self._create_btn(container, icon, mode, lambda m=mode: self.set_tool(m))
            self.tool_btns[mode] = btn
        
        self._add_sep(container)
        
        # Modification Tools
        self._create_btn(container, "rotate", "Rotation", self._rotate_selected)
        self._create_btn(container, "plus", "Agrandir", lambda: self._change_item_size(1.2))
        self._create_btn(container, "minus", "Réduire", lambda: self._change_item_size(0.8))
        self._create_btn(container, "trash", "Supprimer", self._delete_selected)
        
        self._add_sep(container)
        
        # Appearance (Font Size & Color)
        self.size_menu = ctk.CTkComboBox(container, values=["12", "14", "18", "24", "32", "48"], 
                                         width=65, height=28, command=self._update_font_settings)
        self.size_menu.set("14")
        self.size_menu.pack(side="left", padx=5)
        
        self.color_btn = ctk.CTkButton(container, text="", width=24, height=24, 
                                       fg_color=self.current_color, command=self._choose_color, corner_radius=12)
        self.color_btn.pack(side="left", padx=5)

        # --- CANVAS SECTION ---
        self.scroll_canvas = ctk.CTkScrollableFrame(self, fg_color=("#ebebeb", "#1a1a1a"), corner_radius=0)
        self.scroll_canvas.grid(row=1, column=0, sticky="nsew")
        
        self.canvas = Canvas(self.scroll_canvas, bg="white", bd=0, highlightthickness=0)
        self.canvas.pack(pady=20)

        # --- STATUS BAR SECTION ---
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

    # --- UI HELPERS ---

    def _create_btn(self, parent, icon_name, tooltip, command, is_accent=False):
        icon = self._get_edit_icon(icon_name)
        btn = ctk.CTkButton(parent, text="", image=icon, width=32, height=32, 
                            fg_color="transparent" if not is_accent else "#6272a4",
                            hover_color="#44475a", command=command)
        btn.pack(side="left", padx=2)
        return btn

    def _create_nav_btn(self, parent, icon_name, command):
        icon = self._get_edit_icon(icon_name, size=(14, 14))
        btn = ctk.CTkButton(parent, text="", image=icon, width=28, height=28, 
                            fg_color="transparent", hover_color="#44475a", command=command)
        btn.pack(side="left", padx=2)

    def _add_sep(self, parent):
        ctk.CTkFrame(parent, width=2, height=25, fg_color="#44475a").pack(side="left", padx=10)

    def set_tool(self, mode):
        """Updates the active tool mode and visual feedback."""
        self.tool_mode = mode
        self.selected_items = []
        self.canvas.delete("highlighter")
        for m, btn in self.tool_btns.items():
            btn.configure(fg_color="#44475a" if m == mode else "transparent")

    # --- BINDINGS & FIXES ---

    def _setup_bindings(self):
        """Sets up mouse and global keyboard shortcuts."""
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        
        # Double-click to edit text
        self.canvas.bind("<Double-Button-1>", self._on_double_click)

        # Zoom shortcuts (Control + / Control -)
        # Binding to master ensures they work regardless of widget focus
        self.master.bind("<Control-plus>", lambda e: self._change_zoom(0.1))
        self.master.bind("<Control-equal>", lambda e: self._change_zoom(0.1)) # For non-numeric keyboards
        self.master.bind("<Control-KP_Add>", lambda e: self._change_zoom(0.1))
        
        self.master.bind("<Control-minus>", lambda e: self._change_zoom(-0.1))
        self.master.bind("<Control-KP_Subtract>", lambda e: self._change_zoom(-0.1))
        
        # Delete shortcut
        self.master.bind("<Delete>", lambda e: self._delete_selected())

    def _on_double_click(self, event):
        """Triggered on double-click to edit an existing text object."""
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        item = self.canvas.find_closest(cx, cy)
        tags = self.canvas.gettags(item)
        
        if "text_obj" in tags:
            # Capture current text content and location
            current_text = self.canvas.itemcget(item, "text")
            coords = self.canvas.coords(item)
            
            # Remove the current text object and open an entry field at that position
            self.canvas.delete(item)
            self._create_text_input(coords[0], coords[1], initial_text=current_text)

    def _on_click(self, event):
        """Processes initial mouse clicks based on active tool."""
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        if self.active_entry_window: return
        
        if self.tool_mode == "select":
            item = self.canvas.find_closest(cx, cy)
            if "editable" in self.canvas.gettags(item):
                self.selected_items = [item]
                self.drag_data = {"x": cx, "y": cy}
            else:
                self.selected_items = []
                self.rect_start_x, self.rect_start_y = cx, cy
                self.selection_rect_id = self.canvas.create_rectangle(cx, cy, cx, cy, outline="#3498db", dash=(4,4))
            self._draw_highlights()
            
        elif self.tool_mode == "text":
            self._create_text_input(cx, cy)
            
        elif self.tool_mode == "draw":
            self.last_x, self.last_y = cx, cy
            
        elif self.tool_mode == "signature":
            self._add_signature(cx, cy)

    def _on_drag(self, event):
        """Handles item movement or drawing strokes."""
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        
        if self.tool_mode == "select":
            if self.selection_rect_id:
                self.canvas.coords(self.selection_rect_id, self.rect_start_x, self.rect_start_y, cx, cy)
            elif self.selected_items:
                dx, dy = cx - self.drag_data["x"], cy - self.drag_data["y"]
                for item in self.selected_items:
                    self.canvas.move(item, dx, dy)
                self.drag_data["x"], self.drag_data["y"] = cx, cy
                self._draw_highlights()
                
        elif self.tool_mode == "draw":
            self.canvas.create_line(self.last_x, self.last_y, cx, cy, fill=self.current_color, 
                                    width=2, capstyle="round", tags=("editable", "draw_line"))
            self.last_x, self.last_y = cx, cy
            
        elif self.tool_mode == "erase":
            items = self.canvas.find_overlapping(cx-5, cy-5, cx+5, cy+5)
            for it in items:
                if "draw_line" in self.canvas.gettags(it):
                    self.canvas.delete(it)

    def _on_release(self, event):
        """Finalizes the selection rectangle."""
        if self.selection_rect_id:
            coords = self.canvas.coords(self.selection_rect_id)
            found = self.canvas.find_enclosed(coords[0], coords[1], coords[2], coords[3])
            self.selected_items = [it for it in found if "editable" in self.canvas.gettags(it)]
            self.canvas.delete(self.selection_rect_id)
            self.selection_rect_id = None
            self._draw_highlights()

    # --- EDITING LOGIC ---

    def _add_signature(self, x, y):
        """Places the user signature from assets onto the canvas."""
        if not self.signature_img_path.exists():
            return
            
        orig = Image.open(self.signature_img_path).convert("RGBA")
        display_img = orig.copy()
        display_img.thumbnail((150, 150), Image.Resampling.LANCZOS)
        
        photo = ImageTk.PhotoImage(display_img)
        item_id = self.canvas.create_image(x, y, image=photo, anchor=NW, tags=("editable", "signature"))
        
        # Preserve reference and high-res source for resizing
        self.image_refs[item_id] = {
            "photo": photo,
            "original": orig,
            "current_w": display_img.width,
            "current_h": display_img.height
        }
        self.set_tool("select")

    def _create_text_input(self, x, y, initial_text=""):
        """Opens a temporary Entry to type or edit text on the canvas."""
        entry = Entry(self.canvas, font=("Arial", self.current_font_size), fg=self.current_color, bd=1, relief="flat")
        if initial_text:
            entry.insert(0, initial_text)
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

    def _rotate_selected(self):
        """Rotates selected text anchors or signature images."""
        for item in self.selected_items:
            tags = self.canvas.gettags(item)
            if "text_obj" in tags:
                anchors = [NW, "n", "ne", "e", "se", "s", "sw", "w"]
                curr = self.canvas.itemcget(item, "anchor")
                nxt = anchors[(anchors.index(curr) + 2) % len(anchors)]
                self.canvas.itemconfig(item, anchor=nxt)
            elif "signature" in tags and item in self.image_refs:
                data = self.image_refs[item]
                data["original"] = data["original"].rotate(-90, expand=True)
                self._refresh_image_item(item)
        self._draw_highlights()

    def _change_item_size(self, factor):
        """Scales selected items by a specific factor."""
        for item in self.selected_items:
            tags = self.canvas.gettags(item)
            if "text_obj" in tags:
                f = self.canvas.itemcget(item, "font").split()
                sz = max(6, int(float(f[-1]) * factor))
                self.canvas.itemconfig(item, font=("Arial", sz))
            elif "signature" in tags and item in self.image_refs:
                data = self.image_refs[item]
                data["current_w"] = int(data["current_w"] * factor)
                data["current_h"] = int(data["current_h"] * factor)
                self._refresh_image_item(item)
        self._draw_highlights()

    def _refresh_image_item(self, item_id):
        """Updates the canvas image representation from the high-res PIL source."""
        data = self.image_refs[item_id]
        resized = data["original"].copy()
        resized.thumbnail((data["current_w"], data["current_h"]), Image.Resampling.LANCZOS)
        new_photo = ImageTk.PhotoImage(resized)
        self.canvas.itemconfig(item_id, image=new_photo)
        data["photo"] = new_photo 

    def _draw_highlights(self):
        """Draws visual selection markers around items."""
        self.canvas.delete("highlighter")
        for item in self.selected_items:
            bbox = self.canvas.bbox(item)
            if bbox:
                self.canvas.create_rectangle(bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2, 
                                             outline="#3498db", width=1, tags="highlighter")

    def _delete_selected(self):
        """Removes selected objects and clears metadata."""
        for item in self.selected_items:
            self.canvas.delete(item)
            if item in self.image_refs:
                del self.image_refs[item]
        self.selected_items = []
        self.canvas.delete("highlighter")

    # --- PDF ENGINE & RENDER ---

    def _open_file_dialog(self):
        """Standard file dialog to open a PDF document."""
        p = filedialog.askopenfilename(filetypes=[("Documents PDF", "*.pdf")])
        if p: 
            self.pdf_path = p
            self.pdf_doc = fitz.open(p)
            self.current_page_idx = 0
            self._show_page()

    def _show_page(self):
        """Renders the current PDF page to the canvas background."""
        if not self.pdf_doc: return
        page = self.pdf_doc[self.current_page_idx]
        pix = page.get_pixmap(matrix=fitz.Matrix(self.zoom_level, self.zoom_level))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        self.tk_img = ImageTk.PhotoImage(img)
        self.canvas.config(width=pix.width, height=pix.height)
        self.canvas.delete(ALL) 
        self.canvas.create_image(0, 0, anchor=NW, image=self.tk_img, tags="background")
        self.page_label.configure(text=f"Page {self.current_page_idx + 1} / {len(self.pdf_doc)}")
        self.selected_items = []

    def _navigate(self, delta):
        """Changes the current page being viewed."""
        if not self.pdf_doc: return
        new_idx = self.current_page_idx + delta
        if 0 <= new_idx < len(self.pdf_doc):
            self.current_page_idx = new_idx
            self._show_page()

    def _change_zoom(self, delta):
        """Adjusts the rendering zoom factor and refreshes the view."""
        self.zoom_level = max(0.5, min(4.0, self.zoom_level + delta))
        self.zoom_label.configure(text=f"{int(self.zoom_level*100)}%")
        self._show_page()

    def _update_font_settings(self, v): 
        """Sets the font size for text tools and selection."""
        self.current_font_size = int(v)
        for item in self.selected_items:
            if "text_obj" in self.canvas.gettags(item):
                self.canvas.itemconfig(item, font=("Arial", v))

    def _choose_color(self):
        """Opens a color picker for tool settings."""
        c = colorchooser.askcolor()[1]
        if c: 
            self.current_color = c
            self.color_btn.configure(fg_color=c)
            for item in self.selected_items:
                self.canvas.itemconfig(item, fill=c)

    def save_changes(self):
        """Exports canvas edits back into a PDF file."""
        if not self.pdf_doc: return
        
        page = self.pdf_doc[self.current_page_idx]
        ratio = 1 / self.zoom_level 

        for item in self.canvas.find_withtag("editable"):
            tags = self.canvas.gettags(item)
            coords = self.canvas.coords(item)
            
            if "text_obj" in tags:
                text = self.canvas.itemcget(item, "text")
                fill = self.canvas.itemcget(item, "fill")
                font_info = self.canvas.itemcget(item, "font").split()
                font_size = float(font_info[-1]) * ratio
                rgb = [int(fill[i:i+2], 16)/255 for i in (1, 3, 5)]
                # PDF points insertion
                page.insert_text((coords[0]*ratio, coords[1]*ratio + font_size), 
                                 text, fontsize=font_size, color=rgb)

            elif "signature" in tags and item in self.image_refs:
                data = self.image_refs[item]
                import io
                img_byte_arr = io.BytesIO()
                data["original"].save(img_byte_arr, format='PNG')
                
                rect = fitz.Rect(coords[0]*ratio, coords[1]*ratio, 
                                 (coords[0] + data["current_w"])*ratio, 
                                 (coords[1] + data["current_h"])*ratio)
                page.insert_image(rect, stream=img_byte_arr.getvalue())

            elif "draw_line" in tags:
                fill = self.canvas.itemcget(item, "fill")
                rgb = [int(fill[i:i+2], 16)/255 for i in (1, 3, 5)]
                p1 = fitz.Point(coords[0]*ratio, coords[1]*ratio)
                p2 = fitz.Point(coords[2]*ratio, coords[3]*ratio)
                page.draw_line(p1, p2, color=rgb, width=2*ratio)

        save_path = filedialog.asksaveasfilename(defaultextension=".pdf", 
                                                 filetypes=[("Documents PDF", "*.pdf")],
                                                 initialfile=f"edite_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf")
        if save_path:
            self.pdf_doc.save(save_path)
            self._show_page()