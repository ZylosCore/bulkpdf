import customtkinter as ctk
import fitz
from PIL import Image, ImageTk
from tkinter import Canvas, filedialog, colorchooser, Entry, Text, Menu, NW, ALL, messagebox
import tkinter as tk
import os
import sys
import io
import json
import tkinter.font as tkFont
import uuid
from datetime import datetime
from pathlib import Path
from ..i18n import t  
from ..theme import (BG_COLOR, CARD_COLOR, TOPBAR_COLOR, BORDER_COLOR, TEXT_MAIN, FONT_FAMILY, 
                     CORNER_RADIUS, SIZE_MAIN, ACCENT_PRIMARY)

def resource_path(relative_path):
    try:
        base_path = Path(sys._MEIPASS) # type: ignore
    except Exception:
        base_path = Path(__file__).parent.parent.parent.parent
    return base_path / relative_path

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tw = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)

    def enter(self, event=None):
        if not self.text or not self.widget.winfo_exists(): return
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 25
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tw, text=self.text, justify='left',
                         background="#2b2b2b", foreground="white", relief='flat', borderwidth=0,
                         font=(FONT_FAMILY, 9, "normal"), padx=6, pady=3)
        label.pack()

    def leave(self, event=None):
        if self.tw:
            self.tw.destroy()
            self.tw = None

# ==========================================
# CLASSE DE L'ONGLET (PDF INDÉPENDANT)
# ==========================================
class PdfEditorTab(ctk.CTkFrame):
    def __init__(self, master, pdf_path, main_page, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.main_page = main_page 
        self.pdf_path = pdf_path
        
        self.pdf_doc = fitz.open(pdf_path)
        
        if self.pdf_doc.needs_pass:
            dialog = ctk.CTkInputDialog(text="Ce document est protégé. Entrez le mot de passe :", title="PDF Verrouillé")
            pwd = dialog.get_input()
            if not pwd or self.pdf_doc.authenticate(pwd) <= 0:
                self.pdf_doc.close()
                raise ValueError("Encrypted")
                
        self.current_page_idx = 0
        self.zoom_level = 1.3 # Zoom par défaut un peu plus "HD"
        self.pages_data = {} 
        
        # Historique (Undo/Redo)
        self.history = []
        self.redo_stack = []
        self.pre_drag_state = None
        
        self.selected_items = []
        self.item_groups = {} # Grouping: item_id -> group_id
        
        self.drag_data = {"x": 0, "y": 0, "mode": None, "item": None, "moved": False}
        self.active_entry_window = None 
        self.selection_rect_id = None
        self.current_pdf_selection_rect = None 
        self.pdf_selection_bbox = None 
        self._is_finalizing = False 
        
        self.item_real_sizes = {} 
        self.item_original_fonts = {} 
        self.image_refs = {} 
        self.current_pil_image = None 
        self.is_modified = False 
        
        self.thumbnail_buttons = [] 
        
        self._setup_ui()
        self._load_thumbnails_async() 
        self._setup_bindings()
        self._show_page()

    def _get_id(self, item):
        if isinstance(item, (tuple, list)): return int(item[0]) if item else None
        return int(item) if item is not None else None

    # --- SYSTEME DE GROUPEMENT ---
    def group_selected(self):
        if len(self.selected_items) < 2: return
        self.push_history()
        group_id = str(uuid.uuid4())
        for item in self.selected_items:
            self.item_groups[item] = group_id
        self._draw_highlights()

    def ungroup_selected(self):
        if not self.selected_items: return
        self.push_history()
        for item in self.selected_items:
            if item in self.item_groups:
                del self.item_groups[item]
        self._draw_highlights()

    def _expand_selection_to_groups(self):
        # Si un élément d'un groupe est sélectionné, sélectionner tout le groupe
        new_selection = set(self.selected_items)
        groups_to_add = {self.item_groups[i] for i in self.selected_items if i in self.item_groups}
        
        for item_id, g_id in self.item_groups.items():
            if g_id in groups_to_add:
                new_selection.add(item_id)
                
        self.selected_items = list(new_selection)

    # --- SYSTEME UNDO / REDO ---
    def _copy_state(self, state_list):
        new_state = []
        for item in state_list:
            new_item = item.copy()
            if "coords" in new_item:
                new_item["coords"] = item["coords"].copy()
            new_state.append(new_item)
        return new_state

    def push_history(self):
        self._save_current_page_state()
        state = {
            "items": self._copy_state(self.pages_data.get(self.current_page_idx, [])),
            "groups": self.item_groups.copy()
        }
        self.history.append(state)
        if len(self.history) > 30: 
            self.history.pop(0)
        self.redo_stack.clear()
        self.is_modified = True

    def undo(self):
        if not self.history: return
        self._save_current_page_state()
        current_state = {
            "items": self._copy_state(self.pages_data.get(self.current_page_idx, [])),
            "groups": self.item_groups.copy()
        }
        self.redo_stack.append(current_state)
        
        state = self.history.pop()
        self.pages_data[self.current_page_idx] = state["items"]
        self.item_groups = state.get("groups", {})
        
        for item in self.canvas.find_withtag("editable"):
            self.canvas.delete(item)
            
        self._load_page_state()
        self.selected_items = []
        self.canvas.delete("highlighter")
        self.canvas.delete("handle")
        self.main_page._sync_toolbar_with_selection()

    def redo(self):
        if not self.redo_stack: return
        self._save_current_page_state()
        current_state = {
            "items": self._copy_state(self.pages_data.get(self.current_page_idx, [])),
            "groups": self.item_groups.copy()
        }
        self.history.append(current_state)
        
        state = self.redo_stack.pop()
        self.pages_data[self.current_page_idx] = state["items"]
        self.item_groups = state.get("groups", {})
        
        for item in self.canvas.find_withtag("editable"):
            self.canvas.delete(item)
            
        self._load_page_state()
        self.selected_items = []
        self.canvas.delete("highlighter")
        self.canvas.delete("handle")
        self.main_page._sync_toolbar_with_selection()

    # --- UI DU CANVA ---
    def _setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar_frame = ctk.CTkScrollableFrame(self, width=180, fg_color=CARD_COLOR, border_width=0, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        
        self.scroll_canvas = ctk.CTkScrollableFrame(self, fg_color=BG_COLOR, corner_radius=0)
        self.scroll_canvas.grid(row=0, column=1, sticky="nsew")
        self.canvas = Canvas(self.scroll_canvas, bg="white", bd=0, highlightthickness=0)

        self.status_bar = ctk.CTkFrame(self, height=30, fg_color=TOPBAR_COLOR, corner_radius=0, border_width=1, border_color=BORDER_COLOR)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.status_bar.grid_propagate(False)
        
        nav_cnt = ctk.CTkFrame(self.status_bar, fg_color="transparent")
        nav_cnt.pack(side="left", padx=15, pady=3)
        self._create_nav_btn(nav_cnt, "left", lambda: self._navigate(-1), "◀")
        self.page_label = ctk.CTkLabel(nav_cnt, text=f"{t('page_lbl')} 1 / {len(self.pdf_doc)}", font=(FONT_FAMILY, SIZE_MAIN, "bold"), text_color=TEXT_MAIN)
        self.page_label.pack(side="left", padx=10)
        self._create_nav_btn(nav_cnt, "right", lambda: self._navigate(1), "▶")

        zoom_cnt = ctk.CTkFrame(self.status_bar, fg_color="transparent")
        zoom_cnt.pack(side="right", padx=15, pady=3)
        self._create_nav_btn(zoom_cnt, "minus", lambda: self._change_zoom(-0.1), "-")
        self.zoom_label = ctk.CTkLabel(zoom_cnt, text=f"{int(self.zoom_level*100)}%", width=40, font=(FONT_FAMILY, SIZE_MAIN), text_color=TEXT_MAIN)
        self.zoom_label.pack(side="left")
        self._create_nav_btn(zoom_cnt, "plus", lambda: self._change_zoom(0.1), "+")

    def _create_nav_btn(self, parent, icon_name, command, fallback=""):
        icon = self.main_page._get_edit_icon(icon_name, size=(12, 12))
        btn = ctk.CTkButton(parent, text="" if icon else fallback, image=icon, width=24, height=24, corner_radius=4, fg_color="transparent", text_color=TEXT_MAIN, command=command)
        btn.pack(side="left", padx=2)

    def _load_thumbnails_async(self):
        for i in range(len(self.pdf_doc)):
            page = self.pdf_doc[i]
            pix = page.get_pixmap(matrix=fitz.Matrix(0.2, 0.2)) # Qualité des miniatures légèrement augmentée
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples) # type: ignore
            photo = ctk.CTkImage(light_image=img, dark_image=img, size=(pix.width, pix.height))
            
            btn_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
            btn_frame.pack(pady=8, padx=10, fill="x")
            
            btn = ctk.CTkButton(
                btn_frame, image=photo, text="", fg_color="transparent", 
                hover_color=BORDER_COLOR, border_width=2, border_color=CARD_COLOR,
                command=lambda idx=i: self.goto_page(idx)
            )
            btn.pack(pady=(0, 5))
            
            lbl = ctk.CTkLabel(btn_frame, text=str(i+1), font=(FONT_FAMILY, 10))
            lbl.pack()
            self.thumbnail_buttons.append(btn)

    def _update_thumbnail_highlight(self):
        for i, btn in enumerate(self.thumbnail_buttons):
            btn.configure(border_color=ACCENT_PRIMARY if i == self.current_page_idx else CARD_COLOR)

    def goto_page(self, page_index):
        if 0 <= page_index < len(self.pdf_doc) and page_index != self.current_page_idx:
            self._save_current_page_state()
            self.current_page_idx = page_index
            self._show_page()

    def _setup_bindings(self):
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<Button-3>", self._on_right_click)

    def _show_page(self):
        page = self.pdf_doc[self.current_page_idx]
        pix = page.get_pixmap(matrix=fitz.Matrix(self.zoom_level, self.zoom_level))
        self.current_pil_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples) # type: ignore
        self.tk_img = ImageTk.PhotoImage(self.current_pil_image)
        self.canvas.config(width=pix.width, height=pix.height)
        if not self.canvas.winfo_ismapped(): self.canvas.pack(pady=30)
        self.canvas.delete(ALL) 
        self.canvas.create_image(0, 0, anchor=NW, image=self.tk_img, tags="background")
        self._load_page_state() 
        self.page_label.configure(text=f"{t('page_lbl')} {self.current_page_idx + 1} / {len(self.pdf_doc)}")
        self.selected_items = []
        self._update_thumbnail_highlight()
        self.main_page._sync_toolbar_with_selection()

    def _navigate(self, delta):
        self.goto_page(self.current_page_idx + delta)

    def _change_zoom(self, delta):
        self._save_current_page_state()
        self.zoom_level = max(0.3, min(4.0, self.zoom_level + delta))
        self.zoom_label.configure(text=f"{int(self.zoom_level*100)}%")
        self._show_page()

    def _add_signature(self, x, y):
        if not self.main_page.signature_img_path.exists():
            p = filedialog.askopenfilename(title=t("load_sig"), filetypes=[("PNG Images", "*.png")])
            if not p: return
            Image.open(p).save(str(self.main_page.signature_img_path))
        try:
            orig = Image.open(str(self.main_page.signature_img_path)).convert("RGBA")
            w, h = 150, int(150 * (orig.height / orig.width))
            display_img = orig.resize((w, h), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(display_img)
            
            self.push_history() 
            item_id = self._get_id(self.canvas.create_image(x, y, image=photo, anchor=NW, tags=("editable", "signature")))
            self.image_refs[item_id] = {"photo": photo, "original": orig, "current_w": w, "current_h": h}
            self.selected_items = [item_id]
            self._draw_highlights()
            self.main_page.set_tool("select")
        except: pass

    def _refresh_image_item(self, item_id):
        if item_id not in self.image_refs: return
        data = self.image_refs[item_id]
        w, h = max(10, int(data["current_w"])), max(10, int(data["current_h"]))
        resized = data["original"].resize((w, h), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(resized)
        self.canvas.itemconfig(item_id, image=photo)
        data["photo"] = photo

    # --- ACTIONS SOURIS AVEC RESIZE AMÉLIORÉ ---
    def _on_click(self, event):
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        if self.active_entry_window: self.canvas.focus_set(); return 

        mode = self.main_page.tool_mode
        self.drag_data["moved"] = False 
        
        if mode == "pan":
            self.canvas.scan_mark(event.x, event.y)
            return

        if self.main_page.mode_switch.get() == "View": return

        if mode == "select":
            # 1. Check if clicking on a resize handle
            items = self.canvas.find_overlapping(cx-4, cy-4, cx+4, cy+4)
            handles = [i for i in items if "handle" in self.canvas.gettags(i)]
            
            if handles:
                handle_id = handles[-1]
                tags = self.canvas.gettags(handle_id)
                for tag in tags:
                    if tag.startswith("resize_"):
                        target_item = int(tag.split("_")[1])
                        self.pre_drag_state = self._copy_state(self.pages_data.get(self.current_page_idx, []))
                        # Sauvegarde des largeurs initiales pour le calcul du delta
                        initial_w = self.canvas.itemcget(target_item, "width") if "text_obj" in self.canvas.gettags(target_item) else self.image_refs.get(target_item, {}).get("current_w", 0)
                        self.drag_data = {"x": cx, "y": cy, "mode": "resize", "item": target_item, "moved": False, "initial_w": float(initial_w) if initial_w else 0, "initial_x": cx}
                        return

            if self.current_pdf_selection_rect:
                self.canvas.delete(self.current_pdf_selection_rect); self.current_pdf_selection_rect = None; self.pdf_selection_bbox = None

            # 2. Check if clicking on an editable item
            editable_clicked = [i for i in items if "editable" in self.canvas.gettags(i)]
            
            if editable_clicked:
                item_id = self._get_id(editable_clicked[-1])
                
                # Maj-Clic pour ajouter à la sélection (Multiple Selection)
                if event.state & 0x0001: 
                    if item_id in self.selected_items:
                        self.selected_items.remove(item_id)
                    else:
                        self.selected_items.append(item_id)
                else:
                    if item_id not in self.selected_items:
                        self.selected_items = [item_id]
                
                self._expand_selection_to_groups()
                
                self.pre_drag_state = self._copy_state(self.pages_data.get(self.current_page_idx, []))
                self.drag_data = {"x": cx, "y": cy, "mode": "move", "item": item_id, "moved": False}
                self.main_page._sync_toolbar_with_selection() 
            else:
                self.selected_items = []
                self.drag_data = {"x": cx, "y": cy, "mode": "select_box", "item": None, "moved": False}
                if self.selection_rect_id: self.canvas.delete(self.selection_rect_id)
                self.selection_rect_id = self.canvas.create_rectangle(cx, cy, cx, cy, outline="#3498db", fill="#3498db", stipple="gray25", dash=(2, 2))
            self._draw_highlights()
            
        elif mode == "text": self._create_text_input(cx, cy)
        elif mode == "draw": 
            self.push_history()
            self.main_page.last_x, self.main_page.last_y = cx, cy
        elif mode == "signature": self._add_signature(cx, cy)
        elif mode == "erase":
            self.push_history()
        elif mode == "pipette":
            if self.current_pil_image:
                try:
                    r, g, b = self.current_pil_image.getpixel((int(cx), int(cy))) # type: ignore
                    hex_c = f"#{r:02x}{g:02x}{b:02x}"
                    self.main_page.current_color = hex_c
                    self.main_page.color_btn.configure(fg_color=hex_c)
                    
                    if self.selected_items:
                        self.push_history()
                        for item in self.selected_items:
                            tags = self.canvas.gettags(item) # type: ignore
                            if "text_obj" in tags or "draw_line" in tags:
                                self.canvas.itemconfig(item, fill=hex_c) # type: ignore
                    self.main_page.set_tool("select")
                except: pass

    def _on_drag(self, event):
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        if self.main_page.tool_mode == "pan":
            self.canvas.scan_dragto(event.x, event.y, gain=1)
            return

        if self.main_page.mode_switch.get() == "View": return

        mode = self.drag_data.get("mode")
        if self.main_page.tool_mode == "select":
            # --- DÉFORMATION RÉPARÉE (Word-Wrap & Resize fluide) ---
            if mode == "resize":
                self.drag_data["moved"] = True
                target = self.drag_data["item"]
                tags = self.canvas.gettags(target)
                
                dx = cx - self.drag_data["initial_x"]
                
                if "text_obj" in tags:
                    new_width = max(50, self.drag_data["initial_w"] + dx)
                    self.canvas.itemconfig(target, width=new_width) 
                    self._draw_highlights() 
                    
                elif "signature" in tags and target in self.image_refs:
                    coords = self.canvas.coords(target)
                    new_w = max(20, cx - coords[0])
                    new_h = max(20, cy - coords[1])
                    self.image_refs[target]["current_w"] = new_w
                    self.image_refs[target]["current_h"] = new_h
                    self._refresh_image_item(target)
                    self._draw_highlights()

            elif mode == "move" and self.selected_items:
                self.drag_data["moved"] = True
                dx, dy = cx - self.drag_data["x"], cy - self.drag_data["y"]
                for item in self.selected_items: self.canvas.move(item, dx, dy)
                self.drag_data["x"], self.drag_data["y"] = cx, cy
                self._draw_highlights()
                
            elif mode == "select_box" and self.selection_rect_id:
                self.canvas.coords(self.selection_rect_id, self.drag_data["x"], self.drag_data["y"], cx, cy)
                
        elif self.main_page.tool_mode == "draw":
            self.canvas.create_line(self.main_page.last_x, self.main_page.last_y, cx, cy, fill=self.main_page.current_color, width=2, capstyle="round", tags=("editable", "draw_line"))
            self.main_page.last_x, self.main_page.last_y = cx, cy
            self.is_modified = True
        elif self.main_page.tool_mode == "erase":
            for it in self.canvas.find_overlapping(cx-5, cy-5, cx+5, cy+5):
                if "draw_line" in self.canvas.gettags(it): 
                    self.canvas.delete(it)
                    self.is_modified = True

    def _on_release(self, event):
        if self.main_page.mode_switch.get() == "View": return
        
        if self.drag_data.get("moved") and self.drag_data.get("mode") in ("move", "resize"):
            if self.pre_drag_state is not None:
                self.history.append({"items": self.pre_drag_state, "groups": self.item_groups.copy()})
                self.redo_stack.clear()
                self.is_modified = True

        if self.main_page.tool_mode == "select":
            mode = self.drag_data.get("mode")
            if mode == "select_box" and self.selection_rect_id:
                cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
                x1, y1 = min(self.drag_data["x"], cx), min(self.drag_data["y"], cy)
                x2, y2 = max(self.drag_data["x"], cx), max(self.drag_data["y"], cy)
                overlapping = self.canvas.find_overlapping(x1, y1, x2, y2)
                self.selected_items = [self._get_id(i) for i in overlapping if "editable" in self.canvas.gettags(i)]
                
                self._expand_selection_to_groups()
                
                if not self.selected_items and (x2 - x1) > 10 and (y2 - y1) > 10:
                    self.pdf_selection_bbox = (x1, y1, x2, y2); self.current_pdf_selection_rect = self.selection_rect_id; self.selection_rect_id = None 
                else:
                    self.canvas.delete(self.selection_rect_id); self.selection_rect_id = None
                    self.main_page._sync_toolbar_with_selection() 
                    
            self.drag_data["mode"] = None
            self.drag_data["item"] = None
            self.drag_data["moved"] = False
            
        self._draw_highlights()

    def _on_right_click(self, event):
        if self.main_page.mode_switch.get() == "View": return
        if self.main_page.tool_mode == "select" and self.current_pdf_selection_rect and self.pdf_selection_bbox:
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
            self.push_history() 
            s_bbox = [data["bbox"][0]*z, data["bbox"][1]*z, data["bbox"][2]*z, data["bbox"][3]*z]
            self.main_page.current_color = data["color"]; self.main_page.color_btn.configure(fg_color=self.main_page.current_color)
            self.canvas.create_rectangle(s_bbox[0]-2, s_bbox[1]-2, s_bbox[2]+2, s_bbox[3]+2, fill="white", outline="white", tags=("editable", "redaction"))
            self._create_text_input(s_bbox[0], s_bbox[1], initial_text=data["text"], font_family=data["font_family"], real_font_size=data["font_size"], original_pdf_font=data["original_pdf_font"], box_width=(s_bbox[2]-s_bbox[0])+15, box_height=(s_bbox[3]-s_bbox[1])+15, is_multiline=True)

    def _on_double_click(self, event):
        if self.main_page.mode_switch.get() == "View": return
        if self.active_entry_window: return
        if self.main_page.tool_mode == "select":
            cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            item = self.canvas.find_closest(cx, cy)
            item_id = self._get_id(item)
            tags = self.canvas.gettags(item_id) if item_id else []
            
            if item_id and "text_obj" in tags:
                self.push_history()
                current_text = self.canvas.itemcget(item_id, "text")
                coords = self.canvas.coords(item_id)
                self.main_page.current_color = self.canvas.itemcget(item_id, "fill"); self.main_page.color_btn.configure(fg_color=self.main_page.current_color)
                
                f = tkFont.Font(font=self.canvas.itemcget(item_id, "font"))
                real_size = self.item_real_sizes.get(item_id, abs(f.actual("size")) / self.zoom_level)

                bbox = self.canvas.bbox(item_id)
                self.canvas.delete(item_id)
                if item_id in self.selected_items: self.selected_items.remove(item_id)
                self.canvas.delete("highlighter")
                self.canvas.delete("handle")
                
                self._create_text_input(coords[0], coords[1], initial_text=current_text, font_family=f.actual("family"), real_font_size=real_size, original_pdf_font=self.item_original_fonts.get(item_id), box_width=max(80, (bbox[2] - bbox[0]) + 30) if bbox else 150, is_multiline="\n" in current_text)
                return

            word_data = self._find_pdf_word_at(cx, cy)
            if word_data:
                self.push_history()
                bbox = word_data["bbox"]; z = self.zoom_level; scaled_bbox = [bbox[0]*z, bbox[1]*z, bbox[2]*z, bbox[3]*z]
                self.main_page.current_color = word_data["color"]; self.main_page.color_btn.configure(fg_color=self.main_page.current_color)
                self.canvas.create_rectangle(scaled_bbox[0]-1, scaled_bbox[1]-1, scaled_bbox[2]+1, scaled_bbox[3]+1, fill="white", outline="white", tags=("editable", "redaction"))
                self._create_text_input(scaled_bbox[0], scaled_bbox[1] - 2, initial_text=word_data["text"], font_family=word_data["font_family"], real_font_size=word_data["font_size"], original_pdf_font=word_data["original_pdf_font"], box_width=max(50, (scaled_bbox[2]-scaled_bbox[0])+15), is_multiline=False)

    def _draw_highlights(self):
        self.canvas.delete("highlighter")
        self.canvas.delete("handle") 
        
        if not self.selected_items: return
        
        # Draw Group Highlight Box
        if len(self.selected_items) > 1:
            all_bboxes = [self.canvas.bbox(item) for item in self.selected_items if self.canvas.bbox(item)]
            if all_bboxes:
                min_x = min(b[0] for b in all_bboxes)
                min_y = min(b[1] for b in all_bboxes)
                max_x = max(b[2] for b in all_bboxes)
                max_y = max(b[3] for b in all_bboxes)
                self.canvas.create_rectangle(min_x-4, min_y-4, max_x+4, max_y+4, outline=ACCENT_PRIMARY, width=1, dash=(4, 4), tags="highlighter")
        
        # Draw individual highlights and handles
        for item in self.selected_items:
            bbox = self.canvas.bbox(item)
            if bbox: 
                self.canvas.create_rectangle(bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2, outline="#3498db", width=1, tags="highlighter")
                
                # NOUVEAU : Poignée de déformation (Seulement si 1 élément sélectionné pour éviter le conflit)
                if len(self.selected_items) == 1:
                    tags = self.canvas.gettags(item)
                    if "text_obj" in tags or "signature" in tags:
                        hx0, hy0 = bbox[2]-4, bbox[3]-4
                        hx1, hy1 = bbox[2]+5, bbox[3]+5
                        self.canvas.create_rectangle(hx0, hy0, hx1, hy1, fill="#FFFFFF", outline="#3498db", width=1.5, tags=("handle", f"resize_{item}"))

    def _create_text_input(self, x, y, initial_text="", font_family=None, real_font_size=None, original_pdf_font=None, box_width=None, box_height=None, is_multiline=False):
        if self.active_entry_window: return 
        
        ff = font_family if font_family else self.main_page.font_menu.get()
        fs_real = real_font_size if real_font_size else self.main_page.current_real_font_size
        fs_tk = -max(1, round(fs_real * self.zoom_level))
        
        self._is_finalizing = False 
        
        def finalize(event=None):
            if not self.canvas.winfo_exists(): return
            if not self.canvas.find_withtag(window_id): return
            if self._is_finalizing: return
            self._is_finalizing = True
            
            if is_multiline: content = entry.get("1.0", "end-1c").strip() # type: ignore
            else: content = entry.get().strip() # type: ignore
                
            self.canvas.delete(window_id)
            self.active_entry_window = None
            if content:
                self.push_history()
                current_weight = "bold" if self.main_page.btn_bold.cget("fg_color") != "transparent" else "normal"
                current_slant = "italic" if self.main_page.btn_italic.cget("fg_color") != "transparent" else "roman"
                current_underline = 1 if self.main_page.btn_underline.cget("fg_color") != "transparent" else 0
                
                font_tuple = tkFont.Font(family=ff, size=fs_tk, weight=current_weight, slant=current_slant, underline=current_underline)

                item_id = self.canvas.create_text(x, y, text=content, font=font_tuple, fill=self.main_page.current_color, anchor=NW, tags=("editable", "text_obj"), angle=0, width=box_width if is_multiline else 0)
                
                self.item_original_fonts[self._get_id(item_id)] = original_pdf_font or self.main_page._get_pymupdf_font(ff)
                self.item_real_sizes[self._get_id(item_id)] = fs_real
                
                self.selected_items = [self._get_id(item_id)]
                self._draw_highlights()
                self.main_page._sync_toolbar_with_selection()

            if self.canvas.winfo_exists(): self.after(200, lambda: setattr(self, '_is_finalizing', False))

        if is_multiline:
            entry = Text(self.canvas, font=(ff, fs_tk), fg=self.main_page.current_color, bd=0, highlightthickness=1, highlightbackground="#3498db", relief="flat", background="white", wrap="word")
            entry.insert("1.0", initial_text)
            entry.bind("<FocusOut>", lambda e: self.after(100, finalize) if self.canvas.winfo_exists() else None)
            entry.bind("<Control-Return>", finalize) 
        else:
            entry = Entry(self.canvas, font=(ff, fs_tk), fg=self.main_page.current_color, bd=0, highlightthickness=0, relief="flat", background="white")
            if initial_text: entry.insert(0, initial_text)
            entry.bind("<Return>", finalize)
            entry.bind("<FocusOut>", lambda e: self.after(100, finalize) if self.canvas.winfo_exists() else None)
            
        entry.focus_set()
        kwargs = {"window": entry, "anchor": NW}
        if box_width: kwargs["width"] = box_width
        if box_height and is_multiline: kwargs["height"] = box_height
        window_id = self.canvas.create_window(x, y, **kwargs)
        self.active_entry_window = window_id

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
        page = self.pdf_doc[self.current_page_idx]; z = self.zoom_level; pdf_x, pdf_y = cx / z, cy / z
        try:
            words = page.get_text("words"); clicked_word = None
            for w in words:
                if (w[0] - 2) <= pdf_x <= (w[2] + 2) and (w[1] - 2) <= pdf_y <= (w[3] + 2): clicked_word = w; break # type: ignore
            if not clicked_word: return None
            ff, opf, fs, col = self._get_pdf_font_info(page, (clicked_word[0] + clicked_word[2])/2, (clicked_word[1] + clicked_word[3])/2) # type: ignore
            return {"text": clicked_word[4], "bbox": (clicked_word[0], clicked_word[1], clicked_word[2], clicked_word[3]), "font_family": ff, "original_pdf_font": opf, "font_size": fs, "color": col}
        except: return None

    def _find_pdf_text_in_rect(self, pdf_bbox):
        page = self.pdf_doc[self.current_page_idx]; rx0, ry0, rx1, ry1 = pdf_bbox
        words = page.get_text("words")
        selected_words = [w for w in words if not (w[2] < rx0 or w[0] > rx1 or w[3] < ry0 or w[1] > ry1)]
        if not selected_words: return None
        text = page.get_textbox(fitz.Rect(rx0, ry0, rx1, ry1))
        if not text.strip(): return None
        ff, opf, fs, col = self._get_pdf_font_info(page, (selected_words[0][0]+selected_words[0][2])/2, (selected_words[0][1]+selected_words[0][3])/2) # type: ignore
        return {"text": text, "bbox": (min(w[0] for w in selected_words), min(w[1] for w in selected_words), max(w[2] for w in selected_words), max(w[3] for w in selected_words)), "font_family": ff, "original_pdf_font": opf, "font_size": fs, "color": col}

    def _save_current_page_state(self):
        current_items = []; ratio = 1 / self.zoom_level 
        for item in self.canvas.find_withtag("editable"):
            item_id = self._get_id(item); tags = self.canvas.gettags(item_id); coords = self.canvas.coords(item_id) # type: ignore
            real_coords = [c * ratio for c in coords]; data = {"tags": tags, "coords": real_coords}
            if "text_obj" in tags:
                f = tkFont.Font(font=self.canvas.itemcget(item_id, "font"))
                real_font_size = self.item_real_sizes.get(item_id, abs(f.actual("size")) * ratio)
                data.update({
                    "text": self.canvas.itemcget(item_id, "text"), 
                    "fill": self.canvas.itemcget(item_id, "fill"), 
                    "font_family": f.actual("family"), 
                    "weight": f.actual("weight"),
                    "slant": f.actual("slant"),
                    "underline": f.actual("underline"),
                    "original_pdf_font": self.item_original_fonts.get(item_id, "helv"), 
                    "real_font_size": real_font_size, 
                    "anchor": self.canvas.itemcget(item_id, "anchor"), 
                    "angle": float(self.canvas.itemcget(item_id, "angle") or 0.0),
                    "width": float(self.canvas.itemcget(item_id, "width") or 0.0) * ratio
                })
            elif "draw_line" in tags: data.update({"fill": self.canvas.itemcget(item_id, "fill")})
            elif "redaction" in tags: data.update({"fill": self.canvas.itemcget(item_id, "fill"), "outline": self.canvas.itemcget(item_id, "outline")})
            elif "signature" in tags and item_id in self.image_refs: data.update({"original_img": self.image_refs[item_id]["original"], "real_w": self.image_refs[item_id]["current_w"] * ratio, "real_h": self.image_refs[item_id]["current_h"] * ratio})
            current_items.append(data)
        self.pages_data[self.current_page_idx] = current_items

    def _load_page_state(self):
        if self.current_page_idx not in self.pages_data: return
        z = self.zoom_level; self.image_refs = {} 
        for data in self.pages_data[self.current_page_idx]:
            scaled_coords = [c * z for c in data["coords"]]
            if "text_obj" in data["tags"]:
                real_size = data["real_font_size"]; display_size = -max(1, round(real_size * z))
                f_weight = data.get("weight", "normal")
                f_slant = data.get("slant", "roman")
                f_under = data.get("underline", 0)
                font_tuple = tkFont.Font(family=data["font_family"], size=display_size, weight=f_weight, slant=f_slant, underline=f_under)
                
                display_width = data.get("width", 0.0) * z
                
                item_id = self.canvas.create_text(*scaled_coords, text=data["text"], fill=data["fill"], font=font_tuple, anchor=data["anchor"], tags=data["tags"], angle=data.get("angle", 0.0), width=display_width)
                self.item_original_fonts[self._get_id(item_id)] = data.get("original_pdf_font", "helv")
                self.item_real_sizes[self._get_id(item_id)] = real_size
            elif "draw_line" in data["tags"]: self.canvas.create_line(*scaled_coords, fill=data["fill"], width=2, capstyle="round", tags=data["tags"])
            elif "redaction" in data["tags"]: self.canvas.create_rectangle(*scaled_coords, fill=data["fill"], outline=data["outline"], tags=data["tags"])
            elif "signature" in data["tags"]:
                orig = data["original_img"]; w, h = int(data["real_w"] * z), int(data["real_h"] * z)
                display_img = orig.resize((w, h), Image.Resampling.LANCZOS); photo = ImageTk.PhotoImage(display_img)
                item_id = self._get_id(self.canvas.create_image(scaled_coords[0], scaled_coords[1], image=photo, anchor=NW, tags=data["tags"]))
                self.image_refs[item_id] = {"photo": photo, "original": orig, "current_w": w, "current_h": h}

# ==========================================
# LA PAGE PRINCIPALE (GESTION DES ONGLETS)
# ==========================================
class EditPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.app_data_dir = Path(os.getenv('APPDATA', '.')) / "BulkPDF"
        self.sig_dir = self.app_data_dir / "signatures"
        self.sig_dir.mkdir(parents=True, exist_ok=True) 
        self.signature_img_path = self.sig_dir / "user_signature.png"
        
        self.editors = {} 
        self.active_tab_name = None
        
        self.tool_mode = "pan"
        self.current_real_font_size = 14.0 
        self.current_color = "#000000" 
        self.last_x, self.last_y = 0, 0
        
        self._load_shortcuts()
        self._setup_ui()
        self._setup_bindings()

    def get_active_editor(self):
        if self.active_tab_name and self.active_tab_name in self.editors:
            return self.editors[self.active_tab_name]["editor"]
        return None

    def _load_shortcuts(self):
        self.shortcuts = {"select": "v", "pan": "h", "text": "t", "draw": "d", "erase": "e", "signature": "p", "pipette": "i", "rotate": "r", "enlarge": "+", "shrink": "-"}
        cfg_path = self.app_data_dir / "shortcuts.json"
        if cfg_path.exists():
            try:
                with open(cfg_path, "r") as f: self.shortcuts.update(json.load(f))
            except: pass

    def _get_edit_icon(self, name, size=(14, 14)):
        try:
            paths = [resource_path(os.path.join("src", "assets", "edit", f"{name}.png")), resource_path(os.path.join("assets", "edit", f"{name}.png"))]
            for p in paths:
                if p.exists():
                    img_light = Image.open(str(p)).convert("RGBA"); r, g, b, a = img_light.split()
                    img_dark = Image.merge("RGBA", (r.point(lambda _: 255), g.point(lambda _: 255), b.point(lambda _: 255), a))
                    return ctk.CTkImage(light_image=img_light, dark_image=img_dark, size=size)
            return None
        except: return None

    # --- UI HD ET ORGANISÉE EN GROUPES ---
    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # 1. TOP ACTION BAR (MENUS TEXTUELS)
        self.top_action_bar = ctk.CTkFrame(self, height=32, fg_color=BG_COLOR, corner_radius=0)
        self.top_action_bar.grid(row=0, column=0, sticky="ew")
        self.top_action_bar.grid_propagate(False)

        self.btn_menu = ctk.CTkButton(self.top_action_bar, text="Fichier", font=(FONT_FAMILY, SIZE_MAIN), width=50, height=26, fg_color="transparent", text_color=TEXT_MAIN, hover_color=BORDER_COLOR, command=self._show_file_menu)
        self.btn_menu.pack(side="left", padx=5, pady=3)

        self.btn_edit = ctk.CTkButton(self.top_action_bar, text="Édition", font=(FONT_FAMILY, SIZE_MAIN), width=50, height=26, fg_color="transparent", text_color=TEXT_MAIN, hover_color=BORDER_COLOR, command=self._show_edit_menu)
        self.btn_edit.pack(side="left", padx=5, pady=3)

        self.mode_switch = ctk.CTkSegmentedButton(self.top_action_bar, values=["View", "Edit"], command=self._on_mode_change, font=(FONT_FAMILY, SIZE_MAIN, "bold"), height=24)
        self.mode_switch.set("View")
        self.mode_switch.pack(side="right", padx=10, pady=4)

        # 2. TOOLBAR CONTEXTUELLE "HD" AVEC GROUPES
        self.toolbar = ctk.CTkFrame(self, height=48, fg_color=TOPBAR_COLOR, corner_radius=0, border_width=1, border_color=BORDER_COLOR)
        self.toolbar.grid(row=1, column=0, sticky="ew")
        self.toolbar.grid_propagate(False)

        # Groupe 1 : Navigation et Outils de base
        grp_tools = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        grp_tools.pack(side="left", padx=(15, 5), pady=8, fill="y")
        
        self.tool_btns = {}
        tools = [
            ("hand", "pan", self.shortcuts["pan"]), 
            ("cursor", "select", self.shortcuts["select"]), 
            ("text", "text", self.shortcuts["text"]), 
            ("draw", "draw", self.shortcuts["draw"]), 
            ("eraser", "erase", self.shortcuts["erase"]), 
            ("protect", "signature", self.shortcuts["signature"]), 
            ("color", "pipette", self.shortcuts["pipette"])
        ]
        for icon, mode, shortcut in tools:
            btn = self._create_btn(grp_tools, icon, f"{mode.capitalize()} ({shortcut.upper()})", lambda m=mode: self.set_tool(m), fallback_text=mode[0].upper())
            self.tool_btns[mode] = btn
            
        self._add_sep(self.toolbar)
        
        # Groupe 2 : Manipulation d'objets (Agrandir, Réduire, Tourner, Poubelle)
        grp_manip = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        grp_manip.pack(side="left", padx=5, pady=8, fill="y")
        
        self.btn_rotate = self._create_btn(grp_manip, "rotate", f"Pivoter ({self.shortcuts['rotate'].upper()})", self._rotate_selected, "↻")
        self.btn_plus = self._create_btn(grp_manip, "plus", f"Agrandir ({self.shortcuts['enlarge'].upper()})", lambda: self._change_item_size(1.1), "➕")
        self.btn_minus = self._create_btn(grp_manip, "minus", f"Réduire ({self.shortcuts['shrink'].upper()})", lambda: self._change_item_size(0.9), "➖")
        self.btn_trash = self._create_btn(grp_manip, "trash", "Supprimer (Suppr)", self._delete_selected, "🗑")

        self._add_sep(self.toolbar)
        
        # Groupe 3 : Style de Texte (Police, Taille, B I U, Couleur)
        grp_style = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        grp_style.pack(side="left", padx=5, pady=8, fill="y")
        
        self.font_menu = ctk.CTkComboBox(grp_style, values=["Arial", "Helvetica", "Times New Roman", "Courier New", "Calibri", "Cambria"], width=140, height=28, corner_radius=4, border_color=BORDER_COLOR, font=(FONT_FAMILY, SIZE_MAIN), command=self._update_font_family)
        self.font_menu.set("Arial")
        self.font_menu.pack(side="left", padx=(0, 5))

        self.size_menu = ctk.CTkComboBox(grp_style, values=["10", "12", "14", "16", "18", "24", "32", "48", "64"], width=70, height=28, corner_radius=4, border_color=BORDER_COLOR, font=(FONT_FAMILY, SIZE_MAIN), command=self._update_font_size)
        self.size_menu.set("14")
        self.size_menu.pack(side="left", padx=5)
        
        try:
            self.size_menu._entry.bind("<Return>", lambda e: self._update_font_size())
            self.size_menu._entry.bind("<FocusOut>", lambda e: self._update_font_size())
        except: self.size_menu.bind("<Return>", lambda e: self._update_font_size())
        
        self.btn_bold = self._create_btn(grp_style, "bold", "Gras", lambda: self._toggle_text_style("bold"), "B")
        self.btn_bold.configure(font=(FONT_FAMILY, SIZE_MAIN, "bold"))
        self.btn_italic = self._create_btn(grp_style, "italic", "Italique", lambda: self._toggle_text_style("italic"), "I")
        self.btn_italic.configure(font=(FONT_FAMILY, SIZE_MAIN, "italic"))
        self.btn_underline = self._create_btn(grp_style, "underline", "Souligné", lambda: self._toggle_text_style("underline"), "U")
        self.btn_underline.configure(font=(FONT_FAMILY, SIZE_MAIN, "underline"))

        self.color_btn = ctk.CTkButton(grp_style, text="", width=24, height=24, fg_color=self.current_color, command=self._choose_color, corner_radius=12)
        self.color_btn.pack(side="left", padx=(10, 5))
        ToolTip(self.color_btn, "Changer de couleur")

        # 3. ONGLETS
        self.tab_bar = ctk.CTkFrame(self, height=36, fg_color="#2b2b2b", corner_radius=0, border_width=0)
        self.tab_bar.grid(row=2, column=0, sticky="ew")
        self.tab_bar.grid_propagate(False) 

        # 4. CONTENEUR PRINCIPAL
        self.editor_container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.editor_container.grid(row=3, column=0, sticky="nsew")
        self.grid_rowconfigure(3, weight=1)
        
        self._on_mode_change("View")

    def _get_menu_colors(self):
        is_dark = ctk.get_appearance_mode() == "Dark"
        accent = ACCENT_PRIMARY[1] if is_dark and isinstance(ACCENT_PRIMARY, tuple) else (ACCENT_PRIMARY[0] if isinstance(ACCENT_PRIMARY, tuple) else ACCENT_PRIMARY)
        bg = "#2b2b2b" if is_dark else "white"
        fg = "white" if is_dark else "black"
        return bg, fg, accent

    def _show_file_menu(self):
        bg, fg, accent = self._get_menu_colors()
        menu = tk.Menu(self, tearoff=0, font=(FONT_FAMILY, 10), bg=bg, fg=fg, activebackground=accent)
        menu.add_command(label="Nouveau (Vide)", command=lambda: messagebox.showinfo("Info", "Bientôt disponible !"))
        menu.add_command(label="Ouvrir (Ctrl+O)", command=self._open_file_dialog)
        menu.add_separator()
        menu.add_command(label="Sauvegarder (Ctrl+S)", command=lambda: self.save_changes())
        menu.add_command(label="Enregistrer sous...", command=lambda: self.save_changes(force_ask=True))
        menu.add_separator()
        menu.add_command(label="Imprimer", command=lambda: messagebox.showinfo("Info", "Impression non disponible"))
        menu.add_command(label="Fermer l'onglet", command=lambda: self.close_tab(self.active_tab_name) if self.active_tab_name else None)
        
        x = self.btn_menu.winfo_rootx()
        y = self.btn_menu.winfo_rooty() + self.btn_menu.winfo_height()
        menu.tk_popup(x, y)

    def _show_edit_menu(self):
        bg, fg, accent = self._get_menu_colors()
        menu = tk.Menu(self, tearoff=0, font=(FONT_FAMILY, 10), bg=bg, fg=fg, activebackground=accent)
        
        editor = self.get_active_editor()
        menu.add_command(label="Annuler (Ctrl+Z)", command=lambda: editor.undo() if editor else None, state="normal" if editor and editor.history else "disabled")
        menu.add_command(label="Rétablir (Ctrl+Y)", command=lambda: editor.redo() if editor else None, state="normal" if editor and editor.redo_stack else "disabled")
        menu.add_separator()
        menu.add_command(label="Couper (Ctrl+X)", command=lambda: print("Couper (À venir)"))
        menu.add_command(label="Copier (Ctrl+C)", command=lambda: print("Copier (À venir)"))
        menu.add_command(label="Coller (Ctrl+V)", command=lambda: print("Coller (À venir)"))
        menu.add_separator()
        
        # Ajout des options de Groupement
        menu.add_command(label="Grouper (Ctrl+G)", command=lambda: editor.group_selected() if editor else None, state="normal" if editor and len(editor.selected_items) > 1 else "disabled")
        menu.add_command(label="Dégrouper (Ctrl+Maj+G)", command=lambda: editor.ungroup_selected() if editor else None, state="normal" if editor and editor.selected_items else "disabled")
        
        menu.add_separator()
        menu.add_command(label="Tout sélectionner (Ctrl+A)", command=self._select_all)
        menu.add_command(label="Supprimer (Suppr)", command=self._delete_selected)
        
        x = self.btn_edit.winfo_rootx()
        y = self.btn_edit.winfo_rooty() + self.btn_edit.winfo_height()
        menu.tk_popup(x, y)

    def _select_all(self):
        editor = self.get_active_editor()
        if not editor: return
        editor.selected_items = [editor._get_id(i) for i in editor.canvas.find_withtag("editable")]
        editor._draw_highlights()
        self._sync_toolbar_with_selection()

    def _create_btn(self, parent, icon_name, tooltip_text, command, fallback_text=""):
        icon = self._get_edit_icon(icon_name)
        text_to_show = "" if icon else fallback_text
        btn = ctk.CTkButton(parent, text=text_to_show, image=icon, width=28, height=28, corner_radius=4, fg_color="transparent", text_color=TEXT_MAIN, font=(FONT_FAMILY, SIZE_MAIN), command=command)
        btn.pack(side="left", padx=2)
        ToolTip(btn, tooltip_text)
        return btn

    def _add_sep(self, parent):
        ctk.CTkFrame(parent, width=1, height=20, fg_color=BORDER_COLOR).pack(side="left", padx=8, pady=10)

    # --- LOGIQUE DE FORMATAGE DE TEXTE ---
    def _toggle_text_style(self, style_type):
        editor = self.get_active_editor()
        if not editor: return
        
        editor.push_history()
        for item in editor.selected_items:
            if "text_obj" in editor.canvas.gettags(item):
                f = tkFont.Font(font=editor.canvas.itemcget(item, "font"))
                family, size, weight, slant, underline = f.actual("family"), f.actual("size"), f.actual("weight"), f.actual("slant"), f.actual("underline")

                if style_type == "bold": weight = "normal" if weight == "bold" else "bold"
                elif style_type == "italic": slant = "roman" if slant == "italic" else "italic"
                elif style_type == "underline": underline = 0 if underline == 1 else 1

                new_font = tkFont.Font(family=family, size=size, weight=weight, slant=slant, underline=underline)
                editor.canvas.itemconfig(item, font=new_font)
                editor.is_modified = True
                
        if editor.selected_items:
            self._sync_toolbar_with_selection()

    # --- LOGIQUE DES ONGLETS ---
    def _open_file_dialog(self):
        p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if not p: return 
        name = Path(p).name
        base_name = name
        counter = 1
        while name in self.editors:
            name = f"{base_name} ({counter})"
            counter += 1
        try:
            editor = PdfEditorTab(self.editor_container, p, main_page=self)
        except Exception as e:
            if "Encrypted" not in str(e): messagebox.showerror("Erreur", f"Impossible d'ouvrir le fichier :\n{e}")
            return 
        tab_frame = ctk.CTkFrame(self.tab_bar, fg_color="#44475a", corner_radius=4)
        tab_frame.pack(side="left", padx=2, pady=2, fill="y")
        lbl = ctk.CTkLabel(tab_frame, text=name, font=(FONT_FAMILY, 12, "bold"), text_color="white")
        lbl.pack(side="left", padx=(10, 5), pady=2)
        lbl.bind("<Button-1>", lambda e, n=name: self.switch_tab(n))
        close_btn = ctk.CTkButton(tab_frame, text="✕", width=20, height=20, corner_radius=4, fg_color="transparent", hover_color="#ff4757", text_color="white", font=(FONT_FAMILY, 12, "bold"), command=lambda n=name: self.close_tab(n))
        close_btn.pack(side="left", padx=(0, 5), pady=2)
        
        self.editors[name] = {"frame": tab_frame, "lbl": lbl, "editor": editor}
        self.switch_tab(name)

    def switch_tab(self, name):
        if self.active_tab_name and self.active_tab_name in self.editors:
            self.editors[self.active_tab_name]["editor"].pack_forget()
            self.editors[self.active_tab_name]["frame"].configure(fg_color="#44475a")
        if name not in self.editors: return
        self.active_tab_name = name
        self.editors[name]["frame"].configure(fg_color="#4a69bd") 
        self.editors[name]["editor"].pack(fill="both", expand=True)
        self._sync_toolbar_with_selection()

    def close_tab(self, name):
        if name not in self.editors: return
        editor = self.editors[name]["editor"]
        if editor.is_modified:
            ans = messagebox.askyesnocancel("Warning", t("unsaved_warning") if "unsaved_warning" in t("unsaved_warning") else "Vous avez des modifications non sauvegardées.\nVoulez-vous sauvegarder avant de fermer ?")
            if ans is True:
                if not self.save_changes(target_name=name): return 
            elif ans is None: return 

        self.editors[name]["frame"].destroy()
        editor.destroy()
        del self.editors[name]
        
        if self.active_tab_name == name:
            self.active_tab_name = None
            if self.editors: self.switch_tab(list(self.editors.keys())[-1]) 

    # --- GESTION DU MODE ET DES ACTIONS ---
    def _on_mode_change(self, value):
        is_edit = (value == "Edit")
        state = "normal" if is_edit else "disabled"
        
        for name, btn in self.tool_btns.items(): 
            if name != "pan": btn.configure(state=state)
            
        for btn in [self.btn_rotate, self.btn_plus, self.btn_minus, self.btn_trash, self.btn_bold, self.btn_italic, self.btn_underline]:
            btn.configure(state=state)
            if not is_edit: btn.configure(fg_color="transparent")
            
        self.font_menu.configure(state=state); self.size_menu.configure(state=state); self.color_btn.configure(state=state)
        
        if not is_edit: self.set_tool("pan")
        else: self.set_tool("select")

    def set_tool(self, mode):
        if self.mode_switch.get() == "View" and mode != "pan": return
        editor = self.get_active_editor()
        if editor and editor.active_entry_window: editor.canvas.focus_set()
        
        self.tool_mode = mode
        if editor:
            editor.selected_items = []; editor.canvas.delete("highlighter"); editor.canvas.delete("handle")
            if editor.current_pdf_selection_rect:
                editor.canvas.delete(editor.current_pdf_selection_rect); editor.current_pdf_selection_rect = None
                
        for m, btn in self.tool_btns.items(): btn.configure(fg_color=ACCENT_PRIMARY if m == mode else "transparent")

    def _sync_toolbar_with_selection(self):
        editor = self.get_active_editor()
        if editor and len(editor.selected_items) == 1:
            item_id = editor.selected_items[0]
            if "text_obj" in editor.canvas.gettags(item_id):
                real_size = editor.item_real_sizes.get(item_id, 14.0)
                self.current_real_font_size = real_size
                self.size_menu.set(str(int(real_size)) if real_size.is_integer() else f"{real_size:.1f}")
                
                f = tkFont.Font(font=editor.canvas.itemcget(item_id, "font"))
                if f.actual("family") in self.font_menu._values: self.font_menu.set(f.actual("family"))
                
                self.btn_bold.configure(fg_color=ACCENT_PRIMARY if f.actual("weight") == "bold" else "transparent")
                self.btn_italic.configure(fg_color=ACCENT_PRIMARY if f.actual("slant") == "italic" else "transparent")
                self.btn_underline.configure(fg_color=ACCENT_PRIMARY if f.actual("underline") == 1 else "transparent")
                
                c = editor.canvas.itemcget(item_id, "fill")
                self.current_color = c; self.color_btn.configure(fg_color=c)
        else:
            self.btn_bold.configure(fg_color="transparent")
            self.btn_italic.configure(fg_color="transparent")
            self.btn_underline.configure(fg_color="transparent")

    def _get_pymupdf_font(self, tk_font_name, weight="normal", slant="roman"):
        base = "helv"
        lower = tk_font_name.lower()
        if "times" in lower or "cambria" in lower: base = "tiro" 
        elif "courier" in lower or "mono" in lower: base = "cour"
        
        if base == "helv":
            if weight == "bold" and slant == "italic": return "hebi"
            if weight == "bold": return "hebo"
            if slant == "italic": return "heit"
        return base

    def _update_font_family(self, v):
        editor = self.get_active_editor()
        if not editor: return
        editor.push_history()
        for item in editor.selected_items:
            if "text_obj" in editor.canvas.gettags(item):
                f = tkFont.Font(font=editor.canvas.itemcget(item, "font"))
                editor.canvas.itemconfig(item, font=tkFont.Font(family=v, size=f.actual("size"), weight=f.actual("weight"), slant=f.actual("slant"), underline=f.actual("underline")))
                editor.item_original_fonts[item] = self._get_pymupdf_font(v, f.actual("weight"), f.actual("slant"))
                editor.is_modified = True
        editor._draw_highlights()

    def _update_font_size(self, v=None): 
        editor = self.get_active_editor()
        if not editor: return
        if v is None: v = self.size_menu.get()
        try:
            editor.push_history()
            self.current_real_font_size = float(str(v).replace(',', '.'))
            for item in editor.selected_items:
                if "text_obj" in editor.canvas.gettags(item):
                    editor.item_real_sizes[item] = self.current_real_font_size
                    f = tkFont.Font(font=editor.canvas.itemcget(item, "font"))
                    editor.canvas.itemconfig(item, font=tkFont.Font(family=f.actual("family"), size=-max(1, round(self.current_real_font_size * editor.zoom_level)), weight=f.actual("weight"), slant=f.actual("slant"), underline=f.actual("underline")))
                    editor.is_modified = True
            editor._draw_highlights()
        except ValueError: pass

    def _change_item_size(self, factor):
        editor = self.get_active_editor()
        if not editor: return
        editor.push_history()
        for item in editor.selected_items:
            tags = editor.canvas.gettags(item)
            if "signature" in tags and item in editor.image_refs:
                editor.image_refs[item]["current_w"] *= factor; editor.image_refs[item]["current_h"] *= factor; editor._refresh_image_item(item)
                editor.is_modified = True
            elif "text_obj" in tags:
                real_size = editor.item_real_sizes.get(item, 14.0)
                new_real_size = real_size * factor
                old_tk, new_tk = round(real_size * editor.zoom_level), round(new_real_size * editor.zoom_level)
                if old_tk == new_tk: new_real_size += 1.0 if factor > 1 else -1.0
                editor.item_real_sizes[item] = new_real_size
                f = tkFont.Font(font=editor.canvas.itemcget(item, "font"))
                editor.canvas.itemconfig(item, font=tkFont.Font(family=f.actual("family"), size=-max(1, round(new_real_size * editor.zoom_level)), weight=f.actual("weight"), slant=f.actual("slant"), underline=f.actual("underline")))
                editor.is_modified = True
        editor._draw_highlights()
        self._sync_toolbar_with_selection()

    def _delete_selected(self):
        editor = self.get_active_editor()
        if not editor or not editor.selected_items: return
        editor.push_history()
        for item in editor.selected_items:
            editor.canvas.delete(item)
            if item in editor.image_refs: del editor.image_refs[item]
            if item in editor.item_groups: del editor.item_groups[item]
        editor.selected_items = []; editor.canvas.delete("highlighter"); editor.canvas.delete("handle")
        editor.is_modified = True

    def _rotate_selected(self):
        editor = self.get_active_editor()
        if not editor: return
        editor.push_history()
        for item in editor.selected_items:
            tags = editor.canvas.gettags(item)
            if "signature" in tags and item in editor.image_refs:
                data = editor.image_refs[item]
                data["original"] = data["original"].rotate(-90, expand=True)
                data["current_w"], data["current_h"] = data["current_h"], data["current_w"]
                editor._refresh_image_item(item)
                editor.is_modified = True
            elif "text_obj" in tags:
                editor.canvas.itemconfig(item, angle=(float(editor.canvas.itemcget(item, "angle") or 0.0) + 90) % 360)
                editor.is_modified = True
        editor._draw_highlights()

    def _choose_color(self):
        c = colorchooser.askcolor()[1]
        if c: 
            self.current_color = c; self.color_btn.configure(fg_color=c)
            editor = self.get_active_editor()
            if editor:
                editor.push_history()
                for item in editor.selected_items:
                    if "text_obj" in editor.canvas.gettags(item) or "draw_line" in editor.canvas.gettags(item): 
                        editor.canvas.itemconfig(item, fill=c); editor.is_modified = True

    def _setup_bindings(self):
        top = self.winfo_toplevel()
        top.bind("<Key>", self._on_key_press)
        top.bind("<Control-MouseWheel>", lambda e: self._safe_shortcut(lambda: self.get_active_editor() and self.get_active_editor()._change_zoom(0.1 if e.delta > 0 else -0.1)))

    def _safe_shortcut(self, func):
        if not self.winfo_ismapped(): return
        if self.mode_switch.get() == "View": return 
        focus = self.focus_get()
        if isinstance(focus, (Entry, Text, ctk.CTkEntry, ctk.CTkComboBox)): return
        editor = self.get_active_editor()
        if editor and editor.active_entry_window is not None: return
        func()

    def _on_key_press(self, event):
        if not self.winfo_ismapped(): return
        focus = self.focus_get()
        if isinstance(focus, (Entry, Text, ctk.CTkEntry, ctk.CTkComboBox)): return
        editor = self.get_active_editor()
        if editor and editor.active_entry_window is not None: return

        char = event.char.lower() if event.char else ""
        keysym = event.keysym.lower()

        if event.state & 0x0004: 
            if keysym == "o": self._open_file_dialog()
            elif keysym == "s": self.save_changes()
            elif keysym == "a": self._select_all()
            elif keysym == "z": editor and editor.undo()
            elif keysym == "y": editor and editor.redo()
            elif keysym == "g" and event.state & 0x0001: editor and editor.ungroup_selected() # Ctrl+Shift+G
            elif keysym == "g": editor and editor.group_selected() # Ctrl+G
            elif keysym in ("plus", "equal", "add", "kp_add"): editor and editor._change_zoom(0.1)
            elif keysym in ("minus", "subtract", "kp_subtract"): editor and editor._change_zoom(-0.1)
            return

        for action, key in self.shortcuts.items():
            if key.lower() in (char, keysym):
                if action == "pan": self.set_tool("pan")
                elif self.mode_switch.get() == "Edit":
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

        if self.mode_switch.get() == "Edit" and keysym in ("delete", "backspace"): 
            self._delete_selected()

    def save_changes(self, target_name=None, force_ask=False):
        name = target_name if target_name else self.active_tab_name
        if not name or name not in self.editors: return False
        
        editor = self.editors[name]["editor"]
        if not editor.pdf_doc: return False
        if editor.active_entry_window: editor.canvas.focus_set()
        
        editor._save_current_page_state() 
        for pg_idx, items in editor.pages_data.items():
            page = editor.pdf_doc[pg_idx]
            for data in items:
                coords = data["coords"]
                if "text_obj" in data["tags"]:
                    pdf_font_size = data["real_font_size"]
                    rgb = tuple(int(data["fill"].lstrip('#')[i:i+2], 16)/255.0 for i in (0, 2, 4))
                    pdf_font = self._get_pymupdf_font(data.get("font_family", "Arial"), data.get("weight", "normal"), data.get("slant", "roman"))
                    
                    if data.get("underline") == 1:
                        y_pos = coords[1] + (pdf_font_size * 1.1)
                        page.draw_line(fitz.Point(coords[0], y_pos), fitz.Point(coords[0] + (len(data["text"]) * pdf_font_size * 0.5), y_pos), color=rgb, width=1)
                        
                    page.insert_text((coords[0], coords[1] + (pdf_font_size * 0.75)), data["text"], fontname=pdf_font, fontsize=pdf_font_size, color=rgb, rotate=int(data.get("angle", 0)))
                elif "draw_line" in data["tags"]: page.draw_line(fitz.Point(coords[0], coords[1]), fitz.Point(coords[2], coords[3]), color=[int(data["fill"][i:i+2], 16)/255 for i in (1, 3, 5)], width=2)
                elif "redaction" in data["tags"]: page.draw_rect(fitz.Rect(coords[0], coords[1], coords[2], coords[3]), color=(1, 1, 1), fill=(1, 1, 1))
                elif "signature" in data["tags"]:
                    img_buffer = io.BytesIO()
                    data["original_img"].save(img_buffer, format='PNG')
                    page.insert_image(fitz.Rect(coords[0], coords[1], coords[0] + data["real_w"], coords[1] + data["real_h"]), stream=img_buffer.getvalue())

        orig_name = Path(editor.pdf_path).stem
        if force_ask:
            save_path = filedialog.asksaveasfilename(initialfile=f"{orig_name}_edited.pdf", defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        else:
            save_path = filedialog.asksaveasfilename(initialfile=f"{orig_name}_edited.pdf", defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
            
        if save_path:
            editor.pdf_doc.save(save_path)
            editor.is_modified = False 
            messagebox.showinfo(t("success"), t("doc_saved"))
            return True
        return False