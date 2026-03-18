#!/bin/bash
# Nettoyage du cache Python pour éviter les vieux résidus de modules
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Activation de l'environnement (Chemin Windows)
if [ -d "venv/Scripts" ]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# On force le PYTHONPATH au niveau du shell également
export PYTHONPATH="$(pwd)/src"
python run.py
