import streamlit as st
import json
import time
from pathlib import Path

from modules.data_loader import load_all_entries, delete_notice

def normalize_notice_ensemble(o):
    """
    Normalise une notice 'ensemble' en remplaçant les champs vides
    par des chaînes 'AUCUN ...' pour garantir le bon fonctionnement de la recherche.
    """

    o_display = {}

    # Champs principaux
    o_display["id"] = o.get("id") or "AUCUN ID"
    o_display["title"] = o.get("title") or "AUCUN TITRE"
    o_display["entry_type"] = o.get("entry_type") or "AUCUN TYPE"
    o_display["typology"] = o.get("typology") or "AUCUNE TYPOLOGIE"
    o_display["description"] = o.get("description") or "AUCUNE DESCRIPTION"
    o_display["commentary"] = o.get("commentary") or "AUCUN COMMENTAIRE"

    # Date
    date = o.get("dateCreated", {})
    o_display["date_text"] = date.get("text") or "AUCUNE DATE"
    o_display["start_year"] = date.get("startYear") or "AUCUN DÉBUT"
    o_display["end_year"] = date.get("endYear") or "AUCUNE FIN"

    # Localisation (holding_institution OU place)
    # Localisation (robuste)
    location = o.get("location") or {}
    location_type = location.get("type")

    # Valeurs par défaut
    o_display["location_type"] = "AUCUNE LOCALISATION"
    o_display["location_city"] = "AUCUNE VILLE"
    o_display["location_country"] = "AUCUN PAYS"
    o_display["latitude"] = "AUCUNE LATITUDE"
    o_display["longitude"] = "AUCUNE LONGITUDE"
    o_display["location_name"] = "AUCUNE INSTITUTION"
    o_display["inventory_number"] = "AUCUN NUMÉRO"
    o_display["location_url"] = "AUCUNE URL"

    if location_type == "place":
        place = location.get("place") or {}
        coordinates = place.get("coordinates") or {}

        o_display["location_type"] = "lieu"
        o_display["location_city"] = place.get("city") or "AUCUNE VILLE"
        o_display["location_country"] = place.get("country") or "AUCUN PAYS"
        o_display["latitude"] = coordinates.get("latitude") or "AUCUNE LATITUDE"
        o_display["longitude"] = coordinates.get("longitude") or "AUCUNE LONGITUDE"

    elif location_type == "holding_institution":
        institution = location.get("institution") or {}

        o_display["location_type"] = "institution"
        o_display["location_name"] = institution.get("name") or "AUCUNE INSTITUTION"
        o_display["location_city"] = institution.get("place") or "AUCUNE VILLE"
        o_display["inventory_number"] = institution.get("inventory_number") or "AUCUN NUMÉRO"
        o_display["location_url"] = institution.get("url") or "AUCUNE URL"


    # Créateurs
    creators = o.get("creator", [])
    if not creators:
        o_display["creators_display"] = ["AUCUN CRÉATEUR"]
    else:
        display_list = []
        for c in creators:
            nom = c.get("xml_id") or "CRÉATEUR INCONNU"
            role = c.get("role")
            display_list.append(f"{nom} ({role})" if role else nom)
        o_display["creators_display"] = display_list

    # Œuvres liées
    related = o.get("related_works", [])
    if not related:
        o_display["related_works_display"] = ["AUCUNE ŒUVRE LIÉE"]
    else:
        o_display["related_works_display"] = [
            f"{r.get('xml_id_work') or 'ŒUVRE INCONNUE'} ({r.get('link_type') or 'lien inconnu'})"
            for r in related
        ]

    # Bibliographie
    biblio = o.get("bibliography", [])
    if not biblio:
        o_display["biblio_display"] = ["AUCUNE BIBLIOGRAPHIE"]
    else:
        o_display["biblio_display"] = [
            f"{b.get('zotero_key') or 'SANS CLÉ'} ({b.get('location') or 'SANS LOCALISATION'})"
            for b in biblio
        ]

    # Illustrations
    illus = o.get("illustrations", [])
    if not illus:
        o_display["illustrations_display"] = ["AUCUNE ILLUSTRATION"]
    else:
        o_display["illustrations_display"] = [
            i.get("url") or "AUCUNE URL" for i in illus
        ]
    o_display.setdefault("illustrations_display", ["AUCUNE ILLUSTRATION"])

    # Historique
    history = o.get("history", [])
    if not history:
        o_display["history_display"] = ["AUCUN HISTORIQUE"]
    else:
        o_display["history_display"] = [
            f"{h.get('type') or 'événement'} – {h.get('date') or 'date inconnue'}"
            for h in history
        ]

    return o_display