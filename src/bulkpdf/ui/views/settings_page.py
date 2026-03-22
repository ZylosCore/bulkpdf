import os
import sys
import shutil
import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from ..i18n import i18n, t
# Cleaned up imports
from ..theme import (BG_COLOR, CARD_COLOR, BORDER_COLOR, TEXT_TITLE, FONT_FAMILY, TEXT_MAIN, TEXT_LOW,
                     CORNER_RADIUS, BTN_PRIMARY, BTN_PRIMARY_HOVER, 
                     BTN_SUCCESS, BTN_SUCCESS_HOVER, BTN_DANGER, BTN_DANGER_HOVER,
                     SIZE_TITLE, SIZE_MAIN, SIZE_SUBTITLE, TABVIEW_KWARGS)

class SettingsPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.app_data_dir = Path(os.getenv('APPDATA', '.')) / "BulkPDF"
        self.sig_folder = self.app_data_dir / "signatures"
        self.default_sig_path = self.sig_folder / "user_signature.png"
        
        try:
            self.sig_folder.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            pass

        self._setup_ui()
        self.refresh_signature_list()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkLabel(self, text="Settings & Preferences", font=(FONT_FAMILY, SIZE_TITLE, "bold"), text_color=TEXT_TITLE)
        header.grid(row=0, column=0, pady=(20, 10), padx=40, sticky="w")

        # Tabview styling
        self.tabs = ctk.CTkTabview(self, **TABVIEW_KWARGS)
        self.tabs.grid(row=1, column=0, sticky="nsew", padx=40, pady=(0, 20))
        
        self.tabs.add("General Options")
        self.tabs.add("Signatures")

        self._build_general_tab()
        self._build_signatures_tab()

    def _build_general_tab(self):
        tab = self.tabs.tab("General Options")
        tab.grid_columnconfigure(1, weight=1)

        card_gen = ctk.CTkFrame(tab, fg_color=CARD_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=CORNER_RADIUS)
        card_gen.pack(fill="x", pady=10, padx=20)
        card_gen.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(card_gen, text="App Appearance:", font=(FONT_FAMILY, SIZE_MAIN, "bold"), text_color=TEXT_TITLE).grid(row=0, column=0, padx=20, pady=(25, 15), sticky="w")
        self.theme_switch = ctk.CTkOptionMenu(
            card_gen, values=["System", "Light", "Dark"],
            font=(FONT_FAMILY, SIZE_MAIN), corner_radius=CORNER_RADIUS,
            fg_color=BG_COLOR, button_color=BORDER_COLOR, button_hover_color=BORDER_COLOR, text_color=TEXT_MAIN,
            command=self.change_appearance_mode
        )
        self.theme_switch.set("System")
        self.theme_switch.grid(row=0, column=1, padx=20, pady=(25, 15), sticky="w")

        ctk.CTkLabel(card_gen, text="Language:", font=(FONT_FAMILY, SIZE_MAIN, "bold"), text_color=TEXT_TITLE).grid(row=1, column=0, padx=20, pady=(15, 25), sticky="w")
        self.lang_map = {"en": "English", "fr": "Français", "ar": "العربية"}
        self.reverse_map = {v: k for k, v in self.lang_map.items()}
        
        lang_menu = ctk.CTkOptionMenu(
            card_gen, values=list(self.lang_map.values()), 
            font=(FONT_FAMILY, SIZE_MAIN), corner_radius=CORNER_RADIUS,
            fg_color=BG_COLOR, button_color=BORDER_COLOR, button_hover_color=BORDER_COLOR, text_color=TEXT_MAIN,
            command=self._change_language
        )
        lang_menu.set(self.lang_map.get(i18n.current_lang, "English"))
        lang_menu.grid(row=1, column=1, padx=20, pady=(15, 25), sticky="w")

    def _build_signatures_tab(self):
        tab = self.tabs.tab("Signatures")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        sig_header = ctk.CTkFrame(tab, fg_color="transparent")
        sig_header.grid(row=0, column=0, sticky="ew", pady=(10, 5), padx=20)
        
        ctk.CTkLabel(sig_header, text="Manage Signatures", font=(FONT_FAMILY, SIZE_SUBTITLE, "bold"), text_color=TEXT_TITLE).pack(side="left")
        self.add_btn = ctk.CTkButton(
            sig_header, text="+ Import PNG", width=130, height=32, corner_radius=CORNER_RADIUS,
            font=(FONT_FAMILY, SIZE_MAIN, "bold"), fg_color=BTN_PRIMARY, hover_color=BTN_PRIMARY_HOVER,
            command=self.import_new_signature
        )
        self.add_btn.pack(side="right")

        self.list_frame = ctk.CTkScrollableFrame(
            tab, fg_color=CARD_COLOR, corner_radius=CORNER_RADIUS, border_width=1, border_color=BORDER_COLOR
        )
        self.list_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 20), padx=20)

    def change_appearance_mode(self, new_mode):
        ctk.set_appearance_mode(new_mode)

    def _change_language(self, choice):
        selected_code = self.reverse_map[choice]
        if selected_code != i18n.current_lang:
            i18n.set_language(selected_code)
            messagebox.showinfo("Restart", "The app will restart to apply the new language.")
            os.execl(sys.executable, sys.executable, *sys.argv)

    def refresh_signature_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        files = [f for f in self.sig_folder.glob("*.png") if f.name != "user_signature.png"]

        if not files:
            ctk.CTkLabel(self.list_frame, text="No signatures saved", font=(FONT_FAMILY, SIZE_MAIN), text_color=TEXT_LOW).pack(pady=40)
            return

        for sig_file in files:
            item = ctk.CTkFrame(self.list_frame, fg_color=BG_COLOR, corner_radius=CORNER_RADIUS)
            item.pack(fill="x", pady=6, padx=10)
            ctk.CTkLabel(item, text=sig_file.stem, font=(FONT_FAMILY, SIZE_MAIN, "bold"), text_color=TEXT_MAIN).pack(side="left", padx=15, pady=12)

            del_btn = ctk.CTkButton(item, text="Delete", font=(FONT_FAMILY, SIZE_MAIN), fg_color=BTN_DANGER, hover_color=BTN_DANGER_HOVER, width=90, height=30, command=lambda p=sig_file: self.delete_signature(p))
            del_btn.pack(side="right", padx=15)

            def_btn = ctk.CTkButton(item, text="Set as Default", font=(FONT_FAMILY, SIZE_MAIN, "bold"), fg_color="transparent", border_width=1, border_color=BORDER_COLOR, text_color=TEXT_MAIN, hover_color=BORDER_COLOR, width=130, height=30, command=lambda p=sig_file: self.set_as_default(p))
            def_btn.pack(side="right", padx=5)

    def import_new_signature(self):
        file_path = filedialog.askopenfilename(filetypes=[("PNG Image", "*.png")])
        if not file_path: return

        dialog = ctk.CTkInputDialog(text="Enter a name for this signature:", title="Name")
        name = dialog.get_input()

        if name and name.strip():
            clean_name = name.strip().replace(" ", "_")
            target_path = self.sig_folder / f"{clean_name}.png"
            try:
                shutil.copy(file_path, target_path)
                self.refresh_signature_list()
                self.set_as_default(target_path)
            except Exception as e:
                messagebox.showerror("Error", f"Action failed: {e}")

    def set_as_default(self, source_path):
        try:
            shutil.copy(source_path, self.default_sig_path)
            messagebox.showinfo("Signature", f"'{source_path.stem}' is now the active signature!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_signature(self, path):
        if messagebox.askyesno("Confirm", f"Delete '{path.stem}'?"):
            try:
                os.remove(path)
                if self.default_sig_path.exists():
                    os.remove(self.default_sig_path)
                self.refresh_signature_list()
            except Exception as e:
                messagebox.showerror("Error", str(e))