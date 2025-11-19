# modules/add_notice_ui.py
import streamlit as st
from streamlit_smart_text_input import st_smart_text_input
from datetime import datetime
import time
import uuid

from modules.data_loader import load_all_notices, save_notice, exist_notice

def render_add_notice_architecture():
    # Ajout d'une form_key qui est incrémentée à chaque ajout pour vider le formulaire
    if 'form_key_architecture' not in st.session_state:
        st.session_state.form_key_architecture = 0

    """
    Affiche le formulaire d'ajout de notice (réutilisable dans app.py ou pages/1_ajout_notice.py).
    """

    st.header("➕ Ajouter une nouvelle notice Architecture")

    # Le formulaire
    with st.form(key=f"form_new_notice_architecture_{st.session_state.form_key_architecture}"):
        st.subheader("Informations générales")
        id_input = st.text_input("XML:ID de l'œuvre *", help="Champ obligatoire")
        lien_wikidata = st.text_input("Lien de la notice Wikidata")
        titre = st.text_input("Titre de l'œuvre *")
        
        st.subheader("Artistes")
        
        # Initialiser le nombre d'artistes dans session_state
        if 'nb_artistes' not in st.session_state:
            st.session_state.nb_artistes = 1
        
        # Boutons + et -
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 8])
        with col_btn1:
            if st.form_submit_button("➕"):
                if st.session_state.nb_artistes < 10:
                    st.session_state.nb_artistes += 1
        with col_btn2:
            if st.form_submit_button("➖"):
                if st.session_state.nb_artistes > 1:
                    st.session_state.nb_artistes -= 1
        
        # Champs artistes dynamiques
        artistes_list = []
        
        for i in range(st.session_state.nb_artistes):
            col1, col2 = st.columns(2)
            with col1:
                artiste_id = st.text_input(f"XML:ID Artiste {i+1}", key=f"artiste_id_{i}")
            with col2:
                artiste_role = st.text_input(f"Rôle", key=f"artiste_role_{i}", placeholder="ex: peintre")
            
            if artiste_id:
                artistes_list.append({
                    "xml:id": artiste_id,
                    "role": artiste_role if artiste_role else ""
                })
        
        st.subheader("Détails de l'œuvre")
        type_oeuvre = st.selectbox(
            "Type d'œuvre",
            ["Peinture", "Sculpture", "Architecture", "Gravure"]
        )
        technique = st.text_input("Technique")
        technique = st.selectbox(
            "Technique",
            ["huile sur toile", "tempera sur toile", "fresque", "huile sur bois"]
        )
        date_realisation = st.text_input("Date / Période")
        ville = st.text_input("Ville")
        institution = st.text_input("Institution")
        inventaire = st.text_input("Numéro d'inventaire")
        
        st.subheader("Validation")
        submitted = st.form_submit_button("💾 Enregistrer la notice")
        
        # Verification de la notice
        presence_notice = exist_notice(id_input)

        if submitted:
            if not titre:
                st.error("Le titre de l'œuvre est obligatoire.")
            elif presence_notice == True:
                st.error("L'oeuvre existe déjà, veuillez la modifier")
            else:
                new_oeuvre = {
                    "id": id_input,
                    "lien_wikidata": lien_wikidata,
                    "titre": titre,
                    "artistes": artistes_list,
                    "type_oeuvre": type_oeuvre,
                    "technique": technique,
                    "date": date_realisation,
                    "ville": ville,
                    "institution": institution,
                    "inventaire": inventaire,
                    "date_creation_notice": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                # Sauvegarde
                path = save_notice(new_oeuvre)
                st.success(f"✅ Notice ajoutée avec succès !\n\n📁 Fichier créé : `{path}`")
                st.balloons()

                #Incrémenter la session key
                st.session_state.form_key_architecture += 1
                time.sleep(3)
                st.rerun()