import streamlit as st
import requests

def recup_wiki_peinture:

def recup_wiki_architecture:


def get_wikidata_properties(qid):
    url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"

    data = requests.get(url).json()
    entity = data['entities'][qid]['claims']

    def get_value(prop, idx=0):
        if prop not in entity:
            return None
        return entity[prop][idx]['mainsnak']['datavalue']['value']

    result = {}

    # P571 inception
    inception = get_value("P571")
    if inception:
        result["inception"] = inception.get("time")

    # P31 instance of (renvoie la liste des QID)
    if "P31" in entity:
        result["instance_of"] = [
            s["mainsnak"]["datavalue"]["value"]["id"]
            for s in entity["P31"]
        ]

    # P18 image (nom de fichier)
    image = get_value("P18")
    if image:
        result["image"] = image    # nom de fichier Commons

    # P17 pays
    country = get_value("P17")
    if country:
        result["country"] = country["id"]

    # Ville ⇒ P131 (rattachement administratif, le plus souvent la ville)
    admin = get_value("P131")
    if admin:
        result["city"] = admin["id"]

    # P625 coordonnées
    coords = get_value("P625")
    if coords:
        result["coordinates"] = {
            "lat": coords["latitude"],
            "lon": coords["longitude"]
        }

    # P84 architect → récupérer seulement le QID
    architect = get_value("P84")
    if architect:
        result["architect"] = architect["id"]

    return result


# Exemple d’usage : Q243 → Tour Eiffel
print(get_wikidata_properties("Q243"))


def recup_wiki_sculpture:

def recup_wiki_gravure: