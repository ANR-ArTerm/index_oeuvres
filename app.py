import streamlit as st
from pathlib import Path

from modules.git_tools import git_pull, git_commit_and_push

from modules.data_loader import load_all_entries, _load_json

from modules.form.home import render_home
from modules.form.search import render_search_notices
from modules.form.add_notice_architecture import add_notice_architecture
from modules.form.add_notice_peinture import add_notice_peinture

from modules.search.search_architecture import render_search_entries_architecture
from modules.search.search_painting import render_search_entries_painting
from modules.search.modify_entry import edit_json_notice

from modules.data.index_xml_personnes import sync_person_ids
from modules.data.index_xml_oeuvres import sync_oeuvres_from_json
from modules.data.verify_data import verify_json_entries


st.set_page_config(layout="wide")
st.title("🖼️ Editeur de notices d'oeuvres")

# Initialisation des états
if "active_menu" not in st.session_state:
    st.session_state.active_menu = None   # "add" / "search" / None
    st.rerun()

# Sidebar comme navigation principale
st.sidebar.header("Menu")

if st.sidebar.button("Accueil"):
    st.session_state.active_menu = None

st.sidebar.subheader("Edition des notices")
if st.sidebar.button("➕ Ajouter une notice"):
    st.session_state.active_menu = "add" if st.session_state.active_menu != "add" else None

if st.sidebar.button("🔍 Rechercher dans les notices"):
    st.session_state.active_menu = "search" if st.session_state.active_menu != "search" else None

st.sidebar.subheader("Stockage en ligne des données")
if st.sidebar.button("⤵️ Télécharger les données (Git Pull)"):
    ok, out = git_pull()
    if ok:
        st.success("✅ Git pull effectué avec succès !")
        st.text(out)
    else:
        st.error(f"⚠️ Erreur lors du git pull : {out}")

if st.sidebar.button("⤴️ Ajouter les données sur GitHub (Git Commit & Push)"):
    st.session_state.show_commit_box = True

if st.session_state.get("show_commit_box", False):
    message = st.sidebar.text_input("Entrer le message de commit")
    if st.sidebar.button("Valider (Commit et Push)"):
        with st.sidebar:
            with st.spinner("Enregistement de la notice et ajout sur github"):
                ok, out = git_commit_and_push(message)
            if ok:
                st.sidebar.success("✅ Push effectué !")
                st.sidebar.code(out, language="bash")
                st.sidebar.session_state.show_commit_box = False
            else:
                st.error(f"⚠️ Erreur : {out}")

st.sidebar.title("Mise à jour des index")

if st.sidebar.button("👥 Synchroniser l'index XML des personnes"):
    try:
        new_json_ids, json_only_ids = sync_person_ids()

        if new_json_ids:
            st.sidebar.subheader("🆕 Personnes ajoutées au JSON")
            st.sidebar.success(new_json_ids)
        else:
            st.sidebar.info("Aucune nouvelle personne ajoutée au JSON")

        if json_only_ids:
            st.sidebar.subheader("⚠️ Personnes à ajouter dans l’index XML")
            st.sidebar.warning(json_only_ids)
        else:
            st.sidebar.success("L’index XML est à jour")

    except FileNotFoundError as e:
        st.sidebar.error(str(e))

if st.sidebar.button("🎨 Synchroniser Index XML des œuvres"):
    try:
        ids = sync_oeuvres_from_json()

        st.sidebar.success(f"Index XML reconstruit avec succès : {len(ids)} notices indexées dans l'indexOeuvres.xml")
        total_notices = len(load_all_entries("peinture")) + len(load_all_entries("architecture"))
        if len(ids) != total_notices:
            st.sidebar.error(f"Attention, {total_notices - len(ids)} notices semblent corrompues, vérifier grâce à l'outil ci-dessous")

    except FileNotFoundError as e:
        st.sidebar.error(str(e))

st.sidebar.title("Vérification")

if st.sidebar.button("Vérifier les JSON"):
    report, corrupted_files = verify_json_entries()
    st.session_state.json_report = report
    st.session_state.corrupted_files = corrupted_files

if "json_report" in st.session_state:
    st.sidebar.code(st.session_state.json_report)

if "corrupted_files" in st.session_state and st.session_state.corrupted_files:
    st.sidebar.markdown("### ✏️ Notices à corriger")

    for idx, json_path in enumerate(st.session_state.corrupted_files):

        # sécurité : json_path peut être str ou Path
        json_path = Path(json_path)

        st.sidebar.markdown(f"**{json_path.name}**")

        if st.sidebar.button(
            "Modifier ✏️",
            key=f"edit_corrupted_{json_path.stem}_{idx}"
        ):
            try:
                data = _load_json(json_path)
                original_id = data.get("id")
            except Exception:
                pass  # JSON très corrompu, on continue sans id
            st.session_state.editing_notice = str(json_path.resolve())
            st.session_state.original_id = original_id
            st.session_state.active_menu = "edit"
            st.rerun()

# Zone principale
if st.session_state.active_menu is None:
    render_home()
elif st.session_state.active_menu == "add":
    st.header("Ajouter une notice")
    tab1, tab2 = st.tabs(["🖼️ Œuvre", "🏛️ Bâtiment"])
    
    with tab1:
        st.session_state.type_notice = "peinture"
        add_notice_peinture()
    
    with tab2:
        st.session_state.type_notice = "architecture"
        add_notice_architecture()

elif st.session_state.active_menu == "search":
    st.header("Ajouter une notice")
    tab1, tab2, tab3 = st.tabs(["🖼️ Œuvre", "🏛️ Bâtiments", "Corbeille"])
    with tab1:
        st.session_state.type_notice = "peinture"
        render_search_entries_painting()

    with tab2:
        st.session_state.type_notice = "architecture"
        render_search_entries_architecture()


elif st.session_state.active_menu == "edit":
    if "editing_notice" in st.session_state and st.session_state.editing_notice:

        json_path = Path(st.session_state.editing_notice)

        st.header("✏️ Édition de la notice")
        
        if st.button("← Retour à la liste"):
            del st.session_state.editing_notice
            st.session_state.active_menu = "search"
            st.rerun()
        
        edit_json_notice(json_path=json_path)

