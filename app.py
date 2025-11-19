from modules.git_tools import git_pull, git_commit_and_push
import streamlit as st

st.set_page_config(layout="wide")

st.title("🖼️ Editeur de notices d'oeuvres")

st.subheader("☁️ Télécharger et sauvegarder les données en ligne")

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
