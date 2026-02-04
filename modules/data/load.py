import json
import os
from dotenv import load_dotenv
from pathlib import Path
import shutil
import csv

# Variables et csv

DATA_DIR = "data"
PEINTURE_DIR = os.path.join(DATA_DIR, "entry_peinture")
ARCHITECTURE_DIR = os.path.join(DATA_DIR, "entry_architecture")
ENSEMBLE_DIR = os.path.join(DATA_DIR, "entry_ensemble")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
LIST_FORM_DIR = os.path.join(DATA_DIR, "list_form")
WIKIDATA_DIR = os.path.join(DATA_DIR, "wikidata_list")

TYPE_DIRS = {
        "peinture": PEINTURE_DIR,
        "architecture": ARCHITECTURE_DIR,
        "ensemble": ENSEMBLE_DIR
    }

LIST_FORM = {
    "persons":"persons.json",
    "artists_names": "artists_names.json",
    "artists_roles": "artists_roles.json",
    "architects_roles":"architects_roles.json",
    "typologies_architecture": "typologies_architecture.json",
    "institutions": "institutions.json",
    "techniques": "techniques.json",
    "zotero_keys": "zotero_keys.json",
    "usernames": "usernames.json",
    "link_types":"link_types.json",
    "typologies_ensemble":"typologies_ensemble.json",
    "link_types_contained":"link_types_contained.json",
    "link_types_contains":"link_types_contains.json",
    "text_xml":"text_xml.json"
}

LIST_CSV_QID = {
    "people": "people.csv",
    "typologies": "typologies.csv",
    "techniques": "techniques.csv",
    "institutions": "institutions.csv",
    "places":"places.csv"
}

def load_all_entries(type_name: str):
    """
    Charge tous les fichiers JSON dans le dossier correspondant à type_name.

    Args:
        type_name (str): "peinture" ou "architecture"

    Returns:
        list: liste de tuples (data, path) où data est le contenu JSON et path le chemin du fichier
    """
    if type_name not in TYPE_DIRS:
        raise ValueError(f"Type inconnu : {type_name}")

    folder = TYPE_DIRS[type_name]
    notices = []

    # Parcourir tous les fichiers JSON du dossier
    for filename in os.listdir(folder):
        if filename.endswith(".json"):
            path = os.path.join(folder, filename)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    notices.append((data, path))
            except json.JSONDecodeError:
                print(f"Erreur JSON dans le fichier {filename}, ignoré.")

    return notices


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

def get_all_objects_ids_by_type(type_name: str):
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

def get_all_objects_ids_flat_sorted(types=None):
    """
    Récupère tous les IDs pour les types demandés dans TYPE_DIRS.
    - Si types est None : tous les types sont utilisés
    - Sinon : seulement les types fournis (liste, tuple ou set)
    Retourne une liste unique triée alphabétiquement.
    ["peinture", "architecture"]
    """
    all_ids = set()

    # Si aucun type précisé, on prend tout
    if types is None:
        types = TYPE_DIRS.keys()

    for type_name in types:
        if type_name not in TYPE_DIRS:
            raise ValueError(f"Type inconnu : {type_name}")

        ids = get_all_objects_ids_by_type(type_name)
        all_ids.update(ids)

    return sorted(all_ids)


def save_image(uploaded_file, save_path=None):
    # Utiliser pathlib pour une meilleure compatibilité multiplateforme
    images_dir = Path(IMAGES_DIR)
    
    # Extraire uniquement le nom de fichier (sans chemin)
    # et nettoyer les caractères problématiques
    filename = Path(uploaded_file.name).name
    
    # Si un save_path spécifique est fourni
    if save_path:
        save_path = Path(save_path)
    else:
        save_path = images_dir / filename
    
    # Créer le répertoire si nécessaire
    save_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Sauvegarder le fichier
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return str(save_path)  # Retourner en string pour compatibilité



def load_notice(path):
    """
    Charge un seul fichier JSON.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_notice(oeuvre, path=None, old_id=None):
    """
    Sauvegarde une œuvre dans un fichier JSON.
    - Si path est None → génère automatiquement :
        data/entry_[ENTRY_TYPE]/ID.json
    """

    # obtenir le type de l'œuvre
    type_oeuvre = oeuvre.get("entry_type", "error_type")
    base_dir = TYPE_DIRS.get(type_oeuvre, DATA_DIR)

    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    
    new_id = oeuvre.get("id") or "nouvelle_notice"
    new_path = os.path.join(base_dir, f"{new_id}.json")

    if old_id != new_id and os.path.exists(new_path):
        raise ValueError("Un fichier avec cet ID existe déjà.")

    if path and old_id and old_id != new_id:
        if os.path.exists(path):
            os.remove(path)  # supprimer l'ancien fichier
        path = new_path

    # nom de fichier
    if path is None:
        path = new_path

    # sauvegarde
    with open(path, "w", encoding="utf-8") as f:
        json.dump(oeuvre, f, ensure_ascii=False, indent=2)

    return path


def exist_notice(id):
    path = os.path.join(DATA_DIR, f"{id}.json")
    presence_notice = os.path.exists(path)
    return presence_notice

def delete_notice(path):
    """Déplace une notice dans la corbeille au lieu de la supprimer définitivement."""
    if not os.path.exists(path):
        return False
    
    # Créer le dossier corbeille à la racine du repo
    trash_dir = Path("corbeille")
    trash_dir.mkdir(exist_ok=True)
    
    filename = Path(path)
    base_name = filename.stem
    extension = filename.suffix
    
    # Trouver un nom disponible
    counter = 0
    while True:
        if counter == 0:
            new_name = f"{base_name}{extension}"
        else:
            new_name = f"{base_name}_{counter}{extension}"
        
        trash_path = trash_dir / new_name
        
        if not trash_path.exists():
            break
        counter += 1
    
    # Déplacer le fichier dans la corbeille
    shutil.move(path, trash_path)
    
    return True

def _load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_list_form(*keys: str):
    seen = set()
    merged = []

    for key in keys:
        if key not in LIST_FORM:
            raise ValueError(f"Clé inconnue : {key}")

        path = os.path.join(LIST_FORM_DIR, LIST_FORM[key])
        for item in _load_json(path):
            if item not in seen:
                seen.add(item)
                merged.append(item)

    return merged


def save_to_list_form(key: str, value: str):
    if key not in LIST_FORM:
        raise ValueError(f"Clé inconnue : {key}")

    # Ignorer None ou chaîne vide
    if value is None or str(value).strip() == "":
        return

    path = os.path.join(LIST_FORM_DIR, LIST_FORM[key])

    # Charger les données existantes
    data = _load_json(path)

    # Ajouter si non présent
    if value not in data:
        data.append(value)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def save_list_to_list_form(key: str, values: list[str], *, sort: bool = True):
    if key not in LIST_FORM:
        raise ValueError(f"Clé inconnue : {key}")

    if not values:
        return

    path = os.path.join(LIST_FORM_DIR, LIST_FORM[key])

    # Charger les données existantes
    existing = _load_json(path)

    # Fusion + dédoublonnage
    merged = set(existing)
    for value in values:
        if value is None:
            continue
        value = str(value).strip()
        if value:
            merged.add(value)

    # Tri optionnel
    result = sorted(merged) if sort else list(merged)

    # Écriture
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


def load_username(default=None):
    load_dotenv()
    username = os.getenv("USERNAME", default)
    return username.strip() if username else None

def index_username():
    username = load_username()
    options = load_list_form("usernames")
    index = options.index(username) if username in options else None
    return index

def index_list_form(value, keys):
    """
    Retourne l'index de `value` dans la ou les listes fusionnées issues de load_list_form.
    
    Args:
        value (str): valeur à rechercher.
        keys (str | list[str]): clé ou liste de clés pour load_list_form.
    ATTENTION PEUT PRENDRE UNE LISTE DE CLÉS.
    
    Returns:
        int: index de la valeur dans la liste fusionnée, 0 si non trouvée ou si value est None.
    """
    if value is None:
        return None  # sécurité : retourne None pour selectbox

    # convertir en liste si c'est une seule clé
    if isinstance(keys, str):
        keys = [keys]

    # fusionner toutes les listes via load_list_form
    try:
        options = load_list_form(*keys)
    except Exception as e:
        # sécurité : si erreur, on retourne 0
        print(f"⚠️ index_list_form : impossible de charger les listes {keys} : {e}")
        return None

    # retour de l'index
    try:
        return options.index(value)
    except ValueError:
        return None  # valeur non trouvée → returne None pour ne pas présélectionner


def get_wikidata_csv_path(key: str):
    if key not in LIST_CSV_QID:
        raise KeyError(f"Clé wikidata inconnue : {key}")

    csv_path = os.path.join(WIKIDATA_DIR, LIST_CSV_QID[key])

    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"CSV introuvable : {csv_path}")

    return csv_path
