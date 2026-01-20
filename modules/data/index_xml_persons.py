from pathlib import Path
import json
import xml.etree.ElementTree as ET


# =========================
# PATHS PORTABLES
# =========================

BASE_DIR = Path(__file__).resolve().parents[3]

XML_PATH = BASE_DIR / "corpus" / "IndexPersonnes.xml"
JSON_PATH = Path("data") / "list_form" / "persons.json"


TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}


def sync_person_ids():
    """
    Synchronise les xml:id du fichier TEI avec une liste JSON.

    Returns:
        new_json_ids (list[str]):
            personnes ajoutées au JSON
        json_only_ids (list[str]):
            personnes présentes uniquement dans le JSON
            (donc à ajouter dans l'index XML)
    """

    # --- Vérification XML ---
    if not XML_PATH.exists():
        raise FileNotFoundError(
            "L'index xml des personnes n'est pas présents, "
            "veuillez cloner le dépôt github corpus"
        )

    # --- Lecture XML ---
    tree = ET.parse(XML_PATH)
    root = tree.getroot()

    xml_ids = {
        person.attrib.get("{http://www.w3.org/XML/1998/namespace}id")
        for person in root.findall(".//tei:person", TEI_NS)
        if person.attrib.get("{http://www.w3.org/XML/1998/namespace}id")
    }

    # --- Lecture JSON ---
    if JSON_PATH.exists():
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            json_ids = set(json.load(f))
    else:
        json_ids = set()

    # --- Différences intelligentes ---
    new_json_ids = sorted(xml_ids - json_ids)     # 🆕 à ajouter au JSON
    json_only_ids = sorted(json_ids - xml_ids)    # ⚠️ à ajouter au XML

    # --- Mise à jour du JSON ---
    updated_json = sorted(json_ids | xml_ids)

    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(updated_json, f, ensure_ascii=False, indent=2)

    return new_json_ids, json_only_ids