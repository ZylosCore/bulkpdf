import customtkinter as ctk
import fitz
from PIL import Image, ImageTk
from tkinter import Canvas, filedialog, colorchooser, Entry, NW, ALL, messagebox
import os
import sys
import io
import tkinter.font as tkFont
from datetime import datetime
from pathlib import Path

def resource_path(relative_path):
    try:
        base_path = Path(sys._MEIPASS)
    except Exception:
        # Ajuste ce chemin selon ta structure réelle
        base_path = Path(__file__).parent.parent.parent.parent
    return base_path / relative_path

class EditPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # --- CONFIGURATION DES CHEMINS ---
        self.app_data_dir = Path(os.getenv('APPDATA')) / "BulkPDF"
        self.signature_img_path = self.app_data_dir / "signatures" / "user_signature.png"
        
        # --- PDF DOCUMENT STATE ---
        self.pdf_doc = None
        self.current_page_idx = 0
        self.zoom_level = 1.3
        self.pages_data = {} 
        
        # --- INTERACTION STATE ---
        self.tool_mode = "select"
        self.selected_items = []
        self.drag_data = {"x": 0, "y": 0}
        self.active_entry_window = None 
        self.selection_rect_id = None
        self._is_finalizing = False 
        
        # --- DRAWING & TEXT SETTINGS ---
        self.current_font_size = 14
        self.current_color = "#2c3e50" 
        self.last_x, self.last_y = 0, 0
        self.image_refs = {}
        
        self._setup_ui()
        self._setup_bindings()

    # --- MÉTHODE MANQUANTE RÉAJOUTÉE ICI ---
    def _get_edit_icon(self, name, size=(18, 18)):
        """Charge une icône depuis les assets et l'adapte au mode clair/sombre"""
        try:
            p = resource_path(os.path.join("assets", "edit", f"{name}.png"))
            if p.exists():
                img_light = Image.open(str(p)).convert("RGBA")
                # Création d'une version blanche pour le mode sombre
                r, g, b, a = img_light.split()
                img_dark = Image.merge("RGBA", (r.point(lambda _: 255), g.point(lambda _: 255), b.point(lambda _: 255), a))
                return ctk.CTkImage(light_image=img_light, dark_image=img_dark, size=size)
            return None
        except Exception as e:
            print(f"Erreur icône {name}: {e}")
            return None

    def _get_id(self, item):
        if isinstance(item, (tuple, list)):
            return int(item[0]) if item else None
        return int(item) if item is not None else None

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.toolbar = ctk.CTkFrame(self, height=45, fg_color=("#ffffff", "#2b2b2b"), corner_radius=0)
        self.toolbar.grid(row=0, column=0, sticky="ew")
        self.toolbar.grid_propagate(False)

        container = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        container.pack(side="left", padx=10, fill="y")

        self._create_btn(container, "open", "Ouvrir", self._open_file_dialog)
        self._create_btn(container, "save", "Enregistrer", self.save_changes, is_accent=True)
        self._add_sep(container)

        self.tool_btns = {}
        tools = [("cursor", "select"), ("text", "text"), ("draw", "draw"), ("eraser", "erase"), ("protect", "signature")]
        for icon, mode in tools:
            btn = self._create_btn(container, icon, mode, lambda m=mode: self.set_tool(m))
            self.tool_btns[mode] = btn
        
        self._add_sep(container)
        self._create_btn(container, "rotate", "Rotation", self._rotate_selected)
        self._create_btn(container, "plus", "Agrandir", lambda: self._change_item_size(1.1))
        self._create_btn(container, "minus", "Réduire", lambda: self._change_item_size(0.9))
        self._create_btn(container, "trash", "Supprimer", self._delete_selected)
        
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

    # --- LOGIQUE PERSISTENCE ---

    def _save_current_page_state(self):
        if self.pdf_doc is None: return
        current_items = []
        ratio = 1 / self.zoom_level 

        for item in self.canvas.find_withtag("editable"):
            item_id = self._get_id(item)
            tags = self.canvas.gettags(item_id)
            coords = self.canvas.coords(item_id)
            real_coords = [c * ratio for c in coords]
            
            data = {"tags": tags, "coords": real_coords}
            
            if "text_obj" in tags:
                f = tkFont.Font(font=self.canvas.itemcget(item_id, "font"))
                data.update({
                    "text": self.canvas.itemcget(item_id, "text"),
                    "fill": self.canvas.itemcget(item_id, "fill"),
                    "font_family": f.actual("family"),
                    "real_font_size": abs(f.actual("size")) * ratio,
                    "anchor": self.canvas.itemcget(item_id, "anchor")
                })
            elif "draw_line" in tags:
                data.update({"fill": self.canvas.itemcget(item_id, "fill")})
            elif "signature" in tags and item_id in self.image_refs:
                data.update({
                    "original_img": self.image_refs[item_id]["original"],
                    "real_w": self.image_refs[item_id]["current_w"] * ratio,
                    "real_h": self.image_refs[item_id]["current_h"] * ratio
                })
            current_items.append(data)
        self.pages_data[self.current_page_idx] = current_items

    def _load_page_state(self):
        if self.current_page_idx not in self.pages_data: return
        z = self.zoom_level
        self.image_refs = {} 

        for data in self.pages_data[self.current_page_idx]:
            scaled_coords = [c * z for c in data["coords"]]
            
            if "text_obj" in data["tags"]:
                display_size = int(data["real_font_size"] * z)
                self.canvas.create_text(*scaled_coords, text=data["text"], fill=data["fill"], 
                                       font=(data["font_family"], display_size), 
                                       anchor=data["anchor"], tags=data["tags"])
            elif "draw_line" in data["tags"]:
                self.canvas.create_line(*scaled_coords, fill=data["fill"], width=2, capstyle="round", tags=data["tags"])
            elif "signature" in data["tags"]:
                orig = data["original_img"]
                w, h = int(data["real_w"] * z), int(data["real_h"] * z)
                display_img = orig.copy()
                display_img.thumbnail((w, h), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(display_img)
                item_id = self._get_id(self.canvas.create_image(scaled_coords[0], scaled_coords[1], image=photo, anchor=NW, tags=data["tags"]))
                self.image_refs[item_id] = {"photo": photo, "original": orig, "current_w": w, "current_h": h}

    # --- PDF ENGINE ---

    def _show_page(self):
        if not self.pdf_doc: return
        page = self.pdf_doc[self.current_page_idx]
        pix = page.get_pixmap(matrix=fitz.Matrix(self.zoom_level, self.zoom_level))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        self.tk_img = ImageTk.PhotoImage(img)
        self.canvas.config(width=pix.width, height=pix.height)
        self.canvas.delete(ALL) 
        self.canvas.create_image(0, 0, anchor=NW, image=self.tk_img, tags="background")
        
        self._load_page_state() 
        self.page_label.configure(text=f"Page {self.current_page_idx + 1} / {len(self.pdf_doc)}")
        self.selected_items = []

    def _navigate(self, delta):
        if not self.pdf_doc: return
        self._save_current_page_state()
        new_idx = self.current_page_idx + delta
        if 0 <= new_idx < len(self.pdf_doc):
            self.current_page_idx = new_idx
            self._show_page()

    def _change_zoom(self, delta):
        if not self.pdf_doc: return
        self._save_current_page_state()
        self.zoom_level = max(0.5, min(4.0, self.zoom_level + delta))
        self.zoom_label.configure(text=f"{int(self.zoom_level*100)}%")
        self._show_page()

    # --- INTERACTIONS ---

    def _setup_bindings(self):
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)

    def _on_click(self, event):
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        if self.active_entry_window: return 

        if self.tool_mode == "select":
            item = self.canvas.find_closest(cx, cy)
            item_id = self._get_id(item)
            if item_id and "editable" in self.canvas.gettags(item_id):
                self.selected_items = [item_id]
                self.drag_data = {"x": cx, "y": cy}
            else:
                self.selected_items = []
                self.rect_start_x, self.rect_start_y = cx, cy
                self.selection_rect_id = self.canvas.create_rectangle(cx, cy, cx, cy, outline="#3498db", dash=(4,4))
            self._draw_highlights()
        elif self.tool_mode == "text": self._create_text_input(cx, cy)
        elif self.tool_mode == "draw": self.last_x, self.last_y = cx, cy
        elif self.tool_mode == "signature": self._add_signature(cx, cy)

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
            for it in self.canvas.find_overlapping(cx-5, cy-5, cx+5, cy+5):
                if "draw_line" in self.canvas.gettags(it): self.canvas.delete(it)

    def _on_release(self, event):
        if self.selection_rect_id:
            coords = self.canvas.coords(self.selection_rect_id)
            found = self.canvas.find_enclosed(*coords)
            self.selected_items = [self._get_id(it) for it in found if "editable" in self.canvas.gettags(self._get_id(it))]
            self.canvas.delete(self.selection_rect_id)
            self.selection_rect_id = None
            self._draw_highlights()

    def _on_double_click(self, event):
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        item = self.canvas.find_closest(cx, cy)
        item_id = self._get_id(item)
        if item_id and "text_obj" in self.canvas.gettags(item_id):
            txt = self.canvas.itemcget(item_id, "text")
            coords = self.canvas.coords(item_id)
            self.canvas.delete(item_id)
            self._create_text_input(coords[0], coords[1], initial_text=txt)

    def _create_text_input(self, x, y, initial_text=""):
        if self.active_entry_window: return 
        entry = Entry(self.canvas, font=("Arial", int(self.current_font_size)), fg=self.current_color, bd=1, relief="flat")
        if initial_text: entry.insert(0, initial_text)
        entry.focus_set()
        window_id = self.canvas.create_window(x, y, window=entry, anchor=NW)
        self.active_entry_window = window_id
        self._is_finalizing = False 

        def finalize(event=None):
            if not self.canvas.find_withtag(window_id): return
            if self._is_finalizing: return
            self._is_finalizing = True
            content = entry.get().strip()
            self.canvas.delete(window_id)
            self.active_entry_window = None
            if content:
                self.canvas.create_text(x, y, text=content, font=("Arial", self.current_font_size), fill=self.current_color, anchor=NW, tags=("editable", "text_obj"))
            self.after(200, lambda: setattr(self, '_is_finalizing', False))

        entry.bind("<Return>", finalize)
        entry.bind("<FocusOut>", lambda e: self.after(100, finalize))

    def _change_item_size(self, factor):
        for item in self.selected_items:
            item_id = self._get_id(item)
            tags = self.canvas.gettags(item_id)
            if "text_obj" in tags:
                f = tkFont.Font(font=self.canvas.itemcget(item_id, "font"))
                new_size = max(6, int(abs(f.actual("size")) * factor))
                self.canvas.itemconfig(item_id, font=(f.actual("family"), new_size))
            elif "signature" in tags:
                if item_id in self.image_refs:
                    self.image_refs[item_id]["current_w"] *= factor
                    self.image_refs[item_id]["current_h"] *= factor
                    self._refresh_image_item(item_id)
        self._draw_highlights()

    def _add_signature(self, x, y):
        if not self.signature_img_path.exists():
            messagebox.showwarning("Signature", "Importez une signature dans les Paramètres.")
            return
        try:
            orig = Image.open(str(self.signature_img_path)).convert("RGBA")
            display_img = orig.copy()
            display_img.thumbnail((150, 150), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(display_img)
            item_id = self._get_id(self.canvas.create_image(x, y, image=photo, anchor=NW, tags=("editable", "signature")))
            self.image_refs[item_id] = {"photo": photo, "original": orig, "current_w": display_img.width, "current_h": display_img.height}
            self.set_tool("select")
        except Exception as e:
            messagebox.showerror("Erreur", f"Signature : {e}")

    def _refresh_image_item(self, item_id):
        if item_id not in self.image_refs: return
        data = self.image_refs[item_id]
        w, h = max(10, int(data["current_w"])), max(10, int(data["current_h"]))
        resized = data["original"].copy()
        resized.thumbnail((w, h), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(resized)
        self.canvas.itemconfig(item_id, image=photo)
        data["photo"] = photo

    def _draw_highlights(self):
        self.canvas.delete("highlighter")
        for item in self.selected_items:
            bbox = self.canvas.bbox(item)
            if bbox: self.canvas.create_rectangle(bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2, outline="#3498db", width=1, tags="highlighter")

    def _delete_selected(self):
        for item in self.selected_items:
            item_id = self._get_id(item)
            self.canvas.delete(item_id)
            if item_id in self.image_refs: del self.image_refs[item_id]
        self.selected_items = []
        self.canvas.delete("highlighter")

    def _rotate_selected(self):
        for item in self.selected_items:
            item_id = self._get_id(item)
            if "signature" in self.canvas.gettags(item_id):
                if item_id in self.image_refs:
                    data = self.image_refs[item_id]
                    data["original"] = data["original"].rotate(-90, expand=True)
                    data["current_w"], data["current_h"] = data["current_h"], data["current_w"]
                    self._refresh_image_item(item_id)
        self._draw_highlights()

    def set_tool(self, mode):
        self.tool_mode = mode
        self.selected_items = []
        self.canvas.delete("highlighter")
        for m, btn in self.tool_btns.items(): 
            btn.configure(fg_color="#44475a" if m == mode else "transparent")

    def _update_font_settings(self, v): self.current_font_size = int(v)

    def _choose_color(self):
        c = colorchooser.askcolor()[1]
        if c: 
            self.current_color = c
            self.color_btn.configure(fg_color=c)
            for item in self.selected_items:
                self.canvas.itemconfig(self._get_id(item), fill=c)

    def _open_file_dialog(self):
        p = filedialog.askopenfilename(filetypes=[("Documents PDF", "*.pdf")])
        if p: 
            self.pdf_doc = fitz.open(p)
            self.current_page_idx = 0
            self.pages_data = {} 
            self._show_page()

    def _create_btn(self, parent, icon_name, tooltip, command, is_accent=False):
        icon = self._get_edit_icon(icon_name)
        btn = ctk.CTkButton(parent, text="", image=icon, width=32, height=32, fg_color="transparent" if not is_accent else "#6272a4", command=command)
        btn.pack(side="left", padx=2)
        return btn

    def _create_nav_btn(self, parent, icon_name, command):
        icon = self._get_edit_icon(icon_name, size=(14, 14))
        ctk.CTkButton(parent, text="", image=icon, width=28, height=28, fg_color="transparent", command=command).pack(side="left", padx=2)

    def _add_sep(self, parent):
        ctk.CTkFrame(parent, width=2, height=25, fg_color="#44475a").pack(side="left", padx=10)

    def save_changes(self):
        if not self.pdf_doc: return
        self._save_current_page_state() 
        for pg_idx, items in self.pages_data.items():
            page = self.pdf_doc[pg_idx]
            for data in items:
                coords = data["coords"]
                if "text_obj" in data["tags"]:
                    rgb = [int(data["fill"][i:i+2], 16)/255 for i in (1, 3, 5)]
                    page.insert_text((coords[0], coords[1] + data["real_font_size"]), data["text"], fontsize=data["real_font_size"], color=rgb)
                elif "draw_line" in data["tags"]:
                    rgb = [int(data["fill"][i:i+2], 16)/255 for i in (1, 3, 5)]
                    page.draw_line(fitz.Point(coords[0], coords[1]), fitz.Point(coords[2], coords[3]), color=rgb, width=2)
                elif "signature" in data["tags"]:
                    img_buffer = io.BytesIO()
                    data["original_img"].save(img_buffer, format='PNG')
                    rect = fitz.Rect(coords[0], coords[1], coords[0] + data["real_w"], coords[1] + data["real_h"])
                    page.insert_image(rect, stream=img_buffer.getvalue())

        save_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if save_path:
            self.pdf_doc.save(save_path)
            messagebox.showinfo("Succès", "Document enregistré !")