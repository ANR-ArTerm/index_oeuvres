from pathlib import Path
import json
import xml.etree.ElementTree as ET


BASE_DIR = Path(__file__).resolve().parents[3]

DATA_DIRS = [
    Path("data") / "entry_architecture",
    Path("data") / "entry_peinture",
]

XML_PATH = BASE_DIR / "corpus" / "IndexOeuvres.xml"

TEI_NS = "http://www.tei-c.org/ns/1.0"
NSMAP = {"tei": TEI_NS}

ET.register_namespace("", TEI_NS)

def sync_oeuvres_from_json():
    """
    Reconstruit entièrement IndexOeuvres.xml à partir des fichiers JSON.

    Returns:
        object_ids (list[str]): liste des xml:id générés

    Raises:
        FileNotFoundError: si IndexOeuvres.xml n'existe pas
    """

    # --- Le XML doit exister ---
    if not XML_PATH.exists():
        raise FileNotFoundError(
            "L'index xml des œuvres n'est pas présent,"
            "veuillez cloner le dépôt github corpus"
        )

    # --- Collecte des données depuis les JSON ---
    oeuvres = []

    for data_dir in DATA_DIRS:
        if not data_dir.exists():
            continue

        for json_file in sorted(data_dir.glob("*.json")):
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            xml_id = data.get("id")
            title = data.get("title", "").strip()

            creators = data.get("creator", [])
            creator_name = creators[0]["xml_id"] if creators else "Inconnu"

            if not xml_id or not title:
                continue

            label = f"{creator_name}, {title}".strip(", ")
            oeuvres.append((xml_id, label))

    # --- Reconstruction complète du XML ---
    root = ET.Element("TEI")
    list_object = ET.SubElement(root, f"{{{TEI_NS}}}listObject")

    for xml_id, label in sorted(oeuvres, key=lambda x: x[0]):
        obj = ET.SubElement(list_object, f"{{{TEI_NS}}}object")
        obj.set("{http://www.w3.org/XML/1998/namespace}id", xml_id)

        p = ET.SubElement(obj, f"{{{TEI_NS}}}p")
        p.text = label

    # --- Écriture (écrasement total) ---
    tree = ET.ElementTree(root)

    ET.indent(tree, space="    ", level=0)

    tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)

    return [xml_id for xml_id, _ in oeuvres]