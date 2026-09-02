"""Reconstruction de l'index TEI des œuvres depuis les notices JSON."""

import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[3]

DATA_DIRS = [
    BASE_DIR / "data" / "entry_building",
    BASE_DIR / "data" / "entry_artwork",
    BASE_DIR / "data" / "entry_ensemble",
]

XML_PATH = BASE_DIR / "corpus" / "IndexOeuvres.xml"

TEI_NS = "http://www.tei-c.org/ns/1.0"
ET.register_namespace("", TEI_NS)


def sync_oeuvres_from_json():
    """
    Reconstruit entièrement IndexOeuvres.xml à partir des fichiers JSON.

    Returns:
        object_ids (list[str]): liste des xml:id générés

    Raises:
        FileNotFoundError: si IndexOeuvres.xml n'existe pas
        ValueError: si une notice est invalide ou si un ID est dupliqué
    """

    if not XML_PATH.exists():
        raise FileNotFoundError(
            "L'index XML des œuvres est absent : "
            "vérifiez que le dossier corpus a été cloné."
        )

    oeuvres = []
    seen_ids = set()

    for data_dir in DATA_DIRS:
        if not data_dir.exists():
            continue

        for json_file in sorted(data_dir.glob("*.json")):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, json.JSONDecodeError) as error:
                raise ValueError(f"Notice JSON illisible : {json_file}") from error

            if not isinstance(data, dict):
                raise ValueError(f"La notice doit être un objet JSON : {json_file}")

            xml_id = data.get("id")
            title = data.get("title")

            creators = data.get("creator", [])
            creator_name = "Inconnu"
            if isinstance(creators, list) and creators:
                first_creator = creators[0]
                if isinstance(first_creator, dict):
                    creator_name = first_creator.get("xml_id") or "Inconnu"

            if not isinstance(xml_id, str) or not xml_id.strip():
                raise ValueError(f"ID manquant ou invalide dans {json_file}")
            if not isinstance(title, str) or not title.strip():
                raise ValueError(f"Titre manquant ou invalide dans {json_file}")
            if xml_id in seen_ids:
                raise ValueError(f"ID dupliqué dans les notices : {xml_id}")

            seen_ids.add(xml_id)
            label = f"{creator_name}, {title.strip()}".strip(", ")
            oeuvres.append((xml_id, label))

    # Le corpus conserve un élément racine TEI non qualifié et un listObject TEI.
    root = ET.Element("TEI")
    list_object = ET.SubElement(root, f"{{{TEI_NS}}}listObject")

    for xml_id, label in sorted(oeuvres, key=lambda x: x[0]):
        obj = ET.SubElement(list_object, f"{{{TEI_NS}}}object")
        obj.set("{http://www.w3.org/XML/1998/namespace}id", xml_id)
        paragraph = ET.SubElement(obj, f"{{{TEI_NS}}}p")
        paragraph.text = label

    ET.indent(root, space="  ")
    temporary_path = XML_PATH.with_suffix(XML_PATH.suffix + ".tmp")
    try:
        ET.ElementTree(root).write(
            temporary_path,
            encoding="utf-8",
            xml_declaration=True,
        )
        ET.parse(temporary_path)
        os.replace(temporary_path, XML_PATH)
    finally:
        temporary_path.unlink(missing_ok=True)

    return [xml_id for xml_id, _ in oeuvres]