from modules.git_tools import git_pull, git_commit_and_push
from modules.data_loader import load_all_notices, load_notice, save_notice, delete_notice, exist_notice
import streamlit as st
from modules.add_notice_ui import render_add_notice
from modules.search_ui import render_search_notices
from modules.add_notice_architecture import render_add_notice_architecture

st.set_page_config(layout="wide")

st.title("🖼️ Editeur de notices d'oeuvres")

st.header("☁️ Télécharger et sauvegarder les données en ligne")

colPULL, colPUSH = st.columns([1, 3])

# --- Bouton Git Pull ---
with colPULL:
    if st.button("⤵️ Télécharger les données (Git Pull)"):
        ok, out = git_pull()
        if ok:
            st.success("✅ Git pull effectué avec succès !")
            st.text(out)
        else:
            st.error(f"⚠️ Erreur lors du git pull : {out}")


# --- Commit & Push ---
with colPUSH:
    if st.button("⤴️ Ajouter les données sur GitHub (Git Commit & Push)"):
        st.session_state.show_commit_box = True

    if st.session_state.get("show_commit_box", False):
        message = st.text_input("Entrer le message de commit")
        if st.button("Valider (Commit et Push)"):
            ok, out = git_commit_and_push(message)
            if ok:
                st.success("✅ Push effectué !")
                st.text(out)
                st.session_state.show_commit_box = False
            else:
                st.error(f"⚠️ Erreur : {out}")

st.divider()

st.header("☁️ Edition et ajout de données")

colMenuLateral, colMenuPrincipal = st.columns([1, 6])

# Initialisation des états
if "active_menu" not in st.session_state:
    st.session_state.active_menu = None   # "add" / "search" / None

with colMenuLateral:

    # Bouton : Ajouter une notice
    if st.button("➕ Ajouter une notice"):
        st.session_state.active_menu = "add" if st.session_state.active_menu != "add" else None

    # Bouton : Rechercher une notice
    if st.button("🔍 Rechercher dans les notices"):
        st.session_state.active_menu = "search" if st.session_state.active_menu != "search" else None

with colMenuPrincipal:

    if st.session_state.active_menu == "add":
        tab1, tab2, tab3, tab4 = st.tabs(["🖼️ Peinture", "🏛️ Architecture", "🗿 Sculpture", "Gravure"])
        
        with tab1:
            st.session_state.type_notice = "peinture"
            # Formulaire pour peinture
            render_add_notice()
        
        with tab2:
            st.session_state.type_notice = "architecture"
            # Formulaire pour architecture
            render_add_notice_architecture()
        
        with tab3:
            st.session_state.type_notice = "sculpture"
            # Formulaire pour sculpture
        
        with tab4:
            st.session_state.type_notice = "gravure"


    elif st.session_state.active_menu == "search":
        st.divider()
        render_search_notices()

