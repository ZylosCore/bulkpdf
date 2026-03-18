#!/bin/bash

# 1. Chemins
ROOT_DIR=$(pwd)
export PYTHONPATH="$ROOT_DIR/src"

echo "[*] Vérification de la structure des fichiers..."

# Vérifier si le dossier views existe
if [ ! -d "src/bulkpdf/ui/views" ]; then
    echo "[!] ERREUR : Le dossier src/bulkpdf/ui/views/ est INTROUVABLE."
    echo "[*] Création du dossier et d'un fichier merge_page.py de secours..."
    mkdir -p src/bulkpdf/ui/views
    touch src/bulkpdf/ui/views/__init__.py
fi

# Vérifier si merge_page.py existe, sinon le créer pour éviter le crash
if [ ! -f "src/bulkpdf/ui/views/merge_page.py" ]; then
    echo "[*] Création d'un merge_page.py par défaut..."
    cat <<EOF > "src/bulkpdf/ui/views/merge_page.py"
import customtkinter as ctk

class MergePage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        label = ctk.CTkLabel(self, text="Page de Fusion PDF", font=("Arial", 20))
        label.pack(pady=20, padx=20)
EOF
fi

# 2. S'assurer que tous les dossiers sont des packages Python (__init__.py)
find src -type d -exec touch {}/__init__.py \;

echo "[*] Lancement avec PYTHONPATH=$PYTHONPATH"

# 3. Lancement Forcé
python3 -u "src/main.py"