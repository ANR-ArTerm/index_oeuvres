import csv
import json
from pathlib import Path

# Fichiers
CSV_PATH = ".idea/typologies_artwork/artwork_typology.csv"  # à adapter
JSON_DIR = Path("data/entry_artwork")

# Lecture du CSV
mapping = {}

with open(CSV_PATH, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        technique = row["technique"].strip().lower()
        typologie = row["typologie"].strip()
        mapping[technique] = typologie

# Parcours des JSON
for json_file in JSON_DIR.glob("*.json"):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    technique = data.get("materialsAndTechniques", "")

    if technique:
        typology = mapping.get(technique.strip().lower())

        if typology is not None:
            data["typology"] = typology
        else:
            print(f"Aucune correspondance pour : '{technique}' ({json_file.name})")
            data["typology"] = ""

    else:
        data["typology"] = ""

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

print("Terminé.")