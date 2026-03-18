import customtkinter as ctk

class MergePage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#242424", **kwargs)
        self.label = ctk.CTkLabel(self, text="BIENVENUE DANS MERGE PDF", 
                                   font=("Segoe UI", 24, "bold"), text_color="#8a55d1")
        self.label.pack(pady=50, padx=20)
        
        self.btn = ctk.CTkButton(self, text="+ Ajouter des fichiers", fg_color="#8a55d1")
        self.btn.pack(pady=20)
