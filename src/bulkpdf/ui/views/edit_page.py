import customtkinter as ctk
import fitz
from PIL import Image, ImageTk
from tkinter import Canvas, filedialog, colorchooser, Entry, Text, Menu, NW, ALL, messagebox
import os
import sys
import io
import tkinter.font as tkFont
from datetime import datetime
from pathlib import Path
from ..i18n import t  # IMPORTATION DE LA LANGUE

def resource_path(relative_path):
    try:
        base_path = Path(sys._MEIPASS)
    except Exception:
        base_path = Path(__file__).parent.parent.parent.parent
    return base_path / relative_path

class EditPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
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
        
        self.current_pdf_selection_rect = None # Rectangle bleu pour sélection de paragraphe
        self.pdf_selection_bbox = None # Coordonnées de la zone de paragraphe
        
        self._is_finalizing = False 
        
        self.current_font_size = 14
        self.current_color = "#000000" 
        self.last_x, self.last_y = 0, 0
        self.image_refs = {} 
        
        self._setup_ui()
        self._setup_bindings()

    def _get_id(self, item):
        if isinstance(item, (tuple, list)):
            return int(item[0]) if item else None
        return int(item) if item is not None else None

    def _get_edit_icon(self, name, size=(18, 18)):
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

        self.toolbar = ctk.CTkFrame(self, height=45, fg_color=("#ffffff", "#2b2b2b"), corner_radius=0)
        self.toolbar.grid(row=0, column=0, sticky="ew")
        self.toolbar.grid_propagate(False)

        container = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        container.pack(side="left", padx=10, fill="y")

        self._create_btn(container, "open", t("btn_open"), self._open_file_dialog)
        self._create_btn(container, "save", t("btn_save"), self.save_changes, is_accent=True)
        self._add_sep(container)

        self.tool_btns = {}
        tools = [("cursor", "select"), ("text", "text"), ("draw", "draw"), ("eraser", "erase"), ("protect", "signature")]
        for icon, mode in tools:
            btn = self._create_btn(container, icon, "", lambda m=mode: self.set_tool(m))
            self.tool_btns[mode] = btn
        
        self._add_sep(container)
        self._create_btn(container, "rotate", t("btn_rotate"), self._rotate_selected)
        self._create_btn(container, "plus", t("btn_enlarge"), lambda: self._change_item_size(1.1))
        self._create_btn(container, "minus", t("btn_shrink"), lambda: self._change_item_size(0.9))
        self._create_btn(container, "trash", t("btn_delete"), self._delete_selected)
        
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
        self.page_label = ctk.CTkLabel(nav_cnt, text=f"{t('page_lbl')} 0 / 0", font=("Arial", 11, "bold"))
        self.page_label.pack(side="left", padx=10)
        self._create_nav_btn(nav_cnt, "right", lambda: self._navigate(1))

        zoom_cnt = ctk.CTkFrame(self.status_bar, fg_color="transparent")
        zoom_cnt.pack(side="right", padx=20)
        self._create_nav_btn(zoom_cnt, "minus", lambda: self._change_zoom(-0.1))
        self.zoom_label = ctk.CTkLabel(zoom_cnt, text=f"{int(self.zoom_level*100)}%", width=50)
        self.zoom_label.pack(side="left")
        self._create_nav_btn(zoom_cnt, "plus", lambda: self._change_zoom(0.1))

    # ---- AMÉLIORATION : Support d'édition Multiligne (Text) ou Monoligne (Entry) ----
    def _create_text_input(self, x, y, initial_text="", font_family=None, font_size=None, box_width=None, box_height=None, is_multiline=False):
        if self.active_entry_window: return 
        
        ff = font_family if font_family else "Arial"
        fs = int(font_size) if font_size else int(self.current_font_size)
        
        self._is_finalizing = False 
        
        def finalize(event=None):
            if not self.canvas.find_withtag(window_id): return
            if self._is_finalizing: return
            self._is_finalizing = True
            
            if is_multiline:
                content = entry.get("1.0", "end-1c").strip()
            else:
                content = entry.get().strip()
                
            self.canvas.delete(window_id)
            self.active_entry_window = None
            if content:
                # Si c'est multiligne, créer un texte qui peut s'afficher sur plusieurs lignes
                self.canvas.create_text(x, y, text=content, font=(ff, fs), fill=self.current_color, anchor=NW, tags=("editable", "text_obj"), angle=0, width=box_width if is_multiline else 0)
            self.after(200, lambda: setattr(self, '_is_finalizing', False))

        if is_multiline:
            entry = Text(self.canvas, font=(ff, fs), fg=self.current_color, bd=0, highlightthickness=1, highlightbackground="#3498db", relief="flat", background="white", wrap="word")
            entry.insert("1.0", initial_text)
            entry.bind("<FocusOut>", lambda e: self.after(100, finalize))
        else:
            entry = Entry(self.canvas, font=(ff, fs), fg=self.current_color, bd=0, highlightthickness=0, relief="flat", background="white")
            if initial_text: entry.insert(0, initial_text)
            entry.bind("<Return>", finalize)
            entry.bind("<FocusOut>", lambda e: self.after(100, finalize))
            
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
        except Exception as e:
            messagebox.showerror(t("error"), str(e))

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
                angle = self.canvas.itemcget(item_id, "angle")
                data.update({
                    "text": self.canvas.itemcget(item_id, "text"),
                    "fill": self.canvas.itemcget(item_id, "fill"),
                    "font_family": f.actual("family"),
                    "real_font_size": abs(f.actual("size")) * ratio,
                    "anchor": self.canvas.itemcget(item_id, "anchor"),
                    "angle": float(angle) if angle else 0.0
                })
            elif "draw_line" in tags:
                data.update({"fill": self.canvas.itemcget(item_id, "fill")})
            elif "redaction" in tags:
                data.update({
                    "fill": self.canvas.itemcget(item_id, "fill"),
                    "outline": self.canvas.itemcget(item_id, "outline")
                })
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
                                       anchor=data["anchor"], tags=data["tags"], 
                                       angle=data.get("angle", 0.0))
            elif "draw_line" in data["tags"]:
                self.canvas.create_line(*scaled_coords, fill=data["fill"], width=2, capstyle="round", tags=data["tags"])
            elif "redaction" in data["tags"]:
                self.canvas.create_rectangle(*scaled_coords, fill=data["fill"], outline=data["outline"], tags=data["tags"])
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
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.tk_img = ImageTk.PhotoImage(img)
        self.canvas.config(width=pix.width, height=pix.height)
        self.canvas.delete(ALL) 
        self.canvas.create_image(0, 0, anchor=NW, image=self.tk_img, tags="background")
        self._load_page_state() 
        self.page_label.configure(text=f"{t('page_lbl')} {self.current_page_idx + 1} / {len(self.pdf_doc)}")
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

    def _setup_bindings(self):
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<Button-3>", self._on_right_click) # Clic droit ajouté

    # ---- AMÉLIORATION : Récupère la police de n'importe quel point ----
    def _get_pdf_font_info(self, page, px, py):
        font_family = "Arial"
        font_size = 14
        color_hex = "#000000"
        
        blocks = page.get_text("dict").get("blocks", [])
        for block in blocks:
            if block.get("type") != 0: continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    bbox = span["bbox"]
                    pad = 3
                    if (bbox[0] - pad) <= px <= (bbox[2] + pad) and (bbox[1] - pad) <= py <= (bbox[3] + pad):
                        font_size = span.get("size", 14)
                        int_color = span.get("color", 0)
                        color_hex = f"#{int_color:06x}"
                        
                        pdf_font_lower = span.get("font", "Helvetica").lower()
                        if "times" in pdf_font_lower: font_family = "Times New Roman"
                        elif "courier" in pdf_font_lower: font_family = "Courier New"
                        elif "calibri" in pdf_font_lower: font_family = "Calibri"
                        elif "cambria" in pdf_font_lower: font_family = "Cambria"
                        else: font_family = "Arial"
                        
                        return font_family, font_size, color_hex
        return font_family, font_size, color_hex

    # ---- AMÉLIORATION : Cible UNIQUEMENT le mot cliqué ----
    def _find_pdf_word_at(self, cx, cy):
        if not self.pdf_doc: return None
        page = self.pdf_doc[self.current_page_idx]
        z = self.zoom_level
        pdf_x, pdf_y = cx / z, cy / z
        
        try:
            words = page.get_text("words")
            clicked_word = None
            for w in words:
                x0, y0, x1, y1, text, bno, lno, wno = w
                pad = 2
                if (x0 - pad) <= pdf_x <= (x1 + pad) and (y0 - pad) <= pdf_y <= (y1 + pad):
                    clicked_word = w
                    break
            
            if not clicked_word: return None
            
            # Récupère la police exacte au centre du mot
            center_x = (clicked_word[0] + clicked_word[2]) / 2
            center_y = (clicked_word[1] + clicked_word[3]) / 2
            
            ff, fs, col = self._get_pdf_font_info(page, center_x, center_y)
            
            return {
                "text": clicked_word[4], 
                "bbox": (clicked_word[0], clicked_word[1], clicked_word[2], clicked_word[3]),
                "font_family": ff,
                "font_size": fs,
                "color": col
            }
        except Exception as e:
            print(f"Erreur d'extraction de mot: {e}")
        return None

    # ---- NOUVEAU : Extrait tous les mots dans un rectangle (pour un paragraphe) ----
    def _find_pdf_text_in_rect(self, pdf_bbox):
        if not self.pdf_doc: return None
        page = self.pdf_doc[self.current_page_idx]
        rx0, ry0, rx1, ry1 = pdf_bbox
        
        words = page.get_text("words")
        selected_words = []
        for w in words:
            wx0, wy0, wx1, wy1, _, _, _, _ = w
            if not (wx1 < rx0 or wx0 > rx1 or wy1 < ry0 or wy0 > ry1):
                selected_words.append(w)
        
        if not selected_words: return None
        
        rect = fitz.Rect(rx0, ry0, rx1, ry1)
        text = page.get_textbox(rect)
        if not text.strip(): return None
        
        # Base la police sur le premier mot sélectionné
        w = selected_words[0]
        center_x, center_y = (w[0]+w[2])/2, (w[1]+w[3])/2
        ff, fs, col = self._get_pdf_font_info(page, center_x, center_y)
        
        min_x = min(wd[0] for wd in selected_words)
        min_y = min(wd[1] for wd in selected_words)
        max_x = max(wd[2] for wd in selected_words)
        max_y = max(wd[3] for wd in selected_words)
        
        return {
            "text": text,
            "bbox": (min_x, min_y, max_x, max_y),
            "font_family": ff,
            "font_size": fs,
            "color": col
        }

    def _on_click(self, event):
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        if self.active_entry_window: return 

        # Si on clique ailleurs, on nettoie le rectangle de paragraphe
        if self.tool_mode == "select":
            if hasattr(self, 'current_pdf_selection_rect') and self.current_pdf_selection_rect:
                self.canvas.delete(self.current_pdf_selection_rect)
                self.current_pdf_selection_rect = None
                self.pdf_selection_bbox = None

            items = self.canvas.find_overlapping(cx-1, cy-1, cx+1, cy+1)
            editable_clicked = [i for i in items if "editable" in self.canvas.gettags(i)]
            if editable_clicked:
                item_id = self._get_id(editable_clicked[-1]) 
                if item_id not in self.selected_items:
                    self.selected_items = [item_id]
                self.drag_data = {"x": cx, "y": cy, "mode": "move"}
            else:
                self.selected_items = []
                self.drag_data = {"x": cx, "y": cy, "mode": "select_box"}
                if self.selection_rect_id:
                    self.canvas.delete(self.selection_rect_id)
                self.selection_rect_id = self.canvas.create_rectangle(cx, cy, cx, cy, outline="#3498db", fill="#3498db", stipple="gray25", dash=(2, 2))
            self._draw_highlights()
            
        elif self.tool_mode == "text": self._create_text_input(cx, cy)
        elif self.tool_mode == "draw": self.last_x, self.last_y = cx, cy
        elif self.tool_mode == "signature": self._add_signature(cx, cy)

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
                
                # S'il n'y a pas d'items d'édition, c'est peut-être une sélection de paragraphe !
                if not self.selected_items and (x2 - x1) > 10 and (y2 - y1) > 10:
                    self.pdf_selection_bbox = (x1, y1, x2, y2)
                    self.current_pdf_selection_rect = self.selection_rect_id 
                    self.selection_rect_id = None # Garde le rectangle affiché
                else:
                    self.canvas.delete(self.selection_rect_id)
                    self.selection_rect_id = None
            self.drag_data["mode"] = None
        self._draw_highlights()

    # ---- NOUVEAU : Clic droit pour ouvrir le menu Paragraphe ----
    def _on_right_click(self, event):
        if self.tool_mode == "select" and self.current_pdf_selection_rect and self.pdf_selection_bbox:
            cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            x1, y1, x2, y2 = self.pdf_selection_bbox
            if x1 <= cx <= x2 and y1 <= cy <= y2:
                menu = Menu(self, tearoff=0)
                menu.add_command(label="Modifier le paragraphe", command=lambda: self._edit_paragraph(self.pdf_selection_bbox))
                menu.tk_popup(event.x_root, event.y_root)

    def _edit_paragraph(self, canvas_bbox):
        # 1. Nettoyer le rectangle bleu
        if self.current_pdf_selection_rect:
            self.canvas.delete(self.current_pdf_selection_rect)
            self.current_pdf_selection_rect = None
        self.pdf_selection_bbox = None
        
        # 2. Convertir et extraire le texte
        z = self.zoom_level
        pdf_bbox = [c / z for c in canvas_bbox]
        data = self._find_pdf_text_in_rect(pdf_bbox)
        
        if data:
            s_bbox = [data["bbox"][0]*z, data["bbox"][1]*z, data["bbox"][2]*z, data["bbox"][3]*z]
            self.current_color = data["color"]
            self.color_btn.configure(fg_color=self.current_color)
            
            pad = 2
            self.canvas.create_rectangle(
                s_bbox[0]-pad, s_bbox[1]-pad, s_bbox[2]+pad, s_bbox[3]+pad,
                fill="white", outline="white", tags=("editable", "redaction")
            )
            
            TK_TO_PDF_RATIO = 1.333
            tk_font_size = max(8, int((data["font_size"] * z) / TK_TO_PDF_RATIO))
            
            box_width = (s_bbox[2] - s_bbox[0]) + 15
            box_height = (s_bbox[3] - s_bbox[1]) + 15
            
            self._create_text_input(
                s_bbox[0], s_bbox[1], 
                initial_text=data["text"],
                font_family=data["font_family"], font_size=tk_font_size,
                box_width=box_width, box_height=box_height,
                is_multiline=True
            )

    def _on_double_click(self, event):
        if self.active_entry_window: return
        if self.tool_mode == "select":
            cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            item = self.canvas.find_closest(cx, cy)
            item_id = self._get_id(item)
            tags = self.canvas.gettags(item_id) if item_id else []
            
            # Modifier ce qu'on a déjà ajouté
            if item_id and "text_obj" in tags:
                current_text = self.canvas.itemcget(item_id, "text")
                coords = self.canvas.coords(item_id)
                self.current_color = self.canvas.itemcget(item_id, "fill")
                self.color_btn.configure(fg_color=self.current_color)
                
                f = tkFont.Font(font=self.canvas.itemcget(item_id, "font"))
                font_family = f.actual("family")
                font_size = abs(f.actual("size"))

                bbox = self.canvas.bbox(item_id)
                box_width = max(80, (bbox[2] - bbox[0]) + 30) if bbox else 150

                self.canvas.delete(item_id)
                if item_id in self.selected_items: self.selected_items.remove(item_id)
                self.canvas.delete("highlighter")
                
                # Check si c'est multiligne basé sur un \n
                is_multi = "\n" in current_text
                self._create_text_input(coords[0], coords[1], initial_text=current_text, font_family=font_family, font_size=font_size, box_width=box_width, is_multiline=is_multi)
                return

            # Modifier UN SEUL MOT du PDF (Style Adobe)
            word_data = self._find_pdf_word_at(cx, cy)
            if word_data:
                bbox = word_data["bbox"] 
                z = self.zoom_level
                scaled_bbox = [bbox[0]*z, bbox[1]*z, bbox[2]*z, bbox[3]*z]
                
                self.current_color = word_data["color"]
                self.color_btn.configure(fg_color=self.current_color)
                
                pad = 1
                self.canvas.create_rectangle(
                    scaled_bbox[0]-pad, scaled_bbox[1]-pad, scaled_bbox[2]+pad, scaled_bbox[3]+pad,
                    fill="white", outline="white", tags=("editable", "redaction")
                )
                
                TK_TO_PDF_RATIO = 1.333
                tk_font_size = max(8, int((word_data["font_size"] * z) / TK_TO_PDF_RATIO))
                box_width = max(50, (scaled_bbox[2] - scaled_bbox[0]) + 15)
                
                self._create_text_input(
                    scaled_bbox[0], 
                    scaled_bbox[1] - 2, 
                    initial_text=word_data["text"],
                    font_family=word_data["font_family"],
                    font_size=tk_font_size,
                    box_width=box_width,
                    is_multiline=False
                )

    def _change_item_size(self, factor):
        for item in self.selected_items:
            item_id = self._get_id(item)
            tags = self.canvas.gettags(item_id)
            if "signature" in tags and item_id in self.image_refs:
                self.image_refs[item_id]["current_w"] *= factor
                self.image_refs[item_id]["current_h"] *= factor
                self._refresh_image_item(item_id)
            elif "text_obj" in tags:
                f = tkFont.Font(font=self.canvas.itemcget(item_id, "font"))
                new_size = max(6, int(abs(f.actual("size")) * factor))
                self.canvas.itemconfig(item_id, font=(f.actual("family"), new_size))
        self._draw_highlights()

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
                current_angle = float(self.canvas.itemcget(item_id, "angle") or 0.0)
                new_angle = (current_angle + 90) % 360
                self.canvas.itemconfig(item_id, angle=new_angle)
        self._draw_highlights()

    def _draw_highlights(self):
        self.canvas.delete("highlighter")
        for item in self.selected_items:
            bbox = self.canvas.bbox(item)
            if bbox: self.canvas.create_rectangle(bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2, outline="#3498db", width=1, tags="highlighter")

    def set_tool(self, mode):
        self.tool_mode = mode
        self.selected_items = []
        self.canvas.delete("highlighter")
        if hasattr(self, 'current_pdf_selection_rect') and self.current_pdf_selection_rect:
            self.canvas.delete(self.current_pdf_selection_rect)
            self.current_pdf_selection_rect = None
        for m, btn in self.tool_btns.items(): 
            btn.configure(fg_color="#44475a" if m == mode else "transparent")

    def _create_btn(self, parent, icon_name, tooltip, command, is_accent=False):
        icon = self._get_edit_icon(icon_name)
        btn = ctk.CTkButton(parent, text=tooltip, image=icon, width=32, height=32, fg_color="transparent" if not is_accent else "#6272a4", command=command)
        btn.pack(side="left", padx=2)
        return btn

    def _create_nav_btn(self, parent, icon_name, command):
        icon = self._get_edit_icon(icon_name, size=(14, 14))
        ctk.CTkButton(parent, text="", image=icon, width=28, height=28, fg_color="transparent", command=command).pack(side="left", padx=2)

    def _add_sep(self, parent):
        ctk.CTkFrame(parent, width=2, height=25, fg_color="#44475a").pack(side="left", padx=10)

    def _update_font_settings(self, v): 
        self.current_font_size = int(v)
        for item in self.selected_items:
            item_id = self._get_id(item)
            if "text_obj" in self.canvas.gettags(item_id):
                f = tkFont.Font(font=self.canvas.itemcget(item_id, "font"))
                self.canvas.itemconfig(item_id, font=(f.actual("family"), self.current_font_size))
    
    def _choose_color(self):
        c = colorchooser.askcolor()[1]
        if c: 
            self.current_color = c
            self.color_btn.configure(fg_color=c)
            for item in self.selected_items:
                item_id = self._get_id(item)
                tags = self.canvas.gettags(item_id)
                if "text_obj" in tags or "draw_line" in tags:
                    self.canvas.itemconfig(item_id, fill=c)

    def _open_file_dialog(self):
        p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if p: 
            self.pdf_path = p
            self.pdf_doc = fitz.open(p)
            self.current_page_idx = 0
            self.pages_data = {}
            self._show_page()

    def save_changes(self):
        if not self.pdf_doc: return
        self._save_current_page_state() 
        for pg_idx, items in self.pages_data.items():
            page = self.pdf_doc[pg_idx]
            for data in items:
                coords = data["coords"]
                if "text_obj" in data["tags"]:
                    TK_TO_PDF_RATIO = 1.333
                    pdf_font_size = data["real_font_size"] * TK_TO_PDF_RATIO
                    
                    hex_color = data["fill"].lstrip('#')
                    rgb = tuple(int(hex_color[i:i+2], 16)/255.0 for i in (0, 2, 4))
                    
                    angle = int(data.get("angle", 0))
                    y_offset = pdf_font_size * 0.75 
                    
                    tk_font = data.get("font_family", "").lower()
                    pdf_font = "helv" 
                    if "times" in tk_font: pdf_font = "ti-ro"
                    elif "courier" in tk_font: pdf_font = "cour"
                    
                    # insert_text supporte le multiline (\n) automatiquement 
                    page.insert_text((coords[0], coords[1] + y_offset), data["text"], fontname=pdf_font, fontsize=pdf_font_size, color=rgb, rotate=angle)
                
                elif "draw_line" in data["tags"]:
                    rgb = [int(data["fill"][i:i+2], 16)/255 for i in (1, 3, 5)]
                    page.draw_line(fitz.Point(coords[0], coords[1]), fitz.Point(coords[2], coords[3]), color=rgb, width=2)
                
                elif "redaction" in data["tags"]:
                    rect = fitz.Rect(coords[0], coords[1], coords[2], coords[3])
                    page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                
                elif "signature" in data["tags"]:
                    img_buffer = io.BytesIO()
                    data["original_img"].save(img_buffer, format='PNG')
                    rect = fitz.Rect(coords[0], coords[1], coords[0] + data["real_w"], coords[1] + data["real_h"])
                    page.insert_image(rect, stream=img_buffer.getvalue())

        orig_name = Path(self.pdf_path).stem if self.pdf_path else "document"
        date_str = datetime.now().strftime("%Y-%m-%d")
        default_name = f"{orig_name}_edited_{date_str}.pdf"

        save_path = filedialog.asksaveasfilename(initialfile=default_name, defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if save_path:
            self.pdf_doc.save(save_path)
            messagebox.showinfo(t("success"), t("doc_saved"))