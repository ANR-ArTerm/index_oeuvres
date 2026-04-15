import os
import glob
import xml.etree.ElementTree as ET
import streamlit as st
from pathlib import Path
import json

from modules.data.load import get_all_objects_ids_flat_sorted

def verifier_objectnames():
    """
    Parcourt les fichiers XML TEI dans les dossiers définis,
    extrait les identifiants des <objectName ref="#..."> dans <text>
    et affiche dans Streamlit ceux qui ne sont pas dans la liste autorisée.
    """

    BASE_DIR = Path(__file__).resolve().parents[3]

    dossiers = [
        BASE_DIR / "corpus" / "Peinture",
        BASE_DIR / "corpus" / "Architecture",
        BASE_DIR / "corpus" / "Perspective",
    ]

    liste_identifiants = set(get_all_objects_ids_flat_sorted())

    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

    resultats = {}

    for dossier in dossiers:
        fichiers = glob.glob(os.path.join(dossier, "*.xml"))

        for fichier in fichiers:
            try:
                tree = ET.parse(fichier)
                root = tree.getroot()

                inconnus = set()

                text_elem = root.find(".//tei:text", ns)
                if text_elem is None:
                    continue

                for obj in text_elem.findall(".//tei:objectName", ns):
                    ref = obj.get("ref")
                    if ref and ref.startswith("#"):
                        identifiant = ref[1:]

                        if identifiant not in liste_identifiants:
                            inconnus.add(identifiant)

                if inconnus:
                    resultats[fichier] = sorted(inconnus)

            except ET.ParseError:
                st.error(f"❌ Erreur de parsing : {fichier}")

    # ===== AFFICHAGE STREAMLIT =====

    if not resultats:
        st.success("✅ Tous les identifiants objectName sont valides !")
        return

    st.warning(f"⚠️ {len(resultats)} fichier(s) contiennent des identifiants inconnus")

    for fichier, ids in resultats.items():
        with st.expander(f"📄 {os.path.basename(fichier)} ({len(ids)} erreur(s))"):
            for i in ids:
                st.write(f"❌ `{i}`")

def verifier_persnames():
    """
    Vérifie les <persName ref="#..."> dans <text> des fichiers TEI
    et les compare avec une liste d'identifiants issue d'un JSON.
    """

    BASE_DIR = Path(__file__).resolve().parents[3]

    noms_dossiers = ["Peinture", "Architecture", "Perspective"]
    dossiers = [BASE_DIR / "corpus" / nom for nom in noms_dossiers]

    # Charger la liste JSON
    json_path = BASE_DIR / "index_oeuvres" / "data" / "list_form" / "persons.json"
    with open(json_path, "r", encoding="utf-8") as f:
        liste_identifiants = set(json.load(f))

    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

    resultats = {}

    for dossier in dossiers:
        for fichier in dossier.glob("*.xml"):
            try:
                tree = ET.parse(fichier)
                root = tree.getroot()

                inconnus = set()

                text_elem = root.find(".//tei:text", ns)
                if text_elem is None:
                    continue

                # Recherche des persName
                for pers in text_elem.findall(".//tei:persName", ns):
                    ref = pers.get("ref")
                    if ref and ref.startswith("#"):
                        identifiant = ref[1:]

                        if identifiant not in liste_identifiants:
                            inconnus.add(identifiant)

                if inconnus:
                    resultats[fichier] = sorted(inconnus)

            except ET.ParseError:
                st.error(f"❌ Erreur de parsing : {fichier.name}")

    # ===== AFFICHAGE STREAMLIT =====

    if not resultats:
        st.success("✅ Tous les identifiants persName sont valides !")
        return

    st.warning(f"⚠️ {len(resultats)} fichier(s) contiennent des persName inconnus")

    for fichier, ids in resultats.items():
        with st.expander(f"👤 {fichier.name} ({len(ids)} erreur(s))"):
            for i in ids:
                st.write(f"❌ `{i}`")

def verifier_placenames():
    """
    Vérifie les <placeName ref="#..."> dans <text> des fichiers TEI
    et les compare avec une liste d'identifiants issue d'un JSON.
    """

    BASE_DIR = Path(__file__).resolve().parents[3]

    noms_dossiers = ["Peinture", "Architecture", "Perspective"]
    dossiers = [BASE_DIR / "corpus" / nom for nom in noms_dossiers]

    # Charger la liste JSON
    json_path = BASE_DIR / "index_oeuvres" / "data" / "list_form" / "places.json"
    with open(json_path, "r", encoding="utf-8") as f:
        liste_identifiants = set(json.load(f))

    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

    resultats = {}

    for dossier in dossiers:
        for fichier in dossier.glob("*.xml"):
            try:
                tree = ET.parse(fichier)
                root = tree.getroot()

                inconnus = set()

                text_elem = root.find(".//tei:text", ns)
                if text_elem is None:
                    continue

                # Recherche des placeName
                for place in text_elem.findall(".//tei:placeName", ns):
                    ref = place.get("ref")
                    if ref and ref.startswith("#"):
                        identifiant = ref[1:]

                        if identifiant not in liste_identifiants:
                            inconnus.add(identifiant)

                if inconnus:
                    resultats[fichier] = sorted(inconnus)

            except ET.ParseError:
                st.error(f"❌ Erreur de parsing : {fichier.name}")

    # ===== AFFICHAGE STREAMLIT =====

    if not resultats:
        st.success("✅ Tous les identifiants placeName sont valides !")
        return

    st.warning(f"⚠️ {len(resultats)} fichier(s) contiennent des placeName inconnus")

    for fichier, ids in resultats.items():
        with st.expander(f"📍 {fichier.name} ({len(ids)} erreur(s))"):
            for i in ids:
                st.write(f"❌ `{i}`")