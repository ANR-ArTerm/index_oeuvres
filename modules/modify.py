import streamlit as st
import json
import os

from modules.data_loader import (
    load_all_oeuvres,
    save_oeuvre,
    delete_oeuvre,
    DATA_DIR
)

def render_modify_form():

    # Chargement des œuvres + chemins
    oeuvres, paths = load_all_oeuvres()

    if "selected_idx" not in st.session_state:
        st.session_state.selected_idx = None
    if "selected_path" not in st.session_state:
        st.session_state.selected_path = None
    if "form_version" not in st.session_state:
        st.session_state.form_version = 0

    # Rien à modifier → on sort
    if st.session_state.selected_idx is None:
        return

    current = oeuvres[st.session_state.selected_idx]
    path = st.session_state.selected_path

    st.info(f"✏️ Modification : {current.get('titre', 'Sans titre')}")

    # --- listes pour autocomplétion ---
    existing_type = list({o.get("type_oeuvre", "") for o in oeuvres})
    existing_artist = list({o.get("artiste", "") for o in oeuvres})
    existing_technique = list({o.get("technique", "") for o in oeuvres})
    existing_city = list({o.get("ville", "") for o in oeuvres})
    existing_institution = list({o.get("institution", "") for o in oeuvres})

    # --- FORMULAIRE ---
    with st.form("oeuvre_form"):

        # ID obligatoire
        id_input = st.text_input("XML:ID de l'oeuvre *", current.get("id", ""))

        # --- TYPE ---
        type_key = f"type_oeuvre_{st.session_state.form_version}"
        if current.get("type_oeuvre") and type_key not in st.session_state:
            st.session_state[type_key] = current["type_oeuvre"]

        type_input = st_smart_text_input(
            "Type de l'oeuvre",
            options=existing_type,
            placeholder=current.get("type_oeuvre", "Sélectionner ou saisir un type..."),
            key=type_key
        )
        if not type_input:
            type_input = current.get("type_oeuvre", "")

        # --- ARTISTE ---
        artiste_key = f"artiste_{st.session_state.form_version}"
        if current.get("artiste") and artiste_key not in st.session_state:
            st.session_state[artiste_key] = current["artiste"]

        artiste_input = st_smart_text_input(
            "XML:ID de l'artiste (appuyer sur entrée!) *",
            options=existing_artist,
            placeholder=current.get("artiste", "Sélectionner ou saisir un artiste..."),
            key=artiste_key
        )
        if not artiste_input:
            artiste_input = current.get("artiste", "")

        # --- AUTRES CHAMPS ---
        titre_input = st.text_input("Titre *", current.get("titre", ""))
        date_input = st.text_input("Date", current.get("date", ""))

        # Technique
        technique_key = f"technique_{st.session_state.form_version}"
        if current.get("technique") and technique_key not in st.session_state:
            st.session_state[technique_key] = current["technique"]

        technique_input = st_smart_text_input(
            "Technique",
            options=existing_technique,
            placeholder=current.get("technique", ""),
            key=technique_key
        )
        if not technique_input:
            technique_input = current.get("technique", "")

        # Ville
        ville_key = f"ville_{st.session_state.form_version}"
        if current.get("ville") and ville_key not in st.session_state:
            st.session_state[ville_key] = current["ville"]

        ville_input = st_smart_text_input(
            "Ville",
            options=existing_city,
            placeholder=current.get("ville", ""),
            key=ville_key
        )
        if not ville_input:
            ville_input = current.get("ville", "")

        # Institution
        institution_key = f"institution_{st.session_state.form_version}"
        if current.get("institution") and institution_key not in st.session_state:
            st.session_state[institution_key] = current["institution"]

        institution_input = st_smart_text_input(
            "Institution",
            options=existing_institution,
            placeholder=current.get("institution", ""),
            key=institution_key
        )
        if not institution_input:
            institution_input = current.get("institution", "")

        inventaire_input = st.text_input("Inventaire", current.get("inventaire", ""))

        # --- BOUTONS ---
        col_submit, col_cancel = st.columns([1, 1])
        with col_submit:
            submitted = st.form_submit_button("💾 Enregistrer")
        with col_cancel:
            cancel = st.form_submit_button("❌ Annuler")

    # --- Gestion Annulation ---
    if cancel:
        st.session_state.selected_idx = None
        st.session_state.selected_path = None
        st.session_state.form_version += 1
        st.rerun()

    # --- Validation + Enregistrement ---
    if submitted:

        # Vérification des champs obligatoires
        errors = []
        if not id_input.strip():
            errors.append("XML:ID de l'oeuvre")
        if not titre_input.strip():
            errors.append("Titre")
        if not artiste_input.strip():
            errors.append("Artiste")

        if errors:
            st.error("❌ Champs obligatoires manquants : " + ", ".join(errors))
            return

        # Création de la nouvelle entrée
        new_entry = {
            "id": id_input.strip(),
            "type_oeuvre": type_input,
            "artiste": artiste_input,
            "titre": titre_input.strip(),
            "date": date_input,
            "technique": technique_input,
            "ville": ville_input,
            "institution": institution_input,
            "inventaire": inventaire_input
        }

        # Sauvegarde dans le fichier JSON correspondant
        save_oeuvre(new_entry, path)

        st.success("✅ Notice mise à jour !")
        st.session_state.selected_idx = None
        st.session_state.selected_path = None
        st.session_state.form_version += 1
        st.rerun()
