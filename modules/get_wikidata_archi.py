from SPARQLWrapper import SPARQLWrapper, JSON
import csv

def extract_wikidata_id(url):
    if not url:
        return None
    return url.rsplit("/", 1)[-1]

def parse_group_concat(value):
    if value is None or value == "":
        return []
    return value.split("|")

def extract_year(date_string):
    """
    Extrait l'année d'une date Wikidata du type '+1887-01-28T00:00:00Z'
    et la retourne sous forme d'entier.
    """
    if not date_string:
        return None
    
    year_str = date_string.strip("+").split("-")[0]
    
    # Convertit en int pour permettre le tri
    try:
        return int(year_str)
    except ValueError:
        return None


def get_first_and_last_year(dates):
    """
    Prend une liste de dates Wikidata et renvoie :
    - première année (min)
    - dernière année (max)
    """
    if not dates:
        return None, None

    # Conversion des dates Wikidata en années entières
    years = [extract_year(d) for d in dates if d]

    # Filtre les valeurs invalides
    years = [y for y in years if y is not None]

    if not years:
        return None, None

    # 🔥 TRI CHRONOLOGIQUE
    years = sorted(years)

    # Retourne la première et la dernière année
    return years[0], years[-1]


def get_first_or_none(values):
    if not values:
        return None
    return values[0]


def get_first_or_none_list(values):
    """
    Renvoie une liste contenant uniquement la première valeur de la liste.
    Si la liste est vide, renvoie [None].
    """
    if not values:
        return [None]
    return [values[0]]


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

    lat_list         = parse_group_concat(row.get("lat", {}).get("value"))
    lon_list         = parse_group_concat(row.get("lon", {}).get("value"))
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

def wikidata_to_xml_ids_or_qid(qid_list, csv_path):
    # si pas trouvé → on garde le QID
    # mapping wikidata_qid -> xml_id
    # à utiliser pour les personnes et les lieux
    mapping = {}

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            mapping[row["wikidata_qid"]] = row["xml_id"]

    # si pas trouvé → on garde le QID
    return [mapping.get(qid, qid) for qid in qid_list]

import csv

def wikidata_to_xml_ids_or_none(qid_list, key: str):
    """
    À utiliser pour les typologies / techniques.
    - évite les doublons
    - ignore les labels vides
    - retourne un seul label ou None
    """
    if isinstance(qid_list, str):
        qid_list = [qid_list]

    labels_set = set()

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            qid = row.get("wikidata_qid")
            label = row.get("label_fr")

            if qid in qid_list and label:
                labels_set.add(label.strip())

    if not labels_set:
        return None

    # retourne UN seul label (stable)
    return sorted(labels_set)[0]


