def extract_wikidata_id(url):
    # Extraire le QID Wikidata dans un lien
    if not url:
        return None
    return url.rsplit("/", 1)[-1]

def parse_group_concat(value):
    # parser les valeurs concaténées
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