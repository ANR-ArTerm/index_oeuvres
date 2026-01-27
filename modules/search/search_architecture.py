import streamlit as st
import json
import os
import time
from pathlib import Path

from modules.data.load import load_all_entries, delete_notice
from modules.search.functions import truncate

def normalize_notice_architecture(o):
    """
    Remplace les champs vides par des chaînes 'AUCUN ...' pour que la recherche fonctionne.
    """
    o_display = {}

    # Champs principaux
    o_display['id'] = o.get('id') or "AUCUN ID"
    o_display['title'] = o.get('title') or "AUCUN TITRE"
    o_display['entry_type'] = o.get('entry_type') or "AUCUN TYPE"
    o_display['typology'] = o.get('typology') or "AUCUNE TYPOLOGIE"
    o_display['commentary'] = o.get('commentary') or "AUCUN COMMENTAIRE"
    
    # Date
    date = o.get('dateCreated', {})
    o_display['date_text'] = date.get('text') or "AUCUNE DATE"
    
    # Lieu
    location = o.get('location', {})
    o_display['city'] = location.get('city') or "AUCUNE VILLE"
    o_display['country'] = location.get('country') or "AUCUN PAYS"
    
    # Créateurs
    creators = o.get('creator', [])
    if not creators:
        o_display['creators_display'] = ["AUCUN CRÉATEUR"]
    else:
        display_list = []
        for c in creators:
            nom = c.get('xml_id', 'Créateur inconnu')
            role = c.get('role')
            display_list.append(f"{nom} ({role})" if role else nom)
        o_display['creators_display'] = display_list

    # Bibliographie
    biblio = o.get('bibliography', [])
    if not biblio:
        o_display['biblio_display'] = ["AUCUNE BIBLIOGRAPHIE"]
    else:
        o_display['biblio_display'] = [f"{b.get('zotero_key', '')} ({b.get('location', '')})" for b in biblio]

    # Illustrations
    illus = o.get('illustrations', [])
    if not illus:
        o_display['illustrations_display'] = ["AUCUNE ILLUSTRATION"]
    else:
        o_display['illustrations_display'] = [i.get('url', 'AUCUNE URL') for i in illus]

    return o_display

@st.cache_data(show_spinner="Chargement des notices…")
def load_architecture_index():
    oeuvres = load_all_entries("architecture")
    index = []

    for idx, (o, json_path) in enumerate(oeuvres):
        o_display = normalize_notice_architecture(o)
        search_blob = json.dumps(o_display, ensure_ascii=False).lower()
        index.append((idx, o, o_display, json_path, search_blob))

    return index

def render_search_entries_architecture():
    st.header("🔍 Recherche dans les notices d'architecture")

    ITEMS_PER_PAGE = 12

    if "archi_page" not in st.session_state:
        st.session_state.archi_page = 0

    # Chargement CACHÉ
    index = load_architecture_index()

    def reset_archi_page():
        st.session_state.archi_page = 0

    search_query = st.text_input(
        "Rechercher dans toutes les œuvres",
        key="search_architecture",
        on_change=reset_archi_page
    ).lower()

    # Filtrage rapide
    if search_query:
        filtered = [item for item in index if search_query in item[4]]
    else:
        filtered = index

    if not filtered:
        st.info("Aucun résultat trouvé.")
        return

    total_items = len(filtered)
    total_pages = (total_items - 1) // ITEMS_PER_PAGE + 1

    # Sécurité : si page hors limites
    if st.session_state.archi_page >= total_pages:
        st.session_state.archi_page = 0

    start = st.session_state.archi_page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    paged_results = filtered[start:end]

    # Pagination UI
    col_prev, col_info, col_next = st.columns([1, 2, 1])

    with col_prev:
        if st.button("⬅️ Précédent", disabled=st.session_state.archi_page == 0):
            st.session_state.archi_page -= 1
            st.rerun()

    with col_info:
        st.markdown(
            f"<div style='text-align:center'>Page {st.session_state.archi_page + 1} / {total_pages}</div>",
            unsafe_allow_html=True
        )

    with col_next:
        if st.button("Suivant ➡️", disabled=st.session_state.archi_page >= total_pages - 1):
            st.session_state.archi_page += 1
            st.rerun()

    cols = st.columns(3)

    for i, (idx, o, o_display, json_path, _) in enumerate(paged_results):
        with cols[i % 3]:
            creators_str = " ; ".join(o_display.get('creators_display', []))
            biblio_str = " ; ".join(o_display.get('biblio_display', []))
            illustrations_list = o_display.get('illustrations_display', [])

            with st.container(border=True):
                # Image en haut si elle existe (première illustration)
                if illustrations_list and illustrations_list[0] != "AUCUNE ILLUSTRATION":
                    first_illustration = illustrations_list[0]
                    try:
                        st.image(first_illustration, width='stretch')
                    except Exception:
                        st.warning("⚠️ Image non disponible")
                
                # Type d'entrée
                st.caption(o_display['entry_type'])
                
                # ID
                st.markdown(f"xml:id : **{o_display['id']}**")

                col_mod, col_del = st.columns([1, 1])
                
                with col_mod:
                    if st.button("Modifier ✏️", key=f"mod_architecture_{idx}"):
                        st.session_state.editing_notice = str(Path(json_path).resolve())
                        st.session_state.original_id = o.get("id")
                        st.session_state.active_menu = "edit"
                        st.rerun()

                with col_del:
                    if st.button("Supprimer 🗑️", key=f"del_architecture_{idx}"):
                        delete_notice(json_path)
                        st.success(f"Notice déplacée dans la corbeille : {json_path}")
                        time.sleep(1)
                        st.rerun()

                # Titre principal
                st.text(o_display['title'])
                
                # Créateurs en italique
                st.markdown(f"*{creators_str}*")
                
                # Informations secondaires
                st.text(f"{o_display['date_text']}, {o_display['typology']}")
                st.text(f"{o_display['city']} – {o_display['country']}")
                
                # Informations bibliographiques
                st.caption(f"📚 {truncate(biblio_str)}")
                
                # Afficher toutes les illustrations
                if len(illustrations_list) > 1:
                    autres_illus = " ; ".join(illustrations_list[1:])
                    st.caption(f"🖼️ Autres illustrations : {autres_illus}")
                elif illustrations_list:
                    st.caption(f"🖼️ {illustrations_list[0]}")

                st.caption(f"📄 {os.path.basename(json_path)}")
