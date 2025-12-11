import streamlit as st

from modules.git_tools import git_pull, git_commit_and_push

from modules.data_loader import load_all_notices, load_notice, save_notice, delete_notice, exist_notice

from modules.form.home import render_home
from modules.form.search import render_search_notices
from modules.form.add_notice_architecture import add_notice_architecture
from modules.form.add_notice_peinture import add_notice_peinture

from modules.search.search_architecture import render_search_entries_architecture
from modules.search.search_painting import render_search_entries_painting
from modules.search.consult_architecture import edit_json_notice


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

# Zone principale
if st.session_state.active_menu is None:
    render_home()
elif st.session_state.active_menu == "add":
    st.header("Ajouter une notice")
    tab1, tab2 = st.tabs(["🖼️ Peinture", "🏛️ Architecture"])
    
    with tab1:
        st.session_state.type_notice = "peinture"
        add_notice_peinture()
    
    with tab2:
        st.session_state.type_notice = "architecture"
        add_notice_architecture()

elif st.session_state.active_menu == "search":
    st.header("Ajouter une notice")
    tab1, tab2 = st.tabs(["🖼️ Peinture", "🏛️ Architecture"])
    with tab1:
        st.session_state.type_notice = "peinture"
        render_search_entries_painting()

    with tab2:
        st.session_state.type_notice = "architecture"
        render_search_entries_architecture()

elif st.session_state.active_menu == "edit":
    if "editing_notice" in st.session_state and st.session_state.editing_notice:
        st.header("✏️ Édition de la notice")
        
        if st.button("← Retour à la liste"):
            del st.session_state.editing_notice
            st.session_state.active_menu = "search"
            st.rerun()
        
        edit_json_notice(json_path=st.session_state.editing_notice)

