import customtkinter as ctk
import fitz
from PIL import Image, ImageTk
from tkinter import Canvas, filedialog, colorchooser, Entry, Text, Menu, NW, ALL, messagebox
import os
import sys
import io
import json
import tkinter.font as tkFont
from datetime import datetime
from pathlib import Path
from ..i18n import t  
from ..theme import (BG_COLOR, TOPBAR_COLOR, BORDER_COLOR, TEXT_MAIN, FONT_FAMILY, 
                     CORNER_RADIUS, SCROLLBAR_COLOR, SCROLLBAR_HOVER, SIZE_MAIN)

def resource_path(relative_path):
    try:
        base_path = Path(sys._MEIPASS)
    except Exception:
        base_path = Path(__file__).parent.parent.parent.parent
    return base_path / relative_path

class EditPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.app_data_dir = Path(os.getenv('APPDATA', '.')) / "BulkPDF"
        self.sig_dir = self.app_data_dir / "signatures"
        self.sig_dir.mkdir(parents=True, exist_ok=True) 
        self.signature_img_path = self.sig_dir / "user_signature.png"
        
        self.pdf_doc = None
        self.pdf_path = None
        self.current_page_idx = 0
        self.zoom_level = 1.3
        self.pages_data = {} 
        
        self.tool_mode = "select"
        self.selected_items = []
        self.drag_data = {"x": 0, "y": 0, "mode": None}
        self.active_entry_window = None 
        self.selection_rect_id = None
        
        self.current_pdf_selection_rect = None 
        self.pdf_selection_bbox = None 
        
        self._is_finalizing = False 
        
        self.current_real_font_size = 14.0 
        self.item_real_sizes = {} 
        self.item_original_fonts = {} 
        
        self.current_color = "#000000" 
        self.last_x, self.last_y = 0, 0
        self.image_refs = {} 
        self.current_pil_image = None 
        
        self._load_shortcuts()
        self._setup_ui()
        self._setup_bindings()

    def _load_shortcuts(self):
        self.shortcuts = {
            "select": "v", "text": "t", "draw": "d", "erase": "e", 
            "signature": "p", "pipette": "i", "rotate": "r", 
            "enlarge": "+", "shrink": "-"
        }
        cfg_path = self.app_data_dir / "shortcuts.json"
        if cfg_path.exists():
            try:
                with open(cfg_path, "r") as f:
                    self.shortcuts.update(json.load(f))
            except: pass

    def _get_id(self, item):
        if isinstance(item, (tuple, list)):
            return int(item[0]) if item else None
        return int(item) if item is not None else None

    def _get_edit_icon(self, name, size=(12, 12)):
        try:
            paths = [
                resource_path(os.path.join("src", "assets", "edit", f"{name}.png")),
                resource_path(os.path.join("assets", "edit", f"{name}.png"))
            ]
            for p in paths:
                if p.exists():
                    img_light = Image.open(str(p)).convert("RGBA")
                    r, g, b, a = img_light.split()
                    img_dark = Image.merge("RGBA", (r.point(lambda _: 255), g.point(lambda _: 255), b.point(lambda _: 255), a))
                    return ctk.CTkImage(light_image=img_light, dark_image=img_dark, size=size)
            return None
        except: return None

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.toolbar = ctk.CTkFrame(self, height=38, fg_color=TOPBAR_COLOR, corner_radius=0, border_width=1, border_color=BORDER_COLOR)
        self.toolbar.grid(row=0, column=0, sticky="ew")
        self.toolbar.grid_propagate(False)

        container = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        container.pack(side="left", padx=15, pady=5, fill="y")

        self._create_btn(container, "open", f"{t('btn_open')} (Ctrl+O)", self._open_file_dialog)
        self._create_btn(container, "save", f"{t('btn_save')} (Ctrl+S)", self.save_changes, is_accent=True)
        self._add_sep(container)

        self.tool_btns = {}
        tools = [
            ("cursor", "select", self.shortcuts["select"]), 
            ("text", "text", self.shortcuts["text"]), 
            ("draw", "draw", self.shortcuts["draw"]), 
            ("eraser", "erase", self.shortcuts["erase"]), 
            ("protect", "signature", self.shortcuts["signature"]),
            ("color", "pipette", self.shortcuts["pipette"])
        ]
        for icon, mode, shortcut in tools:
            btn = self._create_btn(container, icon, f"[{shortcut.upper()}]", lambda m=mode: self.set_tool(m))
            self.tool_btns[mode] = btn
        
        self._add_sep(container)
        self._create_btn(container, "rotate", f"({self.shortcuts['rotate'].upper()})", self._rotate_selected)
        self._create_btn(container, "plus", f"({self.shortcuts['enlarge'].upper()})", lambda: self._change_item_size(1.1))
        self._create_btn(container, "minus", f"({self.shortcuts['shrink'].upper()})", lambda: self._change_item_size(0.9))
        self._create_btn(container, "trash", "(Suppr)", self._delete_selected)
        
        self._add_sep(container)
        
        self.font_menu = ctk.CTkComboBox(
            container, values=["Arial", "Helvetica", "Times New Roman", "Courier New", "Calibri", "Cambria"], 
            width=130, height=24, corner_radius=4, border_color=BORDER_COLOR, font=(FONT_FAMILY, SIZE_MAIN), 
            command=self._update_font_family
        )
        self.font_menu.set("Arial")
        self.font_menu.pack(side="left", padx=5)

        self.size_menu = ctk.CTkComboBox(
            container, values=["10", "12", "14", "16", "18", "24", "32", "48", "64"], 
            width=65, height=24, corner_radius=4, border_color=BORDER_COLOR, font=(FONT_FAMILY, SIZE_MAIN), 
            command=self._update_font_size
        )
        self.size_menu.set("14")
        self.size_menu.pack(side="left", padx=5)
        
        self.color_btn = ctk.CTkButton(container, text="", width=20, height=20, fg_color=self.current_color, command=self._choose_color, corner_radius=10)
        self.color_btn.pack(side="left", padx=5)

        self.scroll_canvas = ctk.CTkScrollableFrame(self, fg_color=BG_COLOR, corner_radius=0, scrollbar_button_color=SCROLLBAR_COLOR, scrollbar_button_hover_color=SCROLLBAR_HOVER)
        self.scroll_canvas.grid(row=1, column=0, sticky="nsew")
        self.canvas = Canvas(self.scroll_canvas, bg="white", bd=0, highlightthickness=0)

        self.status_bar = ctk.CTkFrame(self, height=30, fg_color=TOPBAR_COLOR, corner_radius=0, border_width=1, border_color=BORDER_COLOR)
        self.status_bar.grid(row=2, column=0, sticky="ew")
        self.status_bar.grid_propagate(False)
        
        nav_cnt = ctk.CTkFrame(self.status_bar, fg_color="transparent")
        nav_cnt.pack(side="left", padx=15, pady=3)
        self._create_nav_btn(nav_cnt, "left", lambda: self._navigate(-1))
        self.page_label = ctk.CTkLabel(nav_cnt, text=f"{t('page_lbl')} 0 / 0", font=(FONT_FAMILY, SIZE_MAIN, "bold"), text_color=TEXT_MAIN)
        self.page_label.pack(side="left", padx=10)
        self._create_nav_btn(nav_cnt, "right", lambda: self._navigate(1))

        zoom_cnt = ctk.CTkFrame(self.status_bar, fg_color="transparent")
        zoom_cnt.pack(side="right", padx=15, pady=3)
        self._create_nav_btn(zoom_cnt, "minus", lambda: self._change_zoom(-0.1))
        self.zoom_label = ctk.CTkLabel(zoom_cnt, text=f"{int(self.zoom_level*100)}%", width=40, font=(FONT_FAMILY, SIZE_MAIN), text_color=TEXT_MAIN)
        self.zoom_label.pack(side="left")
        self._create_nav_btn(zoom_cnt, "plus", lambda: self._change_zoom(0.1))

    def _create_btn(self, parent, icon_name, tooltip, command, is_accent=False):
        icon = self._get_edit_icon(icon_name)
        text_f = "" if icon else tooltip
        btn = ctk.CTkButton(parent, text=text_f, image=icon, width=24, height=24, corner_radius=4, fg_color="transparent" if not is_accent else "#4a69bd", command=command)
        btn.pack(side="left", padx=2)
        return btn

    def _create_nav_btn(self, parent, icon_name, command):
        icon = self._get_edit_icon(icon_name, size=(12, 12))
        ctk.CTkButton(parent, text="", image=icon, width=22, height=22, corner_radius=4, fg_color="transparent", command=command).pack(side="left", padx=2)

    def _add_sep(self, parent):
        ctk.CTkFrame(parent, width=1, height=16, fg_color=BORDER_COLOR).pack(side="left", padx=8)

    # --- SYNCHRONISATION UI ---
    def _sync_toolbar_with_selection(self):
        if len(self.selected_items) == 1:
            item_id = self.selected_items[0]
            if "text_obj" in self.canvas.gettags(item_id):
                real_size = self.item_real_sizes.get(item_id, 14.0)
                self.current_real_font_size = real_size
                display_val = str(int(real_size)) if real_size.is_integer() else f"{real_size:.1f}"
                self.size_menu.set(display_val)
                
                f = tkFont.Font(font=self.canvas.itemcget(item_id, "font"))
                ff = f.actual("family")
                if ff in self.font_menu._values:
                    self.font_menu.set(ff)
                
                c = self.canvas.itemcget(item_id, "fill")
                self.current_color = c
                self.color_btn.configure(fg_color=c)

    # --- CORRECTION DE LA POLICE PYMUPDF ---
    def _get_pymupdf_font(self, tk_font_name):
        """Convertit n'importe quelle police Tkinter en une des 3 polices sécurisées PyMuPDF (Base-14)"""
        if not tk_font_name: return "helv"
        lower = tk_font_name.lower()
        if "times" in lower or "cambria" in lower: 
            return "tiro" # Times-Roman
        if "courier" in lower or "mono" in lower: 
            return "cour" # Courier
        return "helv" # Helvetica par défaut (Arial, Calibri, etc.)

    def _update_font_family(self, v):
        for item in self.selected_items:
            item_id = self._get_id(item)
            if "text_obj" in self.canvas.gettags(item_id):
                f = tkFont.Font(font=self.canvas.itemcget(item_id, "font"))
                self.canvas.itemconfig(item_id, font=(v, f.actual("size")))
                self.item_original_fonts[item_id] = self._get_pymupdf_font(v)
        self._draw_highlights()

    def _update_font_size(self, v): 
        try:
            self.current_real_font_size = float(v)
            for item in self.selected_items:
                item_id = self._get_id(item)
                if "text_obj" in self.canvas.gettags(item_id):
                    self.item_real_sizes[item_id] = self.current_real_font_size
                    new_tk_size = -max(1, round(self.current_real_font_size * self.zoom_level))
                    f = tkFont.Font(font=self.canvas.itemcget(item_id, "font"))
                    self.canvas.itemconfig(item_id, font=(f.actual("family"), new_tk_size))
            self._draw_highlights()
        except ValueError: pass

    # --- RACCOURCIS CLAVIERS ---
    def _setup_bindings(self):
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<Button-3>", self._on_right_click)

        top = self.winfo_toplevel()
        top.bind("<Key>", self._on_key_press)
        top.bind("<Control-MouseWheel>", lambda e: self._safe_shortcut(lambda: self._change_zoom(0.1 if e.delta > 0 else -0.1)))

    def _safe_shortcut(self, func):
        if not self.winfo_ismapped(): return
        focus = self.focus_get()
        if isinstance(focus, (Entry, Text, ctk.CTkEntry, ctk.CTkComboBox)): return
        if self.active_entry_window is not None: return
        func()

    def _on_key_press(self, event):
        if not self.winfo_ismapped(): return
        focus = self.focus_get()
        if isinstance(focus, (Entry, Text, ctk.CTkEntry, ctk.CTkComboBox)): return
        if self.active_entry_window is not None: return

        char = event.char.lower() if event.char else ""
        keysym = event.keysym.lower()

        if event.state & 0x0004: 
            if keysym == "o": self._open_file_dialog()
            elif keysym == "s": self.save_changes()
            elif keysym in ("plus", "equal", "add", "kp_add"): self._change_zoom(0.1)
            elif keysym in ("minus", "subtract", "kp_subtract"): self._change_zoom(-0.1)
            return

        for action, key in self.shortcuts.items():
            if key.lower() in (char, keysym):
                if action == "select": self.set_tool("select")
                elif action == "text": self.set_tool("text")
                elif action == "draw": self.set_tool("draw")
                elif action == "erase": self.set_tool("erase")
                elif action == "signature": self.set_tool("signature")
                elif action == "pipette": self.set_tool("pipette")
                elif action == "rotate": self._rotate_selected()
                elif action == "enlarge": self._change_item_size(1.1)
                elif action == "shrink": self._change_item_size(0.9)
                return

        if keysym in ("delete", "backspace"):
            self._delete_selected()

    # --- CANVAS ---
    def _create_text_input(self, x, y, initial_text="", font_family=None, real_font_size=None, original_pdf_font=None, box_width=None, box_height=None, is_multiline=False):
        if self.active_entry_window: return 
        
        ff = font_family if font_family else self.font_menu.get()
        fs_real = real_font_size if real_font_size else self.current_real_font_size
        fs_tk = -max(1, round(fs_real * self.zoom_level))
        
        self._is_finalizing = False 
        
        def finalize(event=None):
            # Prévention des erreurs Tkinter si le widget n'existe plus
            if not self.canvas.winfo_exists(): return
            if not self.canvas.find_withtag(window_id): return
            if self._is_finalizing: return
            self._is_finalizing = True
            
            if is_multiline: content = entry.get("1.0", "end-1c").strip()
            else: content = entry.get().strip()
                
            self.canvas.delete(window_id)
            self.active_entry_window = None
            if content:
                item_id = self.canvas.create_text(x, y, text=content, font=(ff, fs_tk), fill=self.current_color, anchor=NW, tags=("editable", "text_obj"), angle=0, width=box_width if is_multiline else 0)
                
                self.item_original_fonts[self._get_id(item_id)] = original_pdf_font or self._get_pymupdf_font(ff)
                self.item_real_sizes[self._get_id(item_id)] = fs_real
                
                self.selected_items = [self._get_id(item_id)]
                self._draw_highlights()
                self._sync_toolbar_with_selection()

            # Utilisation de formattage sûr pour le after
            if self.canvas.winfo_exists():
                self.after(200, lambda: setattr(self, '_is_finalizing', False))

        if is_multiline:
            entry = Text(self.canvas, font=(ff, fs_tk), fg=self.current_color, bd=0, highlightthickness=1, highlightbackground="#3498db", relief="flat", background="white", wrap="word")
            entry.insert("1.0", initial_text)
            entry.bind("<FocusOut>", lambda e: self.after(100, finalize) if self.canvas.winfo_exists() else None)
            entry.bind("<Control-Return>", finalize) 
        else:
            entry = Entry(self.canvas, font=(ff, fs_tk), fg=self.current_color, bd=0, highlightthickness=0, relief="flat", background="white")
            if initial_text: entry.insert(0, initial_text)
            entry.bind("<Return>", finalize)
            entry.bind("<FocusOut>", lambda e: self.after(100, finalize) if self.canvas.winfo_exists() else None)
            
        entry.focus_set()
        
        kwargs = {"window": entry, "anchor": NW}
        if box_width: kwargs["width"] = box_width
        if box_height and is_multiline: kwargs["height"] = box_height
            
        window_id = self.canvas.create_window(x, y, **kwargs)
        self.active_entry_window = window_id

    def _add_signature(self, x, y):
        if not self.signature_img_path.exists():
            p = filedialog.askopenfilename(title=t("load_sig"), filetypes=[("PNG Images", "*.png")])
            if not p: return
            Image.open(p).save(str(self.signature_img_path))

        try:
            orig = Image.open(str(self.signature_img_path)).convert("RGBA")
            w, h = 150, int(150 * (orig.height / orig.width))
            display_img = orig.resize((w, h), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(display_img)
            item_id = self._get_id(self.canvas.create_image(x, y, image=photo, anchor=NW, tags=("editable", "signature")))
            self.image_refs[item_id] = {"photo": photo, "original": orig, "current_w": w, "current_h": h}
            self.set_tool("select")
        except: pass

    def _refresh_image_item(self, item_id):
        if item_id not in self.image_refs: return
        data = self.image_refs[item_id]
        w, h = max(10, int(data["current_w"])), max(10, int(data["current_h"]))
        resized = data["original"].resize((w, h), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(resized)
        self.canvas.itemconfig(item_id, image=photo)
        data["photo"] = photo

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
                real_font_size = self.item_real_sizes.get(item_id, abs(f.actual("size")) * ratio)
                
                data.update({
                    "text": self.canvas.itemcget(item_id, "text"),
                    "fill": self.canvas.itemcget(item_id, "fill"),
                    "font_family": f.actual("family"),
                    "original_pdf_font": self.item_original_fonts.get(item_id, "helv"),
                    "real_font_size": real_font_size,
                    "anchor": self.canvas.itemcget(item_id, "anchor"),
                    "angle": float(self.canvas.itemcget(item_id, "angle") or 0.0)
                })
            elif "draw_line" in tags: data.update({"fill": self.canvas.itemcget(item_id, "fill")})
            elif "redaction" in tags: data.update({"fill": self.canvas.itemcget(item_id, "fill"), "outline": self.canvas.itemcget(item_id, "outline")})
            elif "signature" in tags and item_id in self.image_refs:
                data.update({"original_img": self.image_refs[item_id]["original"], "real_w": self.image_refs[item_id]["current_w"] * ratio, "real_h": self.image_refs[item_id]["current_h"] * ratio})
            current_items.append(data)
        self.pages_data[self.current_page_idx] = current_items

    def _load_page_state(self):
        if self.current_page_idx not in self.pages_data: return
        z = self.zoom_level
        self.image_refs = {} 

        for data in self.pages_data[self.current_page_idx]:
            scaled_coords = [c * z for c in data["coords"]]
            if "text_obj" in data["tags"]:
                real_size = data["real_font_size"]
                display_size = -max(1, round(real_size * z))
                item_id = self.canvas.create_text(*scaled_coords, text=data["text"], fill=data["fill"], font=(data["font_family"], display_size), anchor=data["anchor"], tags=data["tags"], angle=data.get("angle", 0.0))
                
                self.item_original_fonts[self._get_id(item_id)] = data.get("original_pdf_font", "helv")
                self.item_real_sizes[self._get_id(item_id)] = real_size
                
            elif "draw_line" in data["tags"]: self.canvas.create_line(*scaled_coords, fill=data["fill"], width=2, capstyle="round", tags=data["tags"])
            elif "redaction" in data["tags"]: self.canvas.create_rectangle(*scaled_coords, fill=data["fill"], outline=data["outline"], tags=data["tags"])
            elif "signature" in data["tags"]:
                orig = data["original_img"]
                w, h = int(data["real_w"] * z), int(data["real_h"] * z)
                display_img = orig.resize((w, h), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(display_img)
                item_id = self._get_id(self.canvas.create_image(scaled_coords[0], scaled_coords[1], image=photo, anchor=NW, tags=data["tags"]))
                self.image_refs[item_id] = {"photo": photo, "original": orig, "current_w": w, "current_h": h}

    def _show_page(self):
        if not self.pdf_doc: return
        page = self.pdf_doc[self.current_page_idx]
        pix = page.get_pixmap(matrix=fitz.Matrix(self.zoom_level, self.zoom_level))
        
        self.current_pil_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.tk_img = ImageTk.PhotoImage(self.current_pil_image)
        
        self.canvas.config(width=pix.width, height=pix.height)
        
        if not self.canvas.winfo_ismapped():
            self.canvas.pack(pady=30)
            
        self.canvas.delete(ALL) 
        self.canvas.create_image(0, 0, anchor=NW, image=self.tk_img, tags="background")
        self._load_page_state() 
        self.page_label.configure(text=f"{t('page_lbl')} {self.current_page_idx + 1} / {len(self.pdf_doc)}")
        self.selected_items = []
        self._sync_toolbar_with_selection()

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

    def _get_pdf_font_info(self, page, px, py):
        font_family, original_pdf_font, font_size, color_hex = "Arial", "helv", 14.0, "#000000"
        blocks = page.get_text("dict").get("blocks", [])
        for block in blocks:
            if block.get("type") != 0: continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    bbox = span["bbox"]
                    pad = 3
                    if (bbox[0] - pad) <= px <= (bbox[2] + pad) and (bbox[1] - pad) <= py <= (bbox[3] + pad):
                        font_size = float(span.get("size", 14.0))
                        color_hex = f"#{span.get('color', 0):06x}"
                        original_pdf_font = span.get("font", "Helvetica")
                        pdf_font_lower = original_pdf_font.lower()
                        
                        if "times" in pdf_font_lower: font_family = "Times New Roman"
                        elif "courier" in pdf_font_lower: font_family = "Courier New"
                        elif "calibri" in pdf_font_lower: font_family = "Calibri"
                        elif "cambria" in pdf_font_lower: font_family = "Cambria"
                        else: font_family = "Arial"
                        return font_family, original_pdf_font, font_size, color_hex
        return font_family, original_pdf_font, font_size, color_hex

    def _find_pdf_word_at(self, cx, cy):
        if not self.pdf_doc: return None
        page = self.pdf_doc[self.current_page_idx]
        z = self.zoom_level
        pdf_x, pdf_y = cx / z, cy / z
        
        try:
            words = page.get_text("words")
            clicked_word = None
            for w in words:
                pad = 2
                if (w[0] - pad) <= pdf_x <= (w[2] + pad) and (w[1] - pad) <= pdf_y <= (w[3] + pad):
                    clicked_word = w; break
            if not clicked_word: return None
            
            ff, opf, fs, col = self._get_pdf_font_info(page, (clicked_word[0] + clicked_word[2])/2, (clicked_word[1] + clicked_word[3])/2)
            return {"text": clicked_word[4], "bbox": (clicked_word[0], clicked_word[1], clicked_word[2], clicked_word[3]), "font_family": ff, "original_pdf_font": opf, "font_size": fs, "color": col}
        except: return None

    def _find_pdf_text_in_rect(self, pdf_bbox):
        if not self.pdf_doc: return None
        page = self.pdf_doc[self.current_page_idx]
        rx0, ry0, rx1, ry1 = pdf_bbox
        words = page.get_text("words")
        selected_words = [w for w in words if not (w[2] < rx0 or w[0] > rx1 or w[3] < ry0 or w[1] > ry1)]
        if not selected_words: return None
        
        text = page.get_textbox(fitz.Rect(rx0, ry0, rx1, ry1))
        if not text.strip(): return None
        
        ff, opf, fs, col = self._get_pdf_font_info(page, (selected_words[0][0]+selected_words[0][2])/2, (selected_words[0][1]+selected_words[0][3])/2)
        return {"text": text, "bbox": (min(w[0] for w in selected_words), min(w[1] for w in selected_words), max(w[2] for w in selected_words), max(w[3] for w in selected_words)), "font_family": ff, "original_pdf_font": opf, "font_size": fs, "color": col}

    def _on_click(self, event):
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        
        if self.active_entry_window: self.canvas.focus_set(); return 

        if self.tool_mode == "select":
            if hasattr(self, 'current_pdf_selection_rect') and self.current_pdf_selection_rect:
                self.canvas.delete(self.current_pdf_selection_rect); self.current_pdf_selection_rect = None; self.pdf_selection_bbox = None

            items = self.canvas.find_overlapping(cx-1, cy-1, cx+1, cy+1)
            editable_clicked = [i for i in items if "editable" in self.canvas.gettags(i)]
            if editable_clicked:
                item_id = self._get_id(editable_clicked[-1]) 
                if item_id not in self.selected_items: self.selected_items = [item_id]
                self.drag_data = {"x": cx, "y": cy, "mode": "move"}
                self._sync_toolbar_with_selection() 
            else:
                self.selected_items = []
                self.drag_data = {"x": cx, "y": cy, "mode": "select_box"}
                if self.selection_rect_id: self.canvas.delete(self.selection_rect_id)
                self.selection_rect_id = self.canvas.create_rectangle(cx, cy, cx, cy, outline="#3498db", fill="#3498db", stipple="gray25", dash=(2, 2))
            self._draw_highlights()
            
        elif self.tool_mode == "text": self._create_text_input(cx, cy)
        elif self.tool_mode == "draw": self.last_x, self.last_y = cx, cy
        elif self.tool_mode == "signature": self._add_signature(cx, cy)
        elif self.tool_mode == "pipette":
            if self.current_pil_image:
                try:
                    r, g, b = self.current_pil_image.getpixel((int(cx), int(cy)))
                    hex_c = f"#{r:02x}{g:02x}{b:02x}"
                    self.current_color = hex_c
                    self.color_btn.configure(fg_color=hex_c)
                    
                    for item in self.selected_items:
                        tags = self.canvas.gettags(item)
                        if "text_obj" in tags or "draw_line" in tags:
                            self.canvas.itemconfig(item, fill=hex_c)
                    self.set_tool("select")
                except: pass

    def _on_drag(self, event):
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        mode = self.drag_data.get("mode")
        if self.tool_mode == "select":
            if mode == "move" and self.selected_items:
                dx, dy = cx - self.drag_data["x"], cy - self.drag_data["y"]
                for item in self.selected_items: self.canvas.move(item, dx, dy)
                self.drag_data["x"], self.drag_data["y"] = cx, cy
                self._draw_highlights()
            elif mode == "select_box" and self.selection_rect_id:
                self.canvas.coords(self.selection_rect_id, self.drag_data["x"], self.drag_data["y"], cx, cy)
        elif self.tool_mode == "draw":
            self.canvas.create_line(self.last_x, self.last_y, cx, cy, fill=self.current_color, width=2, capstyle="round", tags=("editable", "draw_line"))
            self.last_x, self.last_y = cx, cy
        elif self.tool_mode == "erase":
            for it in self.canvas.find_overlapping(cx-5, cy-5, cx+5, cy+5):
                if "draw_line" in self.canvas.gettags(it): self.canvas.delete(it)

    def _on_release(self, event):
        if self.tool_mode == "select":
            mode = self.drag_data.get("mode")
            if mode == "select_box" and self.selection_rect_id:
                cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
                x1, y1 = min(self.drag_data["x"], cx), min(self.drag_data["y"], cy)
                x2, y2 = max(self.drag_data["x"], cx), max(self.drag_data["y"], cy)
                overlapping = self.canvas.find_overlapping(x1, y1, x2, y2)
                self.selected_items = [self._get_id(i) for i in overlapping if "editable" in self.canvas.gettags(i)]
                
                if not self.selected_items and (x2 - x1) > 10 and (y2 - y1) > 10:
                    self.pdf_selection_bbox = (x1, y1, x2, y2); self.current_pdf_selection_rect = self.selection_rect_id; self.selection_rect_id = None 
                else:
                    self.canvas.delete(self.selection_rect_id); self.selection_rect_id = None
                    self._sync_toolbar_with_selection() 
            self.drag_data["mode"] = None
        self._draw_highlights()

    def _on_right_click(self, event):
        if self.tool_mode == "select" and self.current_pdf_selection_rect and self.pdf_selection_bbox:
            cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            x1, y1, x2, y2 = self.pdf_selection_bbox
            if x1 <= cx <= x2 and y1 <= cy <= y2:
                menu = Menu(self, tearoff=0)
                menu.add_command(label="Modifier le paragraphe", command=lambda: self._edit_paragraph(self.pdf_selection_bbox))
                menu.tk_popup(event.x_root, event.y_root)

    def _edit_paragraph(self, canvas_bbox):
        if self.current_pdf_selection_rect:
            self.canvas.delete(self.current_pdf_selection_rect); self.current_pdf_selection_rect = None
        self.pdf_selection_bbox = None
        
        z = self.zoom_level
        pdf_bbox = [c / z for c in canvas_bbox]
        data = self._find_pdf_text_in_rect(pdf_bbox)
        
        if data:
            s_bbox = [data["bbox"][0]*z, data["bbox"][1]*z, data["bbox"][2]*z, data["bbox"][3]*z]
            self.current_color = data["color"]; self.color_btn.configure(fg_color=self.current_color)
            self.canvas.create_rectangle(s_bbox[0]-2, s_bbox[1]-2, s_bbox[2]+2, s_bbox[3]+2, fill="white", outline="white", tags=("editable", "redaction"))
            self._create_text_input(s_bbox[0], s_bbox[1], initial_text=data["text"], font_family=data["font_family"], real_font_size=data["font_size"], original_pdf_font=data["original_pdf_font"], box_width=(s_bbox[2]-s_bbox[0])+15, box_height=(s_bbox[3]-s_bbox[1])+15, is_multiline=True)

    def _on_double_click(self, event):
        if self.active_entry_window: return
        if self.tool_mode == "select":
            cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            item = self.canvas.find_closest(cx, cy)
            item_id = self._get_id(item)
            tags = self.canvas.gettags(item_id) if item_id else []
            
            if item_id and "text_obj" in tags:
                current_text = self.canvas.itemcget(item_id, "text")
                coords = self.canvas.coords(item_id)
                self.current_color = self.canvas.itemcget(item_id, "fill"); self.color_btn.configure(fg_color=self.current_color)
                
                f = tkFont.Font(font=self.canvas.itemcget(item_id, "font"))
                real_size = self.item_real_sizes.get(item_id, abs(f.actual("size")) / self.zoom_level)

                bbox = self.canvas.bbox(item_id)
                self.canvas.delete(item_id)
                if item_id in self.selected_items: self.selected_items.remove(item_id)
                self.canvas.delete("highlighter")
                
                self._create_text_input(coords[0], coords[1], initial_text=current_text, font_family=f.actual("family"), real_font_size=real_size, original_pdf_font=self.item_original_fonts.get(item_id), box_width=max(80, (bbox[2] - bbox[0]) + 30) if bbox else 150, is_multiline="\n" in current_text)
                return

            word_data = self._find_pdf_word_at(cx, cy)
            if word_data:
                bbox = word_data["bbox"]; z = self.zoom_level; scaled_bbox = [bbox[0]*z, bbox[1]*z, bbox[2]*z, bbox[3]*z]
                self.current_color = word_data["color"]; self.color_btn.configure(fg_color=self.current_color)
                self.canvas.create_rectangle(scaled_bbox[0]-1, scaled_bbox[1]-1, scaled_bbox[2]+1, scaled_bbox[3]+1, fill="white", outline="white", tags=("editable", "redaction"))
                self._create_text_input(scaled_bbox[0], scaled_bbox[1] - 2, initial_text=word_data["text"], font_family=word_data["font_family"], real_font_size=word_data["font_size"], original_pdf_font=word_data["original_pdf_font"], box_width=max(50, (scaled_bbox[2]-scaled_bbox[0])+15), is_multiline=False)

    def _change_item_size(self, factor):
        for item in self.selected_items:
            item_id = self._get_id(item)
            tags = self.canvas.gettags(item_id)
            if "signature" in tags and item_id in self.image_refs:
                self.image_refs[item_id]["current_w"] *= factor; self.image_refs[item_id]["current_h"] *= factor; self._refresh_image_item(item_id)
            elif "text_obj" in tags:
                real_size = self.item_real_sizes.get(item_id, 14.0)
                new_real_size = real_size * factor
                
                old_tk = round(real_size * self.zoom_level)
                new_tk = round(new_real_size * self.zoom_level)
                if old_tk == new_tk:
                    new_real_size += 1.0 if factor > 1 else -1.0
                
                self.item_real_sizes[item_id] = new_real_size
                f = tkFont.Font(font=self.canvas.itemcget(item_id, "font"))
                self.canvas.itemconfig(item_id, font=(f.actual("family"), -max(1, round(new_real_size * self.zoom_level))))
        self._draw_highlights()
        self._sync_toolbar_with_selection() 

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
            tags = self.canvas.gettags(item_id)
            if "signature" in tags and item_id in self.image_refs:
                data = self.image_refs[item_id]
                data["original"] = data["original"].rotate(-90, expand=True)
                data["current_w"], data["current_h"] = data["current_h"], data["current_w"]
                self._refresh_image_item(item_id)
            elif "text_obj" in tags:
                self.canvas.itemconfig(item_id, angle=(float(self.canvas.itemcget(item_id, "angle") or 0.0) + 90) % 360)
        self._draw_highlights()

    def _draw_highlights(self):
        self.canvas.delete("highlighter")
        for item in self.selected_items:
            bbox = self.canvas.bbox(item)
            if bbox: self.canvas.create_rectangle(bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2, outline="#3498db", width=1, tags="highlighter")

    def set_tool(self, mode):
        if self.active_entry_window: self.canvas.focus_set()
        self.tool_mode = mode
        self.selected_items = []
        self.canvas.delete("highlighter")
        if hasattr(self, 'current_pdf_selection_rect') and self.current_pdf_selection_rect:
            self.canvas.delete(self.current_pdf_selection_rect); self.current_pdf_selection_rect = None
        for m, btn in self.tool_btns.items(): btn.configure(fg_color="#44475a" if m == mode else "transparent")
    
    def _choose_color(self):
        c = colorchooser.askcolor()[1]
        if c: 
            self.current_color = c; self.color_btn.configure(fg_color=c)
            for item in self.selected_items:
                item_id = self._get_id(item)
                tags = self.canvas.gettags(item_id)
                if "text_obj" in tags or "draw_line" in tags: self.canvas.itemconfig(item_id, fill=c)

    def _open_file_dialog(self):
        p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if p: 
            self.pdf_path = p; self.pdf_doc = fitz.open(p); self.current_page_idx = 0; self.pages_data = {}; self.item_original_fonts = {}; self.item_real_sizes = {}
            self._show_page()

    def save_changes(self):
        if not self.pdf_doc: return
        if self.active_entry_window: self.canvas.focus_set()
        
        self._save_current_page_state() 
        for pg_idx, items in self.pages_data.items():
            page = self.pdf_doc[pg_idx]
            for data in items:
                coords = data["coords"]
                if "text_obj" in data["tags"]:
                    pdf_font_size = data["real_font_size"]
                    hex_color = data["fill"].lstrip('#')
                    rgb = tuple(int(hex_color[i:i+2], 16)/255.0 for i in (0, 2, 4))
                    angle = int(data.get("angle", 0))
                    
                    # Le secret de la stabilité : On map la police Tkinter à la police PyMuPDF universelle
                    pdf_font = self._get_pymupdf_font(data.get("font_family", "Arial"))
                    
                    page.insert_text((coords[0], coords[1] + (pdf_font_size * 0.75)), data["text"], fontname=pdf_font, fontsize=pdf_font_size, color=rgb, rotate=angle)
                
                elif "draw_line" in data["tags"]: page.draw_line(fitz.Point(coords[0], coords[1]), fitz.Point(coords[2], coords[3]), color=[int(data["fill"][i:i+2], 16)/255 for i in (1, 3, 5)], width=2)
                elif "redaction" in data["tags"]: page.draw_rect(fitz.Rect(coords[0], coords[1], coords[2], coords[3]), color=(1, 1, 1), fill=(1, 1, 1))
                elif "signature" in data["tags"]:
                    img_buffer = io.BytesIO()
                    data["original_img"].save(img_buffer, format='PNG')
                    page.insert_image(fitz.Rect(coords[0], coords[1], coords[0] + data["real_w"], coords[1] + data["real_h"]), stream=img_buffer.getvalue())

        orig_name = Path(self.pdf_path).stem if self.pdf_path else "document"
        save_path = filedialog.asksaveasfilename(initialfile=f"{orig_name}_edited_{datetime.now().strftime('%Y-%m-%d')}.pdf", defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if save_path:
            self.pdf_doc.save(save_path)
            messagebox.showinfo(t("success"), t("doc_saved"))