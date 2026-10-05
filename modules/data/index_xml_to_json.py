"""Synchronisation des index TEI personnes et lieux avec les listes JSON."""

from pathlib import Path
import json
import os
import xml.etree.ElementTree as ET


# =========================
# PATHS PORTABLES
# =========================

APP_DIR = Path(__file__).resolve().parents[2]
BASE_DIR = APP_DIR.parent

TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}
TEI_NAMESPACE = TEI_NS["tei"]
XML_ID_ATTRIBUTE = "{http://www.w3.org/XML/1998/namespace}id"
ET.register_namespace("", TEI_NAMESPACE)


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

    XML_PATH = BASE_DIR / "corpus" / "IndexPersonnes.xml"
    JSON_PATH = APP_DIR / "data" / "list_form" / "persons.json"
    WIKIDATA_PATH = APP_DIR / "data" / "list_form" / "persons_wikidata.json"

    # --- Vérification XML ---
    if not XML_PATH.exists():
        raise FileNotFoundError(
            "L'index xml des personnes n'est pas présents, "
            "veuillez cloner le dépôt github corpus"
        )

    # --- Lecture XML ---
    tree = ET.parse(XML_PATH)
    root = tree.getroot()

    person_elements = root.findall(".//tei:person", TEI_NS)
    people_by_id = {
        person.get(XML_ID_ATTRIBUTE): person
        for person in person_elements
        if person.get(XML_ID_ATTRIBUTE)
    }
    xml_ids = set(people_by_id)

    list_person = root.find(".//tei:listPerson", TEI_NS)
    if list_person is None:
        raise ValueError("IndexPersonnes.xml ne contient pas de <listPerson>")

    # --- Lecture JSON ---
    if JSON_PATH.exists():
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            persons_data = json.load(f)
        if not isinstance(persons_data, list):
            raise ValueError("persons.json doit contenir une liste d'identifiants")
        json_ids = {person_id for person_id in persons_data if isinstance(person_id, str)}
    else:
        json_ids = set()

    if WIKIDATA_PATH.exists():
        with open(WIKIDATA_PATH, "r", encoding="utf-8") as f:
            wikidata_by_id = json.load(f)
        if not isinstance(wikidata_by_id, dict):
            raise ValueError("persons_wikidata.json doit contenir un objet JSON")
    else:
        wikidata_by_id = {}

    # --- Différences intelligentes ---
    new_json_ids = sorted(xml_ids - json_ids)     # 🆕 à ajouter au JSON
    json_only_ids = sorted(json_ids - xml_ids)    # ⚠️ à ajouter au XML

    for person_id in json_only_ids:
        person = ET.SubElement(list_person, f"{{{TEI_NAMESPACE}}}person")
        person.set(XML_ID_ATTRIBUTE, person_id)
        source = wikidata_by_id.get(person_id)
        if isinstance(source, str) and source.strip():
            person.set("source", source.strip())
        people_by_id[person_id] = person

    for person_id, person in people_by_id.items():
        source = wikidata_by_id.get(person_id)
        if isinstance(source, str) and source.strip() and not person.get("source"):
            person.set("source", source.strip())

    # --- Mise à jour du JSON ---
    updated_json = sorted(json_ids | xml_ids)

    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(updated_json, f, ensure_ascii=False, indent=2)

    ET.indent(tree, space="  ")
    temporary_path = XML_PATH.with_suffix(XML_PATH.suffix + ".tmp")
    try:
        tree.write(temporary_path, encoding="utf-8", xml_declaration=True)
        ET.parse(temporary_path)
        os.replace(temporary_path, XML_PATH)
    finally:
        temporary_path.unlink(missing_ok=True)

    return new_json_ids, json_only_ids

def sync_place_ids():
    """
    Synchronise les xml:id du fichier TEI des lieux avec une liste JSON.

    Returns:
        new_json_ids (list[str]):
            lieux ajoutés au JSON
        json_only_ids (list[str]):
            lieux présents uniquement dans le JSON
            (donc à ajouter dans l'index XML)
    """

    XML_PATH = BASE_DIR / "corpus" / "IndexLieux.xml"
    JSON_PATH = APP_DIR / "data" / "list_form" / "places.json"
    
    # --- Vérification XML ---
    if not XML_PATH.exists():
        raise FileNotFoundError(
            "L'index xml des lieux n'est pas présent, "
            "veuillez cloner le dépôt github corpus"
        )

    # --- Lecture XML ---
    tree = ET.parse(XML_PATH)
    root = tree.getroot()

    xml_ids = {
        place.attrib.get("{http://www.w3.org/XML/1998/namespace}id")
        for place in root.findall(".//tei:place", TEI_NS)
        if place.attrib.get("{http://www.w3.org/XML/1998/namespace}id")
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