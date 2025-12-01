# modules/add_notice_ui.py
import streamlit as st
from streamlit_smart_text_input import st_smart_text_input
from datetime import datetime
import time
import uuid
from data.list_form.artists_name import list_artists_xml_id
from data.list_form.artists_role import list_role_artists
from data.list_form.techniques import list_techniques_peinture
from data.list_form.zotero_key import list_zotero_key

from modules.data_loader import load_all_notices, save_notice, exist_notice, save_image

def add_notice():
    # initialisation de la clé
    if 'form_key' not in st.session_state:
        st.session_state.form_key = 0

    # Le formulaire
    with st.form(key=f"form_new_notice_{st.session_state.form_key}", enter_to_submit=False, border=False):
        st.subheader("Informations générales")
        entry_creator = st.selectbox("Créateur de la notice :*",("Pierre", "Julia", "Anna", "Emma"))
        id_input = st.text_input("XML:ID de l'œuvre *", help="Champ obligatoire, vérifier dans l'onglet Recherche que l'œuvre n'existe pas")
        QID_wikidata = st.text_input("Lien de la notice Wikidata")
        title = st.text_input("Titre de l'œuvre *")

        # =============== Artistes ===================

        st.subheader("Artistes")
        
        # Initialiser le nombre d'artistes dans session_state
        if 'nb_artistes' not in st.session_state:
            st.session_state.nb_artistes = 1
        
        # Boutons + et -
        col_creator_btn1, col_creator_btn2, col_creator_btn3 = st.columns([1, 1, 8])
        with col_creator_btn1:
            if st.form_submit_button("➕", key="add_artist"):
                if st.session_state.nb_artistes < 10:
                    st.session_state.nb_artistes += 1
        with col_creator_btn2:
            if st.form_submit_button("➖", key="remove_artist"):
                if st.session_state.nb_artistes > 1:
                    st.session_state.nb_artistes -= 1
        
        # Champs artistes dynamiques
        creators_list = []
        
        for i in range(st.session_state.nb_artistes):
            col1, col2 = st.columns(2)
            with col1:
                artiste_id = st.selectbox(
                    f"XML:ID Artiste {i+1}",
                    list_artists_xml_id,
                    index=None,
                    placeholder="XML:ID de l'artiste, selectionner ou entrer un nouveau",
                    accept_new_options=True,
                    key=f"peintre_id_{i}"
                    )
            with col2:
                artiste_role = st.selectbox(
                    f"Rôle",
                    list_role_artists,
                    key=f"peintre_role_{i}", 
                    placeholder="ex: peintre"
                    )
            if artiste_id:
                creators_list.append({
                    "xml:id": artiste_id,
                    "role": artiste_role if artiste_role else ""
                })

        # =============== Caractéristiques (techniques / datation) ===================

        st.subheader("Détails de l'œuvre")

        technique = st.selectbox(
            "Technique et support",
            list_techniques_peinture,
            accept_new_options=True,
            index = None,
            placeholder = "Selectionner ou ajouter une option"
        )

        st.subheader("Datation de l'oeuvre")
        col_date_1, col_date_2, col_date_3 = st.columns([1, 1, 8])
        with col_date_1:
            date_start = st.text_input("Date début", max_chars=4)
        with col_date_2:
            date_end = st.text_input("Date fin" ,max_chars=4)
        with col_date_3:
            date_text = st.text_input("Texte à afficher")
        
        st.subheader("Lieu de conservation")
        holding_place = st.text_input("Ville de conservation")
        holding_institution = st.text_input("Institution de conservation / monument")
        holding_number = st.text_input("Numéro d'inventaire")
        holding_URL = st.text_input("Lien dans la base de données du musée")


        # =============== Oeuvres liées ===================

        st.subheader("Oeuvres liées")

        # Initialiser le nombre d'oeuvres liées dans session_state
        if 'nb_related_works' not in st.session_state:
            st.session_state.nb_related_works = 1
        
        # Boutons + et -
        col_related_btn1, col_related_btn2, col_related_btn3 = st.columns([1, 1, 8])
        with col_related_btn1:
            if st.form_submit_button("➕", key="add_work"):
                if st.session_state.nb_related_works < 10:
                    st.session_state.nb_related_works += 1
        with col_related_btn2:
            if st.form_submit_button("➖", key="remove_work"):
                if st.session_state.nb_related_works > 1:
                    st.session_state.nb_related_works -= 1
        
        # Champs artistes dynamiques
        related_works_list = []
        list_link_type = []
        list_work_xml_id = []
        
        for i in range(st.session_state.nb_related_works):
            col1, col2 = st.columns(2)
            with col1:
                related_work_type = st.selectbox(
                    f"Type de lien",
                    list_link_type,
                    key=f"related_work_type_{i}", 
                    placeholder="ex: copie de, gravé d'après"
                    )
                
            with col2:
                related_work_id = st.selectbox(
                    f"Oeuvres liées {i+1}",
                    list_work_xml_id,
                    index=None,
                    placeholder="XML:ID de l'oeuvre liée ou entrer un nouveau",
                    accept_new_options=True,
                    key=f"related_work_id_{i}"
                    )

            if related_work_id:
                creators_list.append({
                    "link_type": related_work_type if related_work_type else "",
                    "xml_id_work": related_work_id
                })



        # =============== Bibliographie ===================

        st.subheader("Bibliographie")

        # Initialiser le nombre d'oeuvres liées dans session_state
        if 'nb_bibliography' not in st.session_state:
            st.session_state.nb_bibliography = 1
        
        # Boutons + et -
        col_bibliography_btn1, col_bibliography_btn2, col_bibliography_btn3 = st.columns([1, 1, 8])
        with col_bibliography_btn1:
            if st.form_submit_button("➕", key="add_bibliography"):
                if st.session_state.nb_bibliography < 10:
                    st.session_state.nb_bibliography += 1
        with col_bibliography_btn2:
            if st.form_submit_button("➖", key="remove_bibliography"):
                if st.session_state.nb_bibliography > 1:
                    st.session_state.nb_bibliography -= 1

        # Champs artistes dynamiques
        bibliography_list = []
        
        for i in range(st.session_state.nb_bibliography):
            col1, col2 = st.columns(2)
            with col1:
                bibliography_key = st.selectbox(
                    f"Bibliographie {i+1}",
                    list_zotero_key,
                    index=None,
                    placeholder="Clé Zotero de l'ouvrage bibliographique",
                    accept_new_options=True,
                    key=f"bibliography_id_{i}"
                    )
            with col2:
                bibliography_info = st.text_input(
                    f"Page, numéro dans la référence",
                    key=f"bibliography_type_{i}", 
                    placeholder="ex: vol. 3, p. 100, n° 4"
                    )
            if bibliography_key:
                bibliography_list.append({
                    "zotero_key": bibliography_key,
                    "location": bibliography_info if bibliography_info else ""
                })

        # =============== Illustrations ===================

        st.subheader("Illustrations")

        # compteur
        if "nb_illustration" not in st.session_state:
            st.session_state.nb_illustration = 0

        # stockage du type pour chaque illustration
        if "type_illustration" not in st.session_state:
            st.session_state.type_illustration = {}

        # --- BOUTONS + / - --- #
        col1, col2, col3 = st.columns([1, 1, 8])

        with col1:
            if st.form_submit_button("➕ ajouter"):
                if st.session_state.nb_illustration < 10:
                    st.session_state.nb_illustration += 1

        with col2:
            if st.form_submit_button("➖ enlever"):
                if st.session_state.nb_illustration > 0:
                    st.session_state.nb_illustration -= 1


        # --- LISTE DYNAMIQUE --- #
        illustrations_list = []

        for i in range(st.session_state.nb_illustration):

            st.markdown(f"**Illustration {i+1} :**")

            # Initialiser valeur si elle n'existe pas
            if i not in st.session_state.type_illustration:
                st.session_state.type_illustration[i] = None

            colA, colB = st.columns([1, 10])

            # Choix du mode via bouton (dans le form)
            with colA:
                if st.form_submit_button(f"➕ URL {i+1}", key=f"url_btn_{i}"):
                    st.session_state.type_illustration[i] = "URL"
                if st.form_submit_button(f"📁 Local {i+1}", key=f"local_btn_{i}"):
                    st.session_state.type_illustration[i] = "local"

            # Affichage du bon champ selon le choix
            with colB:
                if st.session_state.type_illustration[i] == "URL":
                    url = st.text_input(f"URL illustration {i+1}", key=f"url_{i}")
                    copyright_text = st.text_input(
                        "Droits",
                        key=f"copyright_{i}",
                        placeholder="© Auteur / Source"
                    )
                    caption = st.text_input(
                        "Description (caption)",
                        key=f"caption_{i}",
                        placeholder="image avec cadre, image sans cadre"
                    )
                    illustrations_list.append({"id": i,
                                               "storage": "URL",
                                               "url": url,
                                               "copyright": copyright_text,
                                               "caption": caption})
                elif st.session_state.type_illustration[i] == "local":
                    file = st.file_uploader(f"Fichier illustration {i+1}", key=f"file_{i}")
                    copyright_text = st.text_input(
                        "Droits",
                        key=f"copyright_{i}",
                        placeholder="© Auteur / Source"
                    )
                    caption = st.text_input(
                        "Description (caption)",
                        key=f"caption_{i}",
                        placeholder="image avec cadre, image sans cadre"
                    )
                    illustrations_list.append({"id": i,
                                               "storage": "local",
                                               "url": file,
                                               "copyright": copyright_text,
                                               "caption": caption})

                else:
                    st.info("Choisissez un type : URL ou Local")

            """
            col1, col2 = st.columns(2)

            # Valeurs initiales
            url_value = ""
            storage_value = "local"
            local_path = None

            # === MODE URL ===
            if storage_mode == "URL":
                url_value = st.text_input(
                    "Entrer l’URL de l’image",
                    key=f"url_{i}",
                    placeholder="https://exemple.com/image.jpg"
                )
                storage_value = "online"

                # Prévisualisation
                if url_value:
                    st.image(url_value, caption="Prévisualisation")

            # === MODE LOCAL ===
            if storage_mode == "Local":
                uploaded_file = st.file_uploader(
                    "Uploader une image",
                    type=["jpg", "jpeg", "png"],
                    key=f"upload_{i}"
                )

                if uploaded_file:
                    local_path = save_image(uploaded_file)
                    st.success(f"Image sauvegardée : {local_path}")
                    st.image(uploaded_file, caption="Prévisualisation")
                    url_value = local_path  # le chemin local devient l’URL stockée

            with col2:
                caption = st.text_input(
                    "Légende",
                    key=f"caption_{i}",
                    placeholder="Description de l'image"
                )
                copyright_text = st.text_input(
                    "Droits",
                    key=f"copyright_{i}",
                    placeholder="© Auteur / Source"
                )
            
            illustrations_list.append({
                "id": i,
                "url": url_value,
                "copyright": copyright_text,
                "caption": caption,
                "storage": storage_value
            })
            """

        # =============== Commentaire ===================

        st.subheader("Commentaire")
        commentaire = st.text_area("Commentaire")

        # =============== Validation ===================
        
        st.subheader("Validation")
        submitted = st.form_submit_button("💾 Enregistrer la notice")
        
        # =============== Oeuvres liées ===================

        # Verification de la notice
        presence_notice = exist_notice(id_input)

        if submitted:
            if not title:
                st.error("Le titre de l'œuvre est obligatoire.")
            elif presence_notice == True:
                st.error("L'oeuvre existe déjà, veuillez la modifier")
            else:
                new_oeuvre = {
                    "id": id_input,
                    "QID_wikidata": QID_wikidata,
                    "title": title,
                    "creator": creators_list,
                    "entry_type": "Peinture et arts graphiques",
                    "materialsAndTechniques": technique,
                    "dateCreated":{
                        "startYear": date_start,
                        "endYear": date_end,
                        "text": date_text
                    },
                    "holding_institution": {
                        "place": holding_place,
                        "name": holding_institution,
                        "inventory_number": holding_number,
                        "URL": holding_URL
                        },
                    "related_works": related_works_list,
                    "bibliography": bibliography_list,
                    "illustrations": illustrations_list,
                    "commentary": commentaire,
                    "history": [
                        {
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "type": "created",
                        "author": entry_creator
                        }
                    ]
                    }
                # Sauvegarde
                path = save_notice(new_oeuvre)
                st.success(f"✅ Notice ajoutée avec succès !\n\n📁 Fichier créé : `{path}`")
                st.balloons()
                
                # réinitialisation
                st.session_state.form_key += 1
                time.sleep(3)
                st.rerun()