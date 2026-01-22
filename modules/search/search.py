import os
from pathlib import Path
import time
import streamlit as st
from modules.search.search_painting import normalize_notice_painting
from modules.search.search_architecture import normalize_notice_architecture
from modules.data_loader import load_all_entries, delete_notice
import json
from modules.search.functions import truncate

def reset_all_page():
    st.session_state.all_page = 0


def normalize_notice(o, entry_type):
    if entry_type == "architecture":
        d = normalize_notice_architecture(o)
        d["location_display"] = f"{d.get('city')} – {d.get('country')}"
        d["secondary"] = d.get("typology")
    elif entry_type == "peinture":
        d = normalize_notice_painting(o)
        d["location_display"] = f"{d.get('city')} – {d.get('name')}"
        d["secondary"] = d.get("materialsAndTechniques")
    else:
        return None

    # clés communes obligatoires
    d.setdefault("illustrations_display", [])
    d.setdefault("creators_display", [])
    d.setdefault("biblio_display", [])

    return d


@st.cache_data(show_spinner="Chargement des notices…")
def load_all_entries_index():
    index = []

    for entry_type in ["architecture", "peinture", "ensemble"]:
        oeuvres = load_all_entries(entry_type)

        for idx, (o, json_path) in enumerate(oeuvres):
            o_display = normalize_notice(o, entry_type)
            search_blob = json.dumps(o_display, ensure_ascii=False).lower()

            index.append({
                "entry_type": entry_type,
                "o": o,
                "o_display": o_display,
                "json_path": json_path,
                "search_blob": search_blob
            })

    return index

def render_search_entries_all():

    st.header("🔍 Recherche dans toutes les notices")

    entry_type_filter = st.radio(
        "Type de notice",
        ["🌎 Tout", "🖼️ Œuvre", "🏛️ Bâtiment", "🌿 Ensemble"],
        index=0,
        on_change=reset_all_page,
        horizontal=True
    )

    ENTRY_TYPE_MAP = {
        "🖼️ Œuvre": "peinture",
        "🏛️ Bâtiment": "architecture",
        "🌿 Ensemble": "ensemble"
    }

    ITEMS_PER_PAGE = 12

    if "all_page" not in st.session_state:
        reset_all_page()

    index = load_all_entries_index()

    search_query = st.text_input(
        "Rechercher dans toutes les œuvres",
        key="search_all",
        on_change=reset_all_page
    ).lower()

    filtered = index

    # filtre par type
    if entry_type_filter != "🌎 Tout":
        filtered = [
            i for i in filtered
            if i["entry_type"] == ENTRY_TYPE_MAP[entry_type_filter]
        ]

    # filtre par recherche texte
    if search_query:
        filtered = [
            i for i in filtered
            if search_query in i["search_blob"]
        ]

    if not filtered:
        st.info("Aucun résultat trouvé.")
        return

    total_items = len(filtered)
    total_pages = (total_items - 1) // ITEMS_PER_PAGE + 1

    st.session_state.all_page = min(st.session_state.all_page, total_pages - 1)

    start = st.session_state.all_page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    paged = filtered[start:end]

    # Pagination UI
    col_prev, col_info, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("⬅️ Précédent", disabled=st.session_state.all_page == 0, key="prev"):
            st.session_state.all_page -= 1
            st.rerun()
    with col_info:
        st.markdown(
            f"<div style='text-align:center'>Page {st.session_state.all_page + 1} / {total_pages}</div>",
            unsafe_allow_html=True
        )
    with col_next:
        if st.button("Suivant ➡️", disabled=st.session_state.all_page >= total_pages - 1, key="next"):
            st.session_state.all_page += 1
            st.rerun()

    cols = st.columns(3)

    for i, item in enumerate(paged):
        o = item["o"]
        d = item["o_display"]
        json_path = item["json_path"]
        entry_type = item["entry_type"]

        with cols[i % 3]:
            with st.container(border=True):

                illus = d["illustrations_display"]
                if illus and illus[0] != "AUCUNE ILLUSTRATION":
                    try:
                        st.image(illus[0], width="stretch")
                    except:
                        st.warning("⚠️ Image non disponible")

                st.caption(entry_type)
                st.markdown(f"xml:id : **{d['id']}**")

                col_mod, col_del = st.columns(2)

                with col_mod:
                    if st.button("Modifier ✏️", key=f"mod_{entry_type}_{d['id']}"):
                        st.session_state.editing_notice = str(Path(json_path).resolve())
                        st.session_state.original_id = o.get("id")
                        st.session_state.active_menu = "edit"
                        st.rerun()

                with col_del:
                    if st.button("Supprimer 🗑️", key=f"del_{entry_type}_{d['id']}"):
                        delete_notice(json_path)
                        time.sleep(1)
                        st.rerun()

                st.text(d["title"])
                st.markdown(f"*{' ; '.join(d['creators_display'])}*")
                st.text(f"{d['date_text']}, {d['secondary']}")
                st.text(d["location_display"])
                st.caption(f"📚 {truncate(' ; '.join(d['biblio_display']))}")
                st.caption(f"📄 {os.path.basename(json_path)}")

