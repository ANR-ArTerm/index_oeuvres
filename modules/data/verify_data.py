import json
from pathlib import Path

from modules.data.load import load_all_entries, load_list_form, save_list_to_list_form

DATA_DIRS = [
    Path("data") / "entry_architecture",
    Path("data") / "entry_peinture",
    Path("data") / "entry_ensemble"
]

def verify_json_entries(data_dirs=DATA_DIRS):
    errors = []
    corrupted = []  # <- fichiers à éditer

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

            elif json_file.stem != entry_id:
                corrupted.append(json_file)
                errors.append(
                    f"[NOM ≠ ID] {json_file.name} ≠ {entry_id}.json"
                )

    text = "✅ Tous les fichiers JSON sont valides." if not errors \
        else "❌ Problèmes détectés :\n" + "\n".join(errors)

    return text, corrupted




