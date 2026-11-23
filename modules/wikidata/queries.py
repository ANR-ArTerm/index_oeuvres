from SPARQLWrapper import SPARQLWrapper, JSON
import csv
from urllib.parse import quote

from modules.wikidata.data_treatment import extract_wikidata_id, get_first_or_none, parse_group_concat, get_first_and_last_year
from modules.wikidata.artwork_queries import (
    _commons_image_metadata,
    _extract_year,
    _get_entity,
    _get_entity_labels,
)

def get_monument_data(url):
    qid = extract_wikidata_id(url)
    
    if not qid:
        raise ValueError("QID Wikidata invalide")

    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")

    query = f"""
    SELECT
        (GROUP_CONCAT(DISTINCT STR(?inception); SEPARATOR="|") AS ?inception)
        (GROUP_CONCAT(DISTINCT STR(?instanceOf); SEPARATOR="|") AS ?instanceOf)
        (GROUP_CONCAT(DISTINCT STR(?image); SEPARATOR="|") AS ?image)
        (GROUP_CONCAT(DISTINCT ?countryLabel; SEPARATOR="|") AS ?country)
        (GROUP_CONCAT(DISTINCT ?cityLabel; SEPARATOR="|") AS ?city)
        (GROUP_CONCAT(DISTINCT STR(?lat); SEPARATOR="|") AS ?lat)
        (GROUP_CONCAT(DISTINCT STR(?lon); SEPARATOR="|") AS ?lon)
        (GROUP_CONCAT(DISTINCT STR(?architect); SEPARATOR="|") AS ?architect)
    WHERE {{
      VALUES ?item {{ wd:{qid} }}

      OPTIONAL {{ ?item wdt:P571 ?inception. }}
      OPTIONAL {{ ?item wdt:P31 ?instanceOf. }}
      OPTIONAL {{ ?item wdt:P18 ?image. }}
      OPTIONAL {{ ?item wdt:P17 ?country. }}
      OPTIONAL {{ ?item wdt:P131 ?city. }}

      OPTIONAL {{
        ?item wdt:P625 ?coords.
        BIND(geof:latitude(?coords) AS ?lat)
        BIND(geof:longitude(?coords) AS ?lon)
      }}

      OPTIONAL {{ ?item wdt:P84 ?architect. }}

            SERVICE wikibase:label {{
                bd:serviceParam wikibase:language "fr,it,en".
            }}
    }}
    GROUP BY ?item
    """

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    bindings = results["results"]["bindings"]
    if not bindings:
        return {
            "title": "",
            "year": None,
            "end_year": None,
            "creator_qids": [],
            "creator_labels": [],
            "institutions": [],
            "images": [],
            "instance_of": [],
            "instance_of_labels": [],
            "first_year": None,
            "last_year": None,
            "image": None,
            "country": None,
            "city": None,
            "latitude": None,
            "longitude": None,
            "architects": [],
        }
    row = bindings[0]

    # Lecture des variables brutes
    inception_list = parse_group_concat(row.get("inception", {}).get("value"))
    instance_of_list = [
        extract_wikidata_id(a) for a in parse_group_concat(row.get("instanceOf", {}).get("value")) if a
    ]
    image_list       = parse_group_concat(row.get("image", {}).get("value"))
    country_list = parse_group_concat(row.get("country", {}).get("value"))
    city_list = parse_group_concat(row.get("city", {}).get("value"))

    lat_list = parse_group_concat(row.get("lat", {}).get("value"))
    lon_list = parse_group_concat(row.get("lon", {}).get("value"))
    architect_list = [
        extract_wikidata_id(a) for a in parse_group_concat(row.get("architect", {}).get("value")) if a
    ]

    # 🎯 Transformation :
    first_image   = get_first_or_none(image_list)
    first_lat     = float(get_first_or_none(lat_list)) if lat_list else None
    first_lon     = float(get_first_or_none(lon_list)) if lon_list else None
    first_city    = get_first_or_none(city_list)
    first_country = get_first_or_none(country_list)
    first_year, last_year = get_first_and_last_year(inception_list)

    entity = _get_entity(qid)
    claims = entity.get("claims", {})
    labels = entity.get("labels", {})

    title = next(
        (labels[language]["value"] for language in ("fr", "it", "en") if language in labels),
        "",
    )

    end_year = None
    for claim in claims.get("P576", []):
        if claim.get("rank") == "deprecated":
            continue
        value = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
        if isinstance(value, dict):
            end_year = _extract_year(value.get("time", ""))
            if end_year is not None:
                break

    creator_qids = list(dict.fromkeys(
        value["id"]
        for claim in claims.get("P84", [])
        if isinstance((value := claim.get("mainsnak", {}).get("datavalue", {}).get("value")), dict)
        and value.get("id")
    ))
    entity_labels = _get_entity_labels(list(dict.fromkeys(
        creator_qids + instance_of_list
    )))

    image_urls = []
    for claim in claims.get("P18", []):
        filename = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
        if isinstance(filename, str) and filename:
            image_urls.append(
                f"https://commons.wikimedia.org/wiki/Special:FilePath/{quote(filename)}"
            )
    images = _commons_image_metadata(image_urls)

    # Variables finales
    monument_data = {
        "title": title,
        "year": first_year,
        "end_year": end_year,
        "creator_qids": creator_qids,
        "creator_labels": [
            entity_labels.get(creator_qid, creator_qid)
            for creator_qid in creator_qids
        ],
        "institutions": [],
        "images": images,
        "instance_of_labels": [
            entity_labels.get(qid_value, qid_value)
            for qid_value in instance_of_list
        ],
        "first_year": first_year,
        "last_year": last_year,
        "instance_of": instance_of_list,
        "image": first_image,
        "country": first_country,
        "city": first_city,
        "latitude": first_lat,
        "longitude": first_lon,
        "architects": architect_list
    }

    return monument_data