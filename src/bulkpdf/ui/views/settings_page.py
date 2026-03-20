import os
import shutil
import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path

class SettingsPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # --- CONFIGURATION DES CHEMINS ---
        self.app_data_dir = Path(os.getenv('APPDATA')) / "BulkPDF"
        self.sig_folder = self.app_data_dir / "signatures"
        self.default_sig_path = self.sig_folder / "user_signature.png"
        
        # Créer les dossiers s'ils n'existent pas
        try:
            self.sig_folder.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Erreur création dossier : {e}")

        self._setup_ui()
        self.refresh_signature_list()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # --- SECTION THÈME ---
        self.theme_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.theme_frame.pack(fill="x", padx=40, pady=(30, 10))
        
        ctk.CTkLabel(self.theme_frame, text="Apparence du logiciel", font=("Arial", 16, "bold")).pack(side="left")
        
        self.theme_switch = ctk.CTkOptionMenu(
            self.theme_frame, 
            values=["System", "Light", "Dark"],
            command=self.change_appearance_mode
        )
        self.theme_switch.set("System")
        self.theme_switch.pack(side="right")

        # --- SÉPARATEUR (Remplacement de CTkSeparator) ---
        self.line = ctk.CTkFrame(self, height=2, fg_color=("#dbdbdb", "#44475a"))
        self.line.pack(fill="x", padx=40, pady=20)

        # --- SECTION GESTION SIGNATURES ---
        self.sig_header = ctk.CTkFrame(self, fg_color="transparent")
        self.sig_header.pack(fill="x", padx=40)
        
        ctk.CTkLabel(self.sig_header, text="Gestion des Signatures", font=("Arial", 16, "bold")).pack(side="left")
        
        self.add_btn = ctk.CTkButton(
            self.sig_header, 
            text="+ Importer PNG", 
            width=120,
            command=self.import_new_signature
        )
        self.add_btn.pack(side="right")

        # Zone de liste des signatures
        self.list_frame = ctk.CTkScrollableFrame(self, height=350, fg_color=("#f0f0f0", "#252525"))
        self.list_frame.pack(fill="both", padx=40, pady=20)

    def change_appearance_mode(self, new_mode):
        ctk.set_appearance_mode(new_mode)

    def refresh_signature_list(self):
        """Affiche toutes les signatures PNG trouvées dans AppData"""
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        # Lister les fichiers .png (en ignorant le fichier de travail final)
        files = [f for f in self.sig_folder.glob("*.png") if f.name != "user_signature.png"]

        if not files:
            ctk.CTkLabel(self.list_frame, text="Aucune signature enregistrée", text_color="gray").pack(pady=40)
            return

        for sig_file in files:
            item = ctk.CTkFrame(self.list_frame, fg_color=("#ffffff", "#333333"))
            item.pack(fill="x", pady=5, padx=5)

            ctk.CTkLabel(item, text=sig_file.stem, font=("Arial", 13, "bold")).pack(side="left", padx=15, pady=10)

            # Bouton Supprimer
            del_btn = ctk.CTkButton(
                item, text="Supprimer", fg_color="#e74c3c", hover_color="#c0392b", 
                width=80, height=28, command=lambda p=sig_file: self.delete_signature(p)
            )
            del_btn.pack(side="right", padx=10)

            # Bouton Définir par défaut
            def_btn = ctk.CTkButton(
                item, text="Utiliser par défaut", fg_color="#2ecc71", hover_color="#27ae60",
                width=130, height=28, command=lambda p=sig_file: self.set_as_default(p)
            )
            def_btn.pack(side="right", padx=5)

    def import_new_signature(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image PNG", "*.png")])
        if not file_path:
            return

        dialog = ctk.CTkInputDialog(text="Entrez un nom pour cette signature :", title="Nom")
        name = dialog.get_input()

        if name and name.strip():
            clean_name = name.strip().replace(" ", "_")
            target_path = self.sig_folder / f"{clean_name}.png"
            
            try:
                shutil.copy(file_path, target_path)
                self.refresh_signature_list()
                # On la met par défaut automatiquement à l'import
                self.set_as_default(target_path)
            except Exception as e:
                messagebox.showerror("Erreur", f"Action impossible : {e}")

    def set_as_default(self, source_path):
        """Copie le fichier vers 'user_signature.png' pour l'EditPage"""
        try:
            shutil.copy(source_path, self.default_sig_path)
            messagebox.showinfo("Signature", f"'{source_path.stem}' est maintenant active !")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur d'activation : {e}")

    def delete_signature(self, path):
        if messagebox.askyesno("Confirmation", f"Supprimer '{path.stem}' ?"):
            try:
                os.remove(path)
                # Si on supprime la signature active, on essaie de supprimer aussi user_signature.png
                if self.default_sig_path.exists():
                    os.remove(self.default_sig_path)
                self.refresh_signature_list()
            except Exception as e:
                messagebox.showerror("Erreur", str(e))