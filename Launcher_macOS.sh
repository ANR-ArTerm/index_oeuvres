#!/bin/bash

echo "=== Vérification de Python ==="

# Vérifie si python3 existe
if ! command -v python3 &> /dev/null; then
    echo ""
    echo "Python3 n'est pas installé ou n'est pas dans le PATH."
    echo "Télécharge-le ici : https://www.python.org/downloads/mac-osx/"
    exit 1
fi

PYTHON_FOUND=$(which python3)
echo "Python détecté : $PYTHON_FOUND"
echo ""

echo "=== Création / Activation de l'environnement virtuel ==="
echo ""

# Crée le venv si nécessaire
if [ ! -d ".venv" ]; then
    echo "Création du venv..."
    python3 -m venv .venv
    echo ""
fi

# Activation du venv
# macOS → bin/activate (et non Scripts/activate.bat)
if [ ! -f ".venv/bin/activate" ]; then
    echo "ERREUR : Le venv n'a pas été créé correctement."
    exit 1
fi

source .venv/bin/activate
echo "Environnement virtuel activé"
echo ""

echo "=== Installation des dépendances ==="
echo ""

# Vérifie si streamlit est déjà installé
python3 - <<EOF
import importlib.util, sys
sys.exit(0 if importlib.util.find_spec("streamlit") and importlib.util.find_spec("dotenv") else 1)
EOF

if [ $? -ne 0 ]; then
    echo "Installation des dépendances..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi
echo ""


echo "=== Création / Vérification du .env et du username ==="

VALID_USERS=("Pierre" "Julia" "Anna" "Emma" "Carla")

# Fonction pour demander un nom valide
ask_username() {
    while true; do
        read -p "Entrez votre nom d'utilisateur (Pierre, Julia, Anna, Emma, Carla) : " USERNAME
        for valid in "${VALID_USERS[@]}"; do
            if [ "$USERNAME" == "$valid" ]; then
                return 0
            fi
        done
        echo "Utilisateur invalide. Veuillez choisir parmi : ${VALID_USERS[*]}"
    done
}

# Si le fichier .env n'existe pas
if [ ! -f ".env" ]; then
    echo "Fichier .env introuvable, création..."
    ask_username
    echo "USERNAME=$USERNAME" > .env
else
    CURRENT_USER=$(grep "^USERNAME=" .env | cut -d= -f2)

    if [ -z "$CURRENT_USER" ]; then
        ask_username
        echo "USERNAME=$USERNAME" >> .env
    else
        echo "Nom d'utilisateur déjà présent : $CURRENT_USER"
    fi
fi


echo "=== Lancement de l'application ==="
echo ""
echo "L'application va s'ouvrir dans le navigateur."
echo ""
echo "Pour quitter : Ctrl + C dans ce terminal"
echo ""

streamlit run app.py
