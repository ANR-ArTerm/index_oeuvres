import streamlit as st
import json

from modules.data_loader import load_all_notices, delete_notice


def render_search_notices():
    st.header("🔍 Recherche dans les notices")

    # Charger toutes les œuvres
    oeuvres, filenames = load_all_notices()

    search_query = st.text_input("Rechercher dans toutes les œuvres")

    st.subheader("Résultats")
    filtered = []

    # Préparer les résultats filtrés
    for idx, o in enumerate(oeuvres):
        if search_query.lower() in json.dumps(o, ensure_ascii=False).lower():
            filtered.append((idx, o, filenames[idx]))

    # Affichage des cartes
    cols = st.columns(3)

    for i, (idx, o, path) in enumerate(filtered):

        with cols[i % 3]:

            st.markdown(
                f"""
                <div style='border:1px solid #ddd; border-radius:10px; padding:10px;
                    margin-bottom:10px; background:#fafafa; min-height:220px'>
                    <strong>{o.get('type_oeuvre', '—')}</strong><br>
                    <strong>{o.get('titre', 'Sans titre')}</strong><br>
                    <em>{o.get('artiste', 'Artiste inconnu')}</em><br>
                    <small>{o.get('date', '')}, {o.get('technique', '')}</small><br>
                    <small>{o.get('ville', '')} – {o.get('institution', '')}</small><br>
                    <small>Inventaire : {o.get('inventaire', '')}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Modifier / Supprimer
            col_mod, col_del = st.columns([1, 1])

            with col_mod:
                if st.button("✏️ Modifier", key=f"mod_{idx}"):
                    st.session_state.selected_idx = idx
                    st.session_state.selected_path = path
                    st.session_state.form_version += 1
                    st.rerun()

            with col_del:
                if st.button("Supprimer 🗑️", key=f"del_{idx}"):
                    delete_notice(path)
                    st.success(f"Notice supprimée : {path}")
                    st.rerun()
