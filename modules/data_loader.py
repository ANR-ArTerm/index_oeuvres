import json
import os
from dotenv import load_dotenv

DATA_DIR = "data"
PEINTURE_DIR = os.path.join(DATA_DIR, "entry_peinture")
ARCHITECTURE_DIR = os.path.join(DATA_DIR, "entry_architecture")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
LIST_FORM_DIR = os.path.join(DATA_DIR, "list_form")

TYPE_DIRS = {
        "peinture": PEINTURE_DIR,
        "architecture": ARCHITECTURE_DIR,
    }

def load_all_notices():
    """
    Charge tous les fichiers JSON du dossier DATA_DIR.
    
    Renvoie :
        - oeuvres : liste des œuvres (dict)
        - filenames : liste des chemins de fichiers correspondants
        - existing_type : liste des types d'œuvres existants
        - existing_artist : liste des xml:id des artistes existants
        - existing_role : liste des rôles existants dans les artistes
        - existing_technique : liste des techniques existantes
        - existing_city : liste des villes existantes
        - existing_institution : liste des institutions existantes
    """
    oeuvres = []
    filenames = []

    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # --- Chargement JSON ---
    for file in os.listdir(DATA_DIR):
        if file.endswith(".json"):
            path = os.path.join(DATA_DIR, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    oeuvres.append(data)
                    filenames.append(path)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"⚠️ Impossible de charger {path} : {e}")

    # --- Fonctions utilitaires ---
    def flatten_to_set(field):
        """Renvoie un set des valeurs uniques pour un champ simple"""
        result = set()
        for o in oeuvres:
            val = o.get(field)
            if isinstance(val, list):
                result.update([str(v) for v in val])
            elif val:
                result.add(str(val))
        return sorted(result)

    def flatten_artistes(oeuvres):
        """Renvoie 2 sets : xml:id et roles"""
        artists_set = set()
        roles_set = set()
        for o in oeuvres:
            artistes = o.get("artistes", [])
            for a in artistes:
                if isinstance(a, dict):
                    if "xml:id" in a:
                        artists_set.add(a["xml:id"])
                    if "role" in a:
                        roles_set.add(a["role"])
                elif isinstance(a, str):
                    artists_set.add(a)
        return sorted(artists_set), sorted(roles_set)

    # --- Champs simples ---
    existing_type = flatten_to_set("type_oeuvre")
    existing_technique = flatten_to_set("technique")
    existing_city = flatten_to_set("ville")
    existing_institution = flatten_to_set("institution")

    # --- Artistes & rôles ---
    existing_artist, existing_role = flatten_artistes(oeuvres)

    return (
        oeuvres,
        filenames,
        existing_type,
        existing_artist,
        existing_role,
        existing_technique,
        existing_city,
        existing_institution,
    )

def get_all_objects_ids(type_name: str):
    """
    Récupère la liste des 'id' dans tous les fichiers JSON d'un dossier.

    Args:
        type_name (str): "peinture" ou "architecture"

    Returns:
        list: liste des id trouvés
    """
    if type_name not in TYPE_DIRS:
        raise ValueError(f"Type inconnu : {type_name}")

    folder = TYPE_DIRS[type_name]
    objects_ids = []

    # Parcourir tous les fichiers JSON du dossier
    for filename in os.listdir(folder):
        if filename.endswith(".json"):
            path = os.path.join(folder, filename)
            with open(path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    continue  # Ignorer les fichiers JSON invalides

                # Vérifier si c'est une liste ou un dict unique
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "id" in item:
                            objects_ids.append(item["id"])
                elif isinstance(data, dict) and "id" in data:
                    objects_ids.append(data["id"])

    return objects_ids

def save_image(uploaded_file, save_path=None):
    save_path = os.path.join(IMAGES_DIR, uploaded_file.name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return save_path


def load_notice(path):
    """
    Charge un seul fichier JSON.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_notice(oeuvre, path=None):
    """
    Sauvegarde une œuvre dans un fichier JSON.
    - Si path est None → génère automatiquement :
        data/entry_[ENTRY_TYPE]/ID.json
    """

    # obtenir le type de l'œuvre
    type_oeuvre = oeuvre.get("entry_type", "inconnu")
    base_dir = TYPE_DIRS.get(type_oeuvre, DATA_DIR)

    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    # nom de fichier
    if path is None:
        id_oeuvre = oeuvre.get("id") or "nouvelle_notice"
        path = os.path.join(base_dir, f"{id_oeuvre}.json")

    # sauvegarde
    with open(path, "w", encoding="utf-8") as f:
        json.dump(oeuvre, f, ensure_ascii=False, indent=2)

    return path


def exist_notice(id):
    path = os.path.join(DATA_DIR, f"{id}.json")
    presence_notice = os.path.exists(path)
    return presence_notice

def delete_notice(path):
    """Supprime définitivement une œuvre."""
    if os.path.exists(path):
        os.remove(path)

# ========== Les listes pour l'autocomplétion

LIST_FILES = {
    "artists_names": "artists_names.json",
    "artists_roles": "artists_roles.json",
    "architects_roles":"architects_roles.json",
    "typologies": "typologies.json",
    "institutions": "institutions.json",
    "techniques": "techniques.json",
    "zotero_keys": "zotero_keys.json",
    "usernames": "usernames.json",
    "link_types":"link_types.json"
}

def _load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_list_form(key: str):
    """
    key ex: 'artists_roles', 'techniques', etc.
    """
    if key not in LIST_FILES:
        raise ValueError(f"Clé inconnue : {key}")

    path = os.path.join(LIST_FORM_DIR, LIST_FILES[key])
    return _load_json(path)


def save_to_list_form(key: str, value: str):
    if key not in LIST_FILES:
        raise ValueError(f"Clé inconnue : {key}")

    # Ignorer None ou chaîne vide
    if value is None or str(value).strip() == "":
        return

    path = os.path.join(LIST_FORM_DIR, LIST_FILES[key])

    # Charger les données existantes
    data = _load_json(path)

    # Ajouter si non présent
    if value not in data:
        data.append(value)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def load_username(default=None):
    load_dotenv()
    return os.getenv("USERNAME", default)

def index_username():
    username = load_username()
    options = load_list_form("usernames")
    index = options.index(username) if username in options else 0
    return index




