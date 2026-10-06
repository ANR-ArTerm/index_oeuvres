"""Requêtes Wikidata destinées aux notices d'œuvres."""

import csv
import re
from pathlib import Path

from SPARQLWrapper import JSON, SPARQLWrapper

from modules.wikidata.data_treatment import extract_wikidata_id, parse_group_concat
from modules.data.load import get_wikidata_csv_path


def _extract_year(date_value: str) -> int | None:
    match = re.match(r"([+-]?\d+)-\d{2}-\d{2}", date_value)
    return int(match.group(1)) if match else None


def _load_technique_labels() -> dict[str, str]:
    csv_path = Path(get_wikidata_csv_path("techniques"))
    if not csv_path.exists():
        return {}

    with open(csv_path, newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file, delimiter=";")
        if not reader.fieldnames:
            return {}
        return {
            row["wikidata_qid"].strip(): row["label_fr"].strip()
            for row in reader
            if row.get("wikidata_qid") and row.get("label_fr")
        }


def _save_technique_labels(labels: dict[str, str], new_labels: dict[str, str]) -> None:
    if not new_labels:
        return

    csv_path = Path(get_wikidata_csv_path("techniques"))
    merged_labels = {**labels, **new_labels}
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["wikidata_qid", "label_fr"],
            delimiter=";",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(
            {"wikidata_qid": qid, "label_fr": label}
            for qid, label in sorted(merged_labels.items())
        )


def get_artwork_data(url: str) -> dict:
    """Récupère les informations descriptives disponibles pour une œuvre."""
    qid = extract_wikidata_id(url)
    if not qid:
        raise ValueError("QID Wikidata invalide")

    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setQuery(
        f"""
        SELECT DISTINCT
            ?itemLabel ?titleFr ?titleIt ?titleEn ?inception
            ?material ?materialLabelFr ?technique ?techniqueLabelFr ?image
        WHERE {{
            VALUES ?item {{ wd:{qid} }}

            OPTIONAL {{
                ?item wdt:P1476 ?titleFr.
                FILTER(LANG(?titleFr) = "fr")
            }}
            OPTIONAL {{
                ?item wdt:P1476 ?titleIt.
                FILTER(LANG(?titleIt) = "it")
            }}
            OPTIONAL {{
                ?item wdt:P1476 ?titleEn.
                FILTER(LANG(?titleEn) = "en")
            }}
            OPTIONAL {{ ?item wdt:P571 ?inception. }}
            OPTIONAL {{
                ?item wdt:P186 ?material.
                OPTIONAL {{
                    ?material rdfs:label ?materialLabelFr.
                    FILTER(LANG(?materialLabelFr) = "fr")
                }}
            }}
            OPTIONAL {{
                ?item wdt:P2079 ?technique.
                OPTIONAL {{
                    ?technique rdfs:label ?techniqueLabelFr.
                    FILTER(LANG(?techniqueLabelFr) = "fr")
                }}
            }}
            OPTIONAL {{ ?item wdt:P18 ?image. }}

            SERVICE wikibase:label {{
                bd:serviceParam wikibase:language "fr,it,en".
            }}
        }}
        """
    )
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    bindings = results.get("results", {}).get("bindings", [])
    if not bindings:
        raise ValueError(f"Aucune œuvre trouvée pour {qid}")

    title = ""
    year = None
    images = []
    material_terms = {}
    technique_terms = {}

    for row in bindings:
        def value(name: str) -> str:
            return row.get(name, {}).get("value", "").strip()

        title = title or value("titleFr") or value("titleIt") or value("titleEn") or value("itemLabel")
        year = year if year is not None else _extract_year(value("inception"))

        image_url = value("image")
        if image_url and image_url not in images:
            images.append(image_url)

        for entity_name, label_name, terms in (
            ("material", "materialLabelFr", material_terms),
            ("technique", "techniqueLabelFr", technique_terms),
        ):
            entity_url = value(entity_name)
            entity_qid = extract_wikidata_id(entity_url)
            if entity_qid:
                terms[entity_qid] = terms.get(entity_qid) or value(label_name)

    technique_labels = _load_technique_labels()
    new_technique_labels = {
        qid: label
        for qid, label in {**material_terms, **technique_terms}.items()
        if label and qid not in technique_labels
    }
    _save_technique_labels(technique_labels, new_technique_labels)

    mapped_materials = [
        technique_labels.get(qid) or new_technique_labels.get(qid) or label
        for qid, label in material_terms.items()
    ]
    mapped_techniques = [
        technique_labels.get(qid) or new_technique_labels.get(qid) or label
        for qid, label in technique_terms.items()
    ]
    materials_and_techniques = list(dict.fromkeys(
        label for label in mapped_materials + mapped_techniques if label
    ))

    return {
        "title": title,
        "year": year,
        "materialsAndTechniques": "; ".join(materials_and_techniques),
        "images": images,
    }