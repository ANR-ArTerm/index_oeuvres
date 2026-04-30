from modules.data.load import load_all_entries, save_list_to_list_form, _load_json, _save_json
import os
import streamlit as st
import math
import time

from modules.git_tools import git_commit_and_push

def update_list_institutions():
    ENTRIES = load_all_entries("artwork")
    institutions = set()

    for data, _ in ENTRIES:
        name = (
            data.get("location", {})
                .get("institution", {})
                .get("name")
        )

        if name:
            institutions.add(name.strip())

    save_list_to_list_form("institutions", list(institutions))

DATA_DIR = "data"
LIST_FORM_DIR = os.path.join(DATA_DIR, "list_form")

LISTS_EDITABLE = {
    "Villes et pays":"places.json",
    "Artistes":"persons.json",
    "Rôles des artistes (artwork)": "artists_roles.json",
    "Rôles des architectes (building))":"architects_roles.json",
    "Typologies d'architecture": "typologies_architecture.json",
    "Institutions de conservation": "institutions.json",
    "Techniques et matériaux": "techniques.json",
    "Clés zotero": "zotero_keys.json",
    "Type de liens entre les œuvres":"link_types.json",
    "Typologies d'ensemble":"typologies_ensemble.json",
    "Lien contenu":"link_types_contained.json",
    "Lien contenant":"link_types_contains.json",
    "Textes XML":"text_xml.json"
}

def edit_list_form():
    st.title("Éditeur de listes JSON")

    # Sélection de la liste
    liste_choisie = st.selectbox(
        "Choisir une liste à éditer",
        list(LISTS_EDITABLE.keys())
    )
    file_path = os.path.join(LIST_FORM_DIR, LISTS_EDITABLE[liste_choisie])

    # Chargement des données
    data = _load_json(file_path)

    if not isinstance(data, list):
        st.error("Le fichier JSON doit contenir une liste.")
        return

    # Init session state
    state_key = f"to_delete_{liste_choisie}"
    confirm_key = f"confirm_delete_{liste_choisie}"
    if state_key not in st.session_state:
        st.session_state[state_key] = set()
    if confirm_key not in st.session_state:
        st.session_state[confirm_key] = False

    st.subheader(f"Éléments actuels ({len(data):,} entrées)")

    # ── Barre de recherche ──────────────────────────────────────────────
    search_query = st.text_input("🔍 Rechercher", placeholder="Filtrer les éléments...")

    filtered_data = [
        (i, item) for i, item in enumerate(data)
        if not search_query or search_query.lower() in str(item).lower()
    ][::-1]  # ← ordre décroissant (dernier ajout en premier)
    st.caption(f"{len(filtered_data):,} résultat(s) trouvé(s)")

    # ── Pagination ──────────────────────────────────────────────────────
    PAGE_SIZE = 20
    total_pages = max(1, math.ceil(len(filtered_data) / PAGE_SIZE))

    col_info, col_nav = st.columns([3, 2])
    with col_nav:
        page = st.number_input(
            "Page", min_value=1, max_value=total_pages,
            value=1, step=1, label_visibility="collapsed"
        )
    with col_info:
        st.caption(f"Page {page}/{total_pages} · {PAGE_SIZE} éléments/page")

    start = (page - 1) * PAGE_SIZE
    page_items = filtered_data[start: start + PAGE_SIZE]

    # ── Affichage des éléments ──────────────────────────────────────────
    to_delete = st.session_state[state_key]

    for orig_idx, item in page_items:
        col1, col2 = st.columns([6, 1])
        with col1:
            st.write(item)
        with col2:
            checked = st.checkbox(
                "🗑️", key=f"del_{liste_choisie}_{orig_idx}",
                value=(orig_idx in to_delete)
            )
            if checked:
                to_delete.add(orig_idx)
            else:
                to_delete.discard(orig_idx)

    # ── Actions ─────────────────────────────────────────────────────────
    st.divider()
    nb_selected = len(to_delete)
    st.caption(f"🗑️ {nb_selected} élément(s) marqué(s) pour suppression")

    col_del, col_save = st.columns(2)

    with col_del:
        if st.button(f"🗑️ Supprimer ({nb_selected})", disabled=(nb_selected == 0)):
            st.session_state[confirm_key] = True

        if st.session_state[confirm_key]:
            st.warning(f"Confirmer la suppression de **{nb_selected}** élément(s) ?")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("✅ Confirmer", type="primary"):
                    data = [item for i, item in enumerate(data) if i not in to_delete]
                    st.session_state[state_key] = set()
                    st.session_state[confirm_key] = False
                    _save_json(file_path, data)
                    success, output = git_commit_and_push(
                        f"[liste] Suppression de {nb_selected} élément(s) dans {liste_choisie}"
                    )
                    if success:
                        st.success(f"{nb_selected} élément(s) supprimé(s) et synchronisé.")
                    else:
                        st.error(f"Sauvegardé localement, mais erreur Git :\n{output}")
                    st.rerun()
            with col_no:
                if st.button("❌ Annuler"):
                    st.session_state[confirm_key] = False
                    st.rerun()

    with col_save:
        if st.button("💾 Sauvegarder"):
            with st.spinner("Mise à jour de la liste"):
                _save_json(file_path, data)
                success, output = git_commit_and_push(
                    f"[liste] Mise à jour de {liste_choisie}"
                )
                if success:
                    st.success("Fichier sauvegardé et synchronisé.")
                    time.sleep(1)
                else:
                    st.error(f"Sauvegardé localement, mais erreur Git :\n{output}")