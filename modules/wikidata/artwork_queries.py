"""Requêtes Wikidata destinées aux notices d'œuvres."""

import re

from SPARQLWrapper import JSON, SPARQLWrapper

from modules.wikidata.data_treatment import extract_wikidata_id, parse_group_concat


def _extract_year(date_value: str) -> int | None:
    match = re.match(r"([+-]?\d+)-\d{2}-\d{2}", date_value)
    return int(match.group(1)) if match else None


def get_artwork_data(url: str) -> dict:
    """Récupère les informations descriptives disponibles pour une œuvre."""
    qid = extract_wikidata_id(url)
    if not qid:
        raise ValueError("QID Wikidata invalide")

    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setQuery(
        f"""
        SELECT
            (SAMPLE(?itemLabel) AS ?label)
            (SAMPLE(?titleFr) AS ?titleFr)
            (SAMPLE(?titleEn) AS ?titleEn)
            (SAMPLE(?inception) AS ?inception)
            (GROUP_CONCAT(DISTINCT ?materialLabel; SEPARATOR="|") AS ?materials)
            (GROUP_CONCAT(DISTINCT ?techniqueLabel; SEPARATOR="|") AS ?techniques)
            (GROUP_CONCAT(DISTINCT STR(?image); SEPARATOR="|") AS ?images)
        WHERE {{
            VALUES ?item {{ wd:{qid} }}

            OPTIONAL {{
                ?item wdt:P1476 ?titleFr.
                FILTER(LANG(?titleFr) = "fr")
            }}
            OPTIONAL {{
                ?item wdt:P1476 ?titleEn.
                FILTER(LANG(?titleEn) = "en")
            }}
            OPTIONAL {{ ?item wdt:P571 ?inception. }}
            OPTIONAL {{ ?item wdt:P186 ?material. }}
            OPTIONAL {{ ?item wdt:P2079 ?technique. }}
            OPTIONAL {{ ?item wdt:P18 ?image. }}

            SERVICE wikibase:label {{
                bd:serviceParam wikibase:language "fr,en".
            }}
        }}
        GROUP BY ?item
        """
    )
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    bindings = results.get("results", {}).get("bindings", [])
    if not bindings:
        raise ValueError(f"Aucune œuvre trouvée pour {qid}")

    row = bindings[0]

    def value(name: str) -> str:
        return row.get(name, {}).get("value", "").strip()

    title = value("titleFr") or value("titleEn") or value("label")
    year = _extract_year(value("inception"))
    materials = parse_group_concat(value("materials"))
    techniques = parse_group_concat(value("techniques"))
    images = list(dict.fromkeys(parse_group_concat(value("images"))))

    description_parts = []
    if materials:
        description_parts.append("Matériaux : " + ", ".join(materials))
    if techniques:
        description_parts.append("Techniques : " + ", ".join(techniques))

    return {
        "title": title,
        "year": year,
        "materialsAndTechniques": "; ".join(description_parts),
        "images": images,
    }