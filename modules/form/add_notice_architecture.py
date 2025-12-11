# modules/add_notice_ui.py
import streamlit as st
from datetime import datetime
import time
import uuid

from modules.data_loader import load_all_notices, save_notice, exist_notice, save_image, load_list_form, index_username
from modules.git_tools import git_commit_and_push

def add_notice_architecture():
    # initialisation de la clé
    if 'form_key_architecture' not in st.session_state:
        st.session_state.form_key_architecture = 0

    # Le formulaire
    with st.form(key=f"form_new_notice_architecture_{st.session_state.form_key_architecture}", enter_to_submit=False, border=False):
        st.subheader("Informations générales")
        entry_creator = st.selectbox("Créateur de la notice :*",
                                     load_list_form("usernames"),
                                     index=index_username()
                                     )
        id_input = st.text_input("XML:ID de l'œuvre *", help="Champ obligatoire, vérifier dans l'onglet Recherche que l'œuvre n'existe pas")
        QID_wikidata = st.text_input("Lien de la notice Wikidata")
        title = st.text_input("Titre de l'œuvre *")

        # =============== Artistes ===================

        st.subheader("Artistes")
        
        # Initialiser le nombre d'artistes dans session_state
        if 'nb_architects' not in st.session_state:
            st.session_state.nb_architects = 1
        
        # Boutons + et -
        col_creator_btn1, col_creator_btn2, col_creator_btn3 = st.columns([1, 1, 8])
        with col_creator_btn1:
            if st.form_submit_button("➕", key="add_architect"):
                if st.session_state.nb_architects < 10:
                    st.session_state.nb_architects += 1
        with col_creator_btn2:
            if st.form_submit_button("➖", key="remove_architect"):
                if st.session_state.nb_architects > 1:
                    st.session_state.nb_architects -= 1
        
        # Champs artistes dynamiques
        creators_list = []
        
        for i in range(st.session_state.nb_architects):
            col1, col2 = st.columns(2)
            with col1:
                artiste_id = st.selectbox(
                    f"XML:ID Artiste {i+1}",
                    load_list_form("artists_names"),
                    index=None,
                    placeholder="XML:ID de l'artiste, selectionner ou entrer un nouveau",
                    accept_new_options=True,
                    key=f"architect_id_{i}"
                    )
            with col2:
                artiste_role = st.selectbox(
                    f"Rôle",
                    load_list_form("architects_roles"),
                    key=f"architect_role_{i}", 
                    placeholder="ex: architecte"
                    )
            if artiste_id:
                creators_list.append({
                    "xml:id": artiste_id,
                    "role": artiste_role if artiste_role else ""
                })

        # =============== Caractéristiques (techniques / datation) ===================

        st.subheader("Détails de l'œuvre")

        typology = st.selectbox(
            "Typologie de monument",
            load_list_form("typologies"),
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
        
        st.subheader("Localisation")
        city = st.text_input("Ville")
        country = st.text_input("Pays")
        colLat, colLon = st.columns(2)
        with colLat:
            latitude = st.text_input("Latitude")
        with colLon:
            longitude = st.text_input("Longitude")


        # =============== Oeuvres liées ===================

        st.subheader("Oeuvres liées")

        # Initialiser le nombre d'oeuvres liées dans session_state
        if 'nb_related_architectures' not in st.session_state:
            st.session_state.nb_related_architectures = 1
        
        # Boutons + et -
        col_related_btn1, col_related_btn2, col_related_btn3 = st.columns([1, 1, 8])
        with col_related_btn1:
            if st.form_submit_button("➕", key="add_work_architecture"):
                if st.session_state.nb_related_architectures < 10:
                    st.session_state.nb_related_architectures += 1
        with col_related_btn2:
            if st.form_submit_button("➖", key="remove_work_architecture"):
                if st.session_state.nb_related_architectures > 1:
                    st.session_state.nb_related_architectures -= 1
        
        # Champs artistes dynamiques
        related_works_list = []
        list_link_type = []
        list_work_xml_id = []
        
        for i in range(st.session_state.nb_related_architectures):
            col1, col2 = st.columns(2)
            with col1:
                related_work_type = st.selectbox(
                    f"Type de lien",
                    list_link_type,
                    key=f"related_work_type_architecture_{i}", 
                    placeholder="ex: copie de, gravé d'après"
                    )
                
            with col2:
                related_work_id = st.selectbox(
                    f"Oeuvres liées {i+1}",
                    list_work_xml_id,
                    index=None,
                    placeholder="XML:ID de l'oeuvre liée ou entrer un nouveau",
                    accept_new_options=True,
                    key=f"related_work_id_architecture_{i}"
                    )

            if related_work_id:
                creators_list.append({
                    "link_type": related_work_type if related_work_type else "",
                    "xml_id_work": related_work_id
                })



        # =============== Bibliographie ===================

        st.subheader("Bibliographie")

        # Initialiser le nombre d'oeuvres liées dans session_state
        if 'nb_bibliography_architecture' not in st.session_state:
            st.session_state.nb_bibliography_architecture = 1
        
        # Boutons + et -
        col_bibliography_btn1, col_bibliography_btn2, col_bibliography_btn3 = st.columns([1, 1, 8])
        with col_bibliography_btn1:
            if st.form_submit_button("➕", key="add_bibliography_architecture"):
                if st.session_state.nb_bibliography_architecture < 10:
                    st.session_state.nb_bibliography_architecture += 1
        with col_bibliography_btn2:
            if st.form_submit_button("➖", key="remove_bibliography_architecture"):
                if st.session_state.nb_bibliography_architecture > 1:
                    st.session_state.nb_bibliography_architecture -= 1

        # Champs artistes dynamiques
        bibliography_list = []
        
        for i in range(st.session_state.nb_bibliography_architecture):
            col1, col2 = st.columns(2)
            with col1:
                bibliography_key = st.selectbox(
                    f"Bibliographie {i+1}",
                    load_list_form("zotero_keys"),
                    index=None,
                    placeholder="Clé Zotero de l'ouvrage bibliographique",
                    accept_new_options=True,
                    key=f"bibliography_id_architecture_{i}"
                    )
            with col2:
                bibliography_info = st.text_input(
                    f"Page, numéro dans la référence",
                    key=f"bibliography_type_architecture_{i}", 
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
        if "nb_illustration_architecture" not in st.session_state:
            st.session_state.nb_illustration_architecture = 0

        # stockage du type pour chaque illustration
        if "type_illustration_architecture" not in st.session_state:
            st.session_state.type_illustration_architecture = {}

        if "show_image_architecture" not in st.session_state:
            st.session_state.show_image_architecture = {}

        for i in range(st.session_state.nb_illustration_architecture):
            st.session_state.show_image_architecture.setdefault(i, False)
            st.session_state.type_illustration_architecture.setdefault(i, None)

        # --- BOUTONS + / - --- #
        col1, col2, col3 = st.columns([1, 1, 8])

        with col1:
            if st.form_submit_button("➕ ajouter"):
                if st.session_state.nb_illustration_architecture < 10:
                    st.session_state.nb_illustration_architecture += 1

        with col2:
            if st.form_submit_button("➖ enlever"):
                if st.session_state.nb_illustration_architecture > 0:
                    idx = st.session_state.nb_illustration_architecture - 1
                    st.session_state.nb_illustration_architecture -= 1

                    # ✅ nettoyage des états liés
                    st.session_state.type_illustration_architecture.pop(idx, None)
                    st.session_state.show_image_architecture.pop(idx, None)

        # --- LISTE DYNAMIQUE --- #
        illustrations_list = []

        for i in range(st.session_state.nb_illustration_architecture):

            st.markdown(f"**Illustration {i+1} :**")
            
            # Initialiser les valeurs si elles n'existent pas
            if i not in st.session_state.type_illustration_architecture:
                st.session_state.type_illustration_architecture[i] = None
            if i not in st.session_state.show_image_architecture:
                st.session_state.show_image_architecture[i] = False
            

            colA, colB, colC = st.columns([1, 6, 4])

            # Choix du mode via bouton (dans le form)
            with colA:
                if st.form_submit_button(f"➕ URL {i+1}", key=f"url_architecture_btn_{i}"):
                    st.session_state.type_illustration_architecture[i] = "URL"
                    st.session_state.show_image_architecture[i] = False

                if st.form_submit_button(f"📁 Local {i+1}", key=f"local_architecture_btn_{i}"):
                    st.session_state.type_illustration_architecture[i] = "local"
                    st.session_state.show_image_architecture[i] = False

            # Affichage du bon champ selon le choix
            with colB:
                if st.session_state.type_illustration_architecture[i] == "URL":
                    colB1, colB2 = st.columns([5, 1])
                    with colB1:
                        url = st.text_input(f"URL illustration {i+1}", key=f"url_architecture_{i}")
                    with colB2:
                        if st.form_submit_button(f"Voir l'image", key=f"show_image_url_architecture_{i}"):
                            st.session_state.show_image_architecture[i] = True
                    copyright_text = st.text_input(
                        "Droits",
                        key=f"copyright_architecture_{i}",
                        placeholder="© Auteur / Source"
                    )
                    caption = st.text_input(
                        "Description (caption)",
                        key=f"caption_architecture_{i}",
                        placeholder="image avec cadre, image sans cadre"
                    )
                    
                    with colC:
                        if st.session_state.show_image_architecture[i] == True:
                            st.image(url, caption="Prévisualisation")

                    illustrations_list.append({"id": i,
                                               "storage": "online",
                                               "url": url,
                                               "copyright": copyright_text,
                                               "caption": caption})
                
                # si stockage en local
                elif st.session_state.type_illustration_architecture[i] == "local":
                    colB1, colB2 = st.columns([5, 1])
                    with colB1:
                        uploaded_file = st.file_uploader(
                            f"Fichier illustration {i+1}",
                            type=["jpg", "jpeg", "png"],
                            key=f"upload_file_architecture_{i}"
                        )
                    with colB2:
                        if st.form_submit_button(f"Voir et sauvegarder l'image", key=f"show_image_url_architecture_{i}"):
                            st.session_state.show_image_architecture[i] = True
                    copyright_text = st.text_input(
                        "Droits",
                        key=f"copyright_architecture_{i}",
                        placeholder="© Auteur / Source"
                    )
                    caption = st.text_input(
                        "Description (caption)",
                        key=f"caption_architecture_{i}",
                        placeholder="image avec cadre, image sans cadre"
                    )

                    local_path = None

                    with colC:
                        if st.session_state.show_image_architecture[i] and uploaded_file is not None:
                            # sauvegarder correctement
                            local_path = save_image(uploaded_file)  # ← on passe l’objet fichier !
                            st.success(f"Image sauvegardée : {local_path}")
                            st.image(local_path, caption="Prévisualisation")
                            
                        elif st.session_state.show_image_architecture[i] and uploaded_file is None:
                            st.warning("Veuillez d'abord sélectionner un fichier.")
                    
                    illustrations_list.append({"id": i,
                                               "storage": "local",
                                               "url": local_path,
                                               "copyright": copyright_text,
                                               "caption": caption})

                else:
                    st.info("Choisissez un type : URL ou Local")


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
                    "entry_type": "architecture",
                    "typology": typology,
                    "dateCreated":{
                        "startYear": date_start,
                        "endYear": date_end,
                        "text": date_text
                    },
                    "location": {
                        "city": city,
                        "country": country,
                        "coordinates":{
                            "latitude":latitude,
                            "longitude":longitude
                            }
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
                # ajout sur github
                with st.spinner("Enregistement de la notice et ajout sur github"):
                    path = save_notice(new_oeuvre)
                    message = f"ajout notice {id_input} par {entry_creator} {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"
                    git_commit_and_push(message)
                    st.success(f"✅ Notice ajoutée avec succès sur github !\n\n📁 Fichier créé : `{path}`")
                    st.balloons()
                time.sleep(3)

                # réinitialisation
                for i in range(st.session_state.nb_illustration_architecture):
                    st.session_state.show_image_architecture[i] = False
                st.session_state.nb_illustration_architecture = 0
                st.session_state.type_illustration_architecture = {}
                st.session_state.show_image_architecture = {}
                st.session_state.form_key_architecture += 1

                st.rerun()