"""Reconstruction de l'index TEI des œuvres depuis les notices JSON."""

import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import quoteattr


APP_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = APP_DIR.parent

DATA_DIRS = [
    APP_DIR / "data" / "entry_building",
    APP_DIR / "data" / "entry_artwork",
    APP_DIR / "data" / "entry_ensemble",
]

XML_PATH = REPO_DIR / "corpus" / "IndexOeuvres.xml"

TEI_NS = "http://www.tei-c.org/ns/1.0"


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
    seen_ids = {}

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
            source = data.get("QID_wikidata")

            if not isinstance(xml_id, str) or not xml_id.strip():
                raise ValueError(f"ID manquant ou invalide dans {json_file}")
            xml_id = xml_id.strip()
            if source is not None and not isinstance(source, str):
                raise ValueError(f"QID_wikidata invalide dans {json_file}")
            if xml_id in seen_ids:
                raise ValueError(
                    f"ID dupliqué dans les notices : {xml_id} "
                    f"({seen_ids[xml_id]} et {json_file})"
                )

            seen_ids[xml_id] = json_file
            oeuvres.append((xml_id, source.strip() if source else ""))

    # Le corpus conserve un élément racine TEI non qualifié et un listObject TEI.
    # Le namespace doit rester sur listObject, pas sur TEI.
    # ElementTree remonte la déclaration de namespace au niveau racine ;
    # on écrit donc le document XML de façon explicite pour respecter la structure voulue.
    temporary_path = XML_PATH.with_suffix(XML_PATH.suffix + ".tmp")
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        "<TEI>",
        f'  <listObject xmlns="{TEI_NS}">',
    ]

    for xml_id, source in sorted(oeuvres, key=lambda x: x[0]):
        attributes = [f"xml:id={quoteattr(xml_id)}"]
        if source:
            attributes.append(f"source={quoteattr(source)}")
        lines.append(f"    <object {' '.join(attributes)} />")

    lines.extend([
        "  </listObject>",
        "</TEI>",
    ])

    try:
        with open(temporary_path, "w", encoding="utf-8", newline="") as handle:
            handle.write("\n".join(lines) + "\n")
        ET.parse(temporary_path)
        os.replace(temporary_path, XML_PATH)
    finally:
        temporary_path.unlink(missing_ok=True)

    return [xml_id for xml_id, _ in oeuvres]