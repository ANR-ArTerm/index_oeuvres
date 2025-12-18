from SPARQLWrapper import SPARQLWrapper, JSON
import csv

from modules.wikidata.data_treatment import extract_wikidata_id, get_first_or_none, parse_group_concat, get_first_and_last_year, get_first_or_none_list

def get_monument_data(qid):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")

    query = f"""
    SELECT
        (GROUP_CONCAT(DISTINCT STR(?inception); SEPARATOR="|") AS ?inception)
        (GROUP_CONCAT(DISTINCT STR(?instanceOf); SEPARATOR="|") AS ?instanceOf)
        (GROUP_CONCAT(DISTINCT STR(?image); SEPARATOR="|") AS ?image)
        (GROUP_CONCAT(DISTINCT STR(?country); SEPARATOR="|") AS ?country)
        (GROUP_CONCAT(DISTINCT STR(?city); SEPARATOR="|") AS ?city)
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
    }}
    GROUP BY ?item
    """

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    row = results["results"]["bindings"][0]

    # Lecture des variables brutes
    inception_list = [
        extract_wikidata_id(a) for a in parse_group_concat(row.get("inception", {}).get("value")) if a
    ]
    instance_of_list = [
        extract_wikidata_id(a) for a in parse_group_concat(row.get("instanceOf", {}).get("value")) if a
    ]
    image_list       = parse_group_concat(row.get("image", {}).get("value"))
    country_list = [
        extract_wikidata_id(a) for a in parse_group_concat(row.get("country", {}).get("value")) if a
    ]
    city_list = [
        extract_wikidata_id(a) for a in parse_group_concat(row.get("city", {}).get("value")) if a
    ]

    lat_list = parse_group_concat(row.get("lat", {}).get("value"))
    lon_list = parse_group_concat(row.get("lon", {}).get("value"))
    architect_list = [
        extract_wikidata_id(a) for a in parse_group_concat(row.get("architect", {}).get("value")) if a
    ]

    # 🎯 Transformation :
    first_image   = get_first_or_none(image_list)
    first_lat     = float(get_first_or_none(lat_list)) if lat_list else None
    first_lon     = float(get_first_or_none(lon_list)) if lon_list else None
    first_city    = get_first_or_none_list(city_list)
    first_country = get_first_or_none_list(country_list)
    first_year, last_year = get_first_and_last_year(inception_list)


    # Variables finales
    return (
        first_year,       # ✔ année de début
        last_year,        # ✔ année de fin
        instance_of_list,
        first_image,      
        first_country,
        first_city,
        first_lat,        # ✔️ float
        first_lon,        # ✔️ float
        architect_list
    )