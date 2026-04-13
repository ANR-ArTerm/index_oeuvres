import json
from pathlib import Path
import re

from modules.data.load import load_all_entries, load_list_form, save_list_to_list_form

DATA_DIRS = [
    Path("data") / "entry_building",
    Path("data") / "entry_artwork",
    Path("data") / "entry_ensemble"
]


def fix_date_created(data):
    """
    Convertit startYear et endYear en int si ce sont des strings numériques
    """
    if "dateCreated" in data and isinstance(data["dateCreated"], dict):
        dc = data["dateCreated"]

        if "startYear" in dc and isinstance(dc["startYear"], str):
            if dc["startYear"].isdigit():
                dc["startYear"] = int(dc["startYear"])

        if "endYear" in dc and isinstance(dc["endYear"], str):
            if dc["endYear"].isdigit():
                dc["endYear"] = int(dc["endYear"])

    return data


def fix_location_fields(files):
    fixed_files = []

    for json_file in files:
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        location = data.get("location", {})
        loc_type = location.get("type")

        modified = False

        if loc_type == "holding_institution":
            if "place" in location:
                location.pop("place")
                modified = True

        elif loc_type == "place":
            if "institution" in location:
                location.pop("institution")
                modified = True

        elif loc_type == "unlocated":
            if "place" in location:
                location.pop("place")
                modified = True
            if "institution" in location:
                location.pop("institution")
                modified = True

        # correction dateCreated
        before = json.dumps(data)
        data = fix_date_created(data)
        after = json.dumps(data)

        if modified or before != after:
            json_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            fixed_files.append(json_file.name)

    return fixed_files


def verify_json_entries(data_dirs=DATA_DIRS):
    errors = []
    corrupted = []

    valid_pattern = re.compile(r"^[A-Za-z0-9]+$")

    for data_dir in data_dirs:
        for json_file in data_dir.glob("*.json"):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
            except Exception:
                corrupted.append(json_file)
                errors.append(f"[JSON INVALIDE] {json_file}")
                continue

            entry_id = data.get("id")
            title = data.get("title")

            if not entry_id or not title:
                corrupted.append(json_file)
                errors.append(f"[CHAMPS MANQUANTS] {json_file}")

            if entry_id and not valid_pattern.match(entry_id):
                corrupted.append(json_file)
                errors.append(
                    f"[ID INVALIDE] {json_file.name} : caractères spéciaux dans l'id '{entry_id}'"
                )

            if not valid_pattern.match(json_file.stem):
                corrupted.append(json_file)
                errors.append(
                    f"[NOM INVALIDE] {json_file.name} : caractères spéciaux dans le nom de fichier"
                )

            elif json_file.stem != entry_id:
                corrupted.append(json_file)
                errors.append(
                    f"[NOM ≠ ID] {json_file.name} ≠ {entry_id}.json"
                )

            location = data.get("location", {})
            loc_type = location.get("type")

            place = location.get("place")
            institution = location.get("institution")

            if loc_type == "holding_institution":
                if place:
                    corrupted.append(json_file)
                    errors.append(
                        f"[LOCATION INVALIDE] {json_file.name} : "
                        "holding_institution ne doit pas contenir 'place'"
                    )

            elif loc_type == "place":
                if institution:
                    corrupted.append(json_file)
                    errors.append(
                        f"[LOCATION INVALIDE] {json_file.name} : "
                        "place ne doit pas contenir 'institution'"
                    )

            elif loc_type == "unlocated":
                if place or institution:
                    corrupted.append(json_file)
                    errors.append(
                        f"[LOCATION INVALIDE] {json_file.name} : "
                        "unlocated ne doit contenir ni 'place' ni 'institution'"
                    )

    text = (
        "✅ Tous les fichiers JSON sont valides."
        if not errors
        else "❌ Problèmes détectés :\n" + "\n".join(errors)
    )

    return text, corrupted