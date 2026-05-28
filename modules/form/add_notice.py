import streamlit as st
from datetime import datetime
import time
import uuid
import re

from modules.data.load import save_notice, exist_notice, save_image, load_list_form, index_username, save_to_list_form_git, get_all_objects_ids_flat_sorted
from modules.git_tools import git_commit_and_push
from modules.wikidata.queries import get_monument_data

from modules.form.components import exemple_desc_image

from modules.status_entry import STATUS_ENTRY_OPTIONS

def init_empty_notice(xml_id, entry_type):
    return {
        "id": xml_id,
        "QID_wikidata": "",
        "entry_type": entry_type,
        "title": "",
        "creator": [],
        "dateCreated": {
            "startYear": None,
            "endYear": None,
            "text": ""
        },
        "location": "",
        "related_works": [],
        "bibliography": [],
        "illustrations": [],
        "description": "",
        "commentary": "",
        "history": [],
        "status_entry":0
    }

def add_creator(xml_id, creator, idx, type_entry):
    """Édite un artiste"""
    st.subheader(f"Artiste {idx + 1}")
    col1, col2 = st.columns(2)
    with col1:
        creator["xml_id"] = st.selectbox("Artiste :*",
                                     load_list_form("persons"),
                                     accept_new_options=True,
                                     index=None,
                                     key=f"{xml_id}_creator_xmlid_{idx}"
                                     )
        if creator["xml_id"] is not None and creator["xml_id"] not in load_list_form("persons"):
            with st.spinner("Sauvegarde du nouvel identifiant"):
                success, message = save_to_list_form_git("persons", creator["xml_id"])
                if success:
                    st.success(message)
                else:
                    st.error(message)

    with col2:
        if type_entry == "artwork":
            creator["role"] = st.selectbox("Rôle :",
                                            load_list_form("artists_roles"),
                                            index=None,
                                            key=f"{xml_id}_creator_artwork_xmlid_{idx}",
                                            accept_new_options=True
                                            )
            if creator["role"] is not None and creator["role"] not in load_list_form("artists_roles"):
                st.write("Sauvegarde du nouveau rôle")
                success, message = save_to_list_form_git("artists_roles", creator["role"])
                if success:
                    st.success(message)
                else:
                    st.error(message)

        if type_entry == "building":
            creator["role"] = st.selectbox("Rôle :",
                                            load_list_form("architects_roles"),
                                            index=None,
                                            key=f"{xml_id}_creator_architect_xmlid_{idx}",
                                            accept_new_options=True
                                            )
            if creator["role"] is not None and creator["role"] not in load_list_form("architects_roles"):
                st.write("Sauvegarde du nouveau rôle")
                success, message = save_to_list_form_git("architects_roles", creator["role"])
                if success:
                    st.success(message)
                else:
                    st.error(message)
        
        if type_entry == "ensemble":
            creator["role"] = st.selectbox("Rôle :",
                                            load_list_form("artists_roles", "architects_roles"),
                                            index=None,
                                            key=f"{xml_id}_creator_ensemble_xmlid_{idx}"
                                            )
            if creator["role"] is not None and creator["role"] not in load_list_form("artists_roles", "architects_roles"):
                st.write("Sauvegarde du nouveau rôle dans la liste des rôles des artistes")
                success, message = save_to_list_form_git("artists_roles", creator["role"])
                if success:
                    st.success(message)
                else:
                    st.error(message)
    return creator

def _add_work_core(xml_id, work, idx, list_xml_id, title, link_types_key, key_prefix):
    st.subheader(f"{title} {idx + 1}")
    col1, col2 = st.columns(2)

    with col1:
        work["link_type"] = st.selectbox(
            "Type de lien",
            load_list_form(link_types_key),
            key=f"{xml_id}_{key_prefix}_type_{idx}",
            index=None,
            accept_new_options=True,
        )

        if work["link_type"] is not None and work["link_type"] not in load_list_form(link_types_key):
            st.write("Sauvegarde du nouveau type de lien")
            success_link, message_link = save_to_list_form_git(link_types_key, work["link_type"])
            if success_link:
                st.success(message_link)
            else:
                st.error(message_link)

    with col2:
        work["xml_id_work"] = st.selectbox(
            f"XML:id de l'oeuvre liée {idx + 1}",
            list_xml_id,
            index=None,
            key=f"{xml_id}_{key_prefix}_xmlid_{idx}",
        )
    return work

def add_related_work(xml_id, work, idx, list_xml_id):
    return _add_work_core(
        xml_id, work, idx, list_xml_id,
        title="Œuvre liée",
        link_types_key="link_types",
        key_prefix="related_work",
    )

def add_contained_work(xml_id, work, idx, list_xml_id):
    return _add_work_core(
        xml_id, work, idx, list_xml_id,
        title="Œuvre contenue dans l'ensemble",
        link_types_key="link_types_contained",
        key_prefix="contained_work",
    )

def add_bibliography(xml_id, biblio, idx):
    """Édite une référence bibliographique"""
    st.subheader(f"Référence {idx + 1}")
    col1, col2 = st.columns(2)

    with col1:
        zotero_list = load_list_form("zotero_keys")

        # Valeur actuelle
        current_value = biblio.get("zotero_key", None)

        biblio["zotero_key"] = st.selectbox(
            "Clé Zotero",
            zotero_list,
            key=f"{xml_id}_biblio_key_{idx}",
            index=zotero_list.index(current_value) if current_value in zotero_list else None,
            accept_new_options=True
        )

        if biblio["zotero_key"] is not None and biblio["zotero_key"] not in zotero_list:
            st.write("Sauvegarde de l'entrée bibliographique")
            success, message = save_to_list_form_git("zotero_keys", biblio["zotero_key"])
            if success:
                st.success(message)
            else:
                st.error(message)

    with col2:
        biblio["location"] = st.text_input(
            "Localisation",
            biblio.get("location", ""),
            key=f"{xml_id}_biblio_loc_{idx}"
        )
    return biblio


def add_illustration(xml_id, illus, idx):
    """Édite une illustration existante (hors formulaire)."""

    st.markdown(f"### Illustration {idx + 1}")

    # --- Initialisations dans session_state ---
    if "type_illustration_add" not in st.session_state:
        st.session_state.type_illustration_add = {}
    if "show_image_add" not in st.session_state:
        st.session_state.show_image_add = {}

    if illus is None:
        illus = {
            "id": idx,
            "url": "",
            "storage": "",
            "copyright": "",
            "caption": ""
        }


    # Déduction automatique du type si non défini
    if idx not in st.session_state.type_illustration_add:
        existing_storage = illus.get("storage", "")
        st.session_state.type_illustration_add[idx] = (
            "URL" if existing_storage == "online" else
            "local" if existing_storage == "local" else
            None
        )

    if idx not in st.session_state.show_image_add:
        st.session_state.show_image_add[idx] = False


    # --- Colonnes de structure ---
    colA, colB, colPreview = st.columns([1, 6, 4])

    # --- Choix du mode (boutons) ---
    with colA:
        if st.button("➕ URL", key=f"{xml_id}_edit_url_btn_{idx}"):
            st.session_state.type_illustration_add[idx] = "URL"
            st.session_state.show_image_add[idx] = False

        if st.button("📁 Local", key=f"{xml_id}_edit_local_btn_{idx}"):
            st.session_state.type_illustration_add[idx] = "local"
            st.session_state.show_image_add[idx] = False


    # --- Champs selon le mode ---
    with colB:
        illus_id = st.number_input("ID", value=illus.get("id", idx), key=f"{xml_id}_edit_illus_id_{idx}", disabled=True)
        illus["id"] = illus_id

        mode = st.session_state.type_illustration_add[idx]

        # ---- MODE URL ----
        if mode == "URL":
            col_url, col_btn = st.columns([5,1])
            with col_url:
                url = st.text_input("URL", illus.get("url", ""), key=f"{xml_id}_edit_illus_url_{idx}")
            with col_btn:
                if st.button("Voir", key=f"{xml_id}_edit_show_url_{idx}"):
                    st.session_state.show_image_add[idx] = True

            illus["storage"] = "online"
            illus["url"] = url

        # ---- MODE LOCAL ----
        elif mode == "local":
            col_up, col_btn = st.columns([5,1])
            with col_up:
                uploaded = st.file_uploader(
                    "Fichier (jpg/png)",
                    type=["jpg", "jpeg", "png"],
                    key=f"{xml_id}_edit_upload_{idx}"
                )
            with col_btn:
                if st.button("Voir/Sauvegarder", key=f"{xml_id}_edit_show_local_{idx}"):
                    st.session_state.show_image_add[idx] = True
                    st.image(uploaded, caption="Prévisualisation")

            illus["storage"] = "local"

            # Si on voit l'image + fichier chargé → sauvegarde
            if st.session_state.show_image_add[idx] and uploaded is not None:
                local_path = save_image(uploaded)
                illus["url"] = local_path
            else:
                # garde l’existant
                illus["url"] = illus.get("url", None)

        else:
            st.info("Choisissez un mode : URL ou Local")
        
        with colPreview:
            if st.session_state.show_image_add[idx]:
                if illus.get("url", None):
                    st.image(illus["url"], caption="Prévisualisation")
                else:
                    st.warning("Aucune image à afficher.")


        # Champs communs
        illus["copyright"] = st.text_input(
            "Droits",
            illus.get("copyright", ""),
            key=f"{xml_id}_edit_illus_copyright_{idx}"
        )

        exemple_desc_image()

        illus["caption"] = st.text_input(
            "Légende",
            illus.get("caption", ""),
            key=f"{xml_id}_edit_illus_caption_{idx}",
            help="""
            Pour précisier des informations sur l'image, en particulier si l'image ne correspond pas exactement à l'œuvre décrite dans la notice (une copie, un dessin préparatoire,...) """
        )

def add_notice():
    st.title("➕ Ajouter une notice")

    entry_editor = st.selectbox(
        "Créateur de la notice : *",
        load_list_form("usernames"),
        index=index_username()
    )

    entry_type_display = st.radio(
        "Type de notice *",
        ["🖼️ Œuvre", "🏛️ Architecture", "🌿 Ensemble"],
        horizontal=True
    )

    entry_type = {
        "🖼️ Œuvre": "artwork",
        "🏛️ Architecture": "building",
        "🌿 Ensemble": "ensemble"
    }[entry_type_display]


    # =========================
    # Choix ID + type
    # =========================
    xml_id = st.text_input(
        "XML:ID *",
        help="Identifiant unique de la notice"
    )

    if exist_notice(xml_id) == True:
        st.error(f"Une notice avec le XML:ID '{xml_id}' existe déjà. Veuillez choisir un autre identifiant.")
        st.stop()

    if not xml_id:
        st.warning("Veuillez saisir un XML:ID")
        st.stop()

    valid_pattern = re.compile(r"^[A-Za-z0-9]+$")
    
    if xml_id and not valid_pattern.match(xml_id):
        st.error("Vous ne pouvez pas utiliser de caractères spéciaux pour l'identifiant de la notice (ni accent, ni espace)")
        st.stop()



    # =========================
    # Initialisation session
    # =========================
    if (
        "creating_notice" not in st.session_state
        or st.session_state.creating_notice["id"] != xml_id
        or st.session_state.creating_notice["entry_type"] != entry_type
    ):
        st.session_state.creating_notice = init_empty_notice(xml_id, entry_type)

    notice = st.session_state.creating_notice

    if "wikidata_data" not in st.session_state:
        st.session_state["wikidata_data"] = {}
    wikidata_data = st.session_state.get("wikidata_data", {})

    # =========================
    # INFOS GÉNÉRALES
    # =========================
    st.header("📋 Informations générales")

    colWiki1, colWiki2 = st.columns([4, 1])
    
    with colWiki1:
        notice["QID_wikidata"] = st.text_input(
            "QID Wikidata",
            notice.get("QID_wikidata", "")
        )
    
    with colWiki2:
        if st.button("Recherche Wikidata"):
            url_wikidata = notice.get("QID_wikidata", "")
            if not url_wikidata:
                st.warning("Veuillez entrer un QID.")
            if entry_type == "building":
                wikidata_data = get_monument_data(notice["QID_wikidata"])
                st.session_state["wikidata_dic"] = wikidata_data
            if entry_type == "ensemble":
                st.warning("La fonction n'existe pas encore")
            if entry_type == "artwork":
                st.warning("La fonction n'existe pas encore")

    notice["title"] = st.text_input(
        "Titre *",
        notice.get("title", "")
    )

    # =========================
    # CRÉATEURS (LOGIQUE ÉDITEUR)
    # =========================
    st.header("👥 Créateurs")

    if "creator" not in notice:
        notice["creator"] = []

    for idx, creator in enumerate(notice["creator"]):
        notice["creator"][idx] = add_creator(
            notice["id"], creator, idx, entry_type
        )
        if st.button(
            f"Supprimer créateur {idx + 1}",
            key=f"del_creator_create_{idx}"
        ):
            notice["creator"].pop(idx)
            st.rerun()

    if st.button("➕ Ajouter un créateur"):
        notice["creator"].append({"xml_id": "", "role": ""})
        st.rerun()

    if entry_type == "artwork":
        st.header("🎨 Matériaux & Techniques")

        notice["materialsAndTechniques"] = st.selectbox(
                    "Matériaux et techniques",
                    load_list_form("techniques"),
                    index=None,
                    accept_new_options=True
                    )
        if notice["materialsAndTechniques"] is not None and notice["materialsAndTechniques"] not in load_list_form("techniques"):
            st.write("Sauvegarde de la technique")
            success, message = save_to_list_form_git("techniques", notice["materialsAndTechniques"])
            if success:
                st.success(message)
            else:
                st.error(message)
    
    if entry_type == "building":
        st.header("Typologie de monument")

        notice["typology"] = st.selectbox(
                    "Typologie",
                    load_list_form("typologies_architecture"),
                    index=None,
                    accept_new_options=True
                    )

        if notice["typology"] is not None and notice["typology"] not in load_list_form("typologies_architecture"):
            st.write("Sauvegarde de la nouvelle typologie")
            success, message = save_to_list_form_git("typologies_architecture", notice["typology"])
            if success:
                st.success(message)
            else:
                st.error(message)
    
    if entry_type == "ensemble":
        st.header("Typologie d'ensemble")

        notice["typology"] = st.selectbox(
                    "Typologie",
                    load_list_form("typologies_ensemble"),
                    index=None,
                    accept_new_options=True
                    )
        
        if notice["typology"] is not None and notice["typology"] not in load_list_form("typologies_ensemble"):
            st.write("Sauvegarde de la nouvelle typologie")
            success, message = save_to_list_form_git("typologies_ensemble", notice["typology"])
            if success:
                st.success(message)
            else:
                st.error(message)

    # =========================
    # DATATION
    # =========================
    st.header("📅 Date de création")

    col1, col2, col3 = st.columns([1,1,3])
    start_year = notice["dateCreated"].get("startYear")
    end_year = notice["dateCreated"].get("endYear")

    with col1:
        notice["dateCreated"]["startYear"] = st.number_input(
            "Année début",
            min_value=-10000,
            max_value=3000,
            value = int(start_year) if start_year not in ("", None) else None,
            step=1,
            format="%d"
        )

    with col2:
        notice["dateCreated"]["endYear"] = st.number_input(
            "Année fin",
            min_value=-10000,
            max_value=3000,
            value=int(end_year) if end_year not in ("", None) else None,
            step=1,
            format="%d"
        )
    with col3:
        notice["dateCreated"]["text"] = st.text_input(
            "Texte",
            notice["dateCreated"].get("text", "")
        )

    # =========================
    # LOCALISATION
    # =========================
    st.header("🏛️ Institution de conservation / 📍 Localisation")

    # ----------------------------
    # Déduction du type par défaut
    # ----------------------------
    if entry_type == "artwork":
        index_type_location = 0
    elif entry_type == "building":
        index_type_location = 1
    elif entry_type == "ensemble":
        index_type_location = 0
    else:
        index_type_location = 2

    # ----------------------------
    # Choix du type de localisation
    # ----------------------------
    type_location_label = st.radio(
        "Type de localisation",
        [
            "🏛️ Institution de conservation (musée, église)",
            "📍 Localisation (pour les bâtiments)",
            "Non localisée",
            "Plusieurs localisations"
        ],
        horizontal=True,
        index=index_type_location
    )

    # mapping label → valeur interne
    location_type = {
        "🏛️ Institution de conservation (musée, église)": "holding_institution",
        "📍 Localisation (pour les bâtiments)": "place",
        "Non localisée": "unlocated",
        "Plusieurs localisations": "multiple_locations"
    }[type_location_label]

    # ----------------------------
    # Initialisation
    # ----------------------------
    if "location" not in notice or not isinstance(notice["location"], dict):
        notice["location"] = {}

    notice["location"]["type"] = location_type

    # ----------------------------
    # CAS : LOCALISATION GÉOGRAPHIQUE
    # ----------------------------

    place = notice["location"].get("place", {})
    if location_type == "place":

        if "place_city" not in st.session_state:
            st.session_state["place_city"] = place.get("city", None)

        if "place_country" not in st.session_state:
            st.session_state["place_country"] = place.get("country", None)

        colVille, colPays = st.columns([1, 1])

        with colVille:
            st.selectbox(
                "Ville",
                load_list_form("places"),
                index=None,
                accept_new_options=True,
                key="place_city"
            )
            
            # Sauvegarder nouvelle valeur si inconnue
            if st.session_state["place_city"] and st.session_state["place_city"] not in load_list_form("places"):
                with st.spinner("Sauvegarde de la nouvelle ville"):
                    success_ville, message_ville = save_to_list_form_git("places", st.session_state["place_city"])
                    if success_ville:
                        st.success(message_ville)
                    else:
                        st.error(message_ville)

            # Sauvegarder dans le json temporaire
            place["city"] = st.session_state["place_city"]

        with colPays:
            st.selectbox(
                "Pays",
                load_list_form("places"),
                index=None,
                accept_new_options=True,
                key="place_country"
            )

            if st.session_state["place_country"] and st.session_state["place_country"] not in load_list_form("places"):
                with st.spinner("Sauvegarde du nouveau pays"):
                    success_pays, message_pays = save_to_list_form_git("places", st.session_state["place_country"])
                    if success_pays:
                        st.success(message_pays)
                    else:
                        st.error(message_pays)

            place["country"] = st.session_state["place_country"]


        coordinates = place.get("coordinates", {})

        colLat, colLong = st.columns([1, 1])
        with colLat:
            coordinates["latitude"] = st.text_input(
                "Latitude",
                value=str(
                    wikidata_data.get("latitude")
                    if wikidata_data.get("latitude") is not None
                    else coordinates.get("latitude", "")
                ),
                disabled=True
            )

        with colLong:
            coordinates["longitude"] = st.text_input(
                "Longitude",
                value=str(
                    wikidata_data.get("longitude")
                    if wikidata_data.get("longitude") is not None
                    else coordinates.get("longitude", "")
                ),
                disabled=True
            )

        place["coordinates"] = coordinates
        notice["location"]["place"] = place

    # ----------------------------
    # CAS : INSTITUTION
    # ----------------------------
    elif location_type == "holding_institution":

        institution = notice["location"].get("institution", {})

        institution["name"] = st.selectbox(
            "Nom de l'institution",
            load_list_form("institutions"),
            index=None,
            accept_new_options=True,
            key=f"{xml_id}_institution"
        )
        if institution["name"] and institution["name"] not in load_list_form("institutions"):
            with st.spinner("Sauvegarde de la nouvelle institution"):
                success_institution, message_institution = save_to_list_form_git("institutions", institution["name"])
                if success_institution:
                    st.success(message_institution)
                else:
                    st.error(message_institution)

        institution["place"] = st.selectbox(
                "Ville de l'institution",
                load_list_form("places"),
                index=None,
                accept_new_options=True,
                key="institution_city"
            )
            
        # Sauvegarder nouvelle valeur si inconnue
        if st.session_state["institution_city"] and st.session_state["institution_city"] not in load_list_form("places"):
                with st.spinner("Sauvegarde de la nouvelle ville"):
                    success_inst_ville, message_inst_ville = save_to_list_form_git("places", st.session_state["institution_city"])
                    if success_inst_ville:
                        st.success(message_inst_ville)
                    else:
                        st.error(message_inst_ville)


        institution["inventory_number"] = st.text_input(
            "Numéro d'inventaire",
            value=institution.get("inventory_number", "")
        )

        institution["url"] = st.text_input(
            "URL de l'oeuvre sur le site de l'institution",
            value=institution.get("url", "")
        )

        notice["location"]["institution"] = institution

    # ----------------------------
    # CAS : NON LOCALISÉ
    # ----------------------------
    elif location_type == "unlocated":
        notice["location"] = {"type": "unlocated"}
    
    elif location_type == "multiple_locations":
        notice["location"] = {"type": "multiple_locations"}

    else:
        notice["location"] = {"type": "unlocated"}

    # =========================
    # ŒUVRES LIÉES
    # =========================
    st.header("🔗 Œuvres liées")

    if "related_works" not in notice:
        notice["related_works"] = []

    list_xml_id = get_all_objects_ids_flat_sorted()

    for idx, work in enumerate(notice["related_works"]):
        notice["related_works"][idx] = add_related_work(
            notice["id"], work, idx, list_xml_id
        )
        if st.button(
            f"Supprimer œuvre {idx + 1}",
            key=f"del_work_create_{idx}"
        ):
            notice["related_works"].pop(idx)
            st.rerun()

    if st.button("➕ Ajouter une œuvre liée"):
        notice["related_works"].append({
            "link_type": "",
            "xml_id_work": ""
        })
        st.rerun()

    # =========================
    # ENSEMBLE : oeuvres constituantes et oeuvres d'ensemble
    # =========================

    if entry_type == "ensemble":
        st.header("🌿 Œuvres constituantes de l'ensemble")
        if "contains_works" not in notice:
            notice["contains_works"] = []
        
        list_xml_id_contained = get_all_objects_ids_flat_sorted(["artwork", "building"])

        for idx, work in enumerate(notice["contains_works"]):
            notice["contains_works"][idx] = add_contained_work(
                notice["id"], work, idx, list_xml_id_contained
            )
            if st.button(
                f"Supprimer œuvre {idx + 1}",
                key=f"{xml_id}_del_contained_work_{idx}"
            ):
                notice["contains_works"].pop(idx)
                st.rerun()

        if st.button("➕ Ajouter une œuvre contenue", key=f"{xml_id}_add_contained_work"):
            notice["contains_works"].append({
                "link_type": "",
                "xml_id_work": ""
            })
            st.rerun()

    if entry_type in {"building", "artwork"}:
        st.header("🌿 Ensemble contenant l'œuvre")

        has_ensemble = st.radio(
            "Cette œuvre appartient-elle à un ensemble ?",
            ["Non", "Oui"],
            horizontal=True,
            key=f"{xml_id}_has_ensemble"
        )

        # Si NON → reset
        if has_ensemble == "Non":
            notice["contained_by_ensemble"] = {}

        # Si OUI → afficher les champs
        else:
            notice.setdefault("contained_by_ensemble", {})

            list_xml_id_ensemble = get_all_objects_ids_flat_sorted(["ensemble"])

            col1, col2 = st.columns(2)

            with col1:
                link_types_contained = load_list_form("link_types_contained")

                notice["contained_by_ensemble"]["link_type"] = st.selectbox(
                    "Type de lien",
                    link_types_contained,
                    key=f"{xml_id}_contained_by_ensemble_type",
                    index=None,
                    accept_new_options=True,
                )

                # sauvegarde du lien
                if notice["contained_by_ensemble"]["link_type"] and notice["contained_by_ensemble"]["link_type"] not in link_types_contained:
                    success_link_contained, message_link_contained = save_to_list_form_git("link_types_contained", notice["contained_by_ensemble"]["link_type"])
                    if success_link_contained:
                        st.success(message_link_contained)
                    else:
                        st.error(message_link_contained)

            with col2:
                notice["contained_by_ensemble"]["xml_id_work"] = st.selectbox(
                    "Ensemble contenant l'œuvre",
                    list_xml_id_ensemble,
                    placeholder="XML:ID de l'oeuvre liée",
                    accept_new_options=False,
                    index=None,
                    key=f"{xml_id}_contained_by_ensemble_xmlid"
                )

    # =========================
    # ILLUSTRATIONS (MENU ÉDITION)
    # =========================

    st.header("Bibliographie")

    if "bibliography" not in notice:
        notice["bibliography"] = []

    colBibl1, colBibl2 = st.columns([1, 4])

    with colBibl1:
        nbr_bibliography = st.radio(
            "Nombre d'ouvrages",
            [0, 1, 2, 3],
            index=len(notice["bibliography"])
        )

    with colBibl2:
        # Ajuster dynamiquement la taille de la liste
        while len(notice["bibliography"]) < nbr_bibliography:
            notice["bibliography"].append({
                "zotero_key": "",
                "location": ""
            })

        while len(notice["bibliography"]) > nbr_bibliography:
            notice["bibliography"].pop()

        # Utilisation de ta fonction existante
        for idx, biblio in enumerate(notice["bibliography"]):
            notice["bibliography"][idx] = add_bibliography(xml_id, biblio, idx)

    

    # =========================
    # ILLUSTRATIONS (MENU ÉDITION)
    # =========================
    st.header("🖼️ Illustrations")

    if "illustrations" not in notice:
        notice["illustrations"] = []

    for idx, illus in enumerate(notice["illustrations"]):
        add_illustration(notice["id"], illus, idx)

        if st.button(
            f"Supprimer illustration {idx + 1}",
            key=f"del_illus_create_{idx}"
        ):
            notice["illustrations"].pop(idx)
            st.rerun()

    if st.button("➕ Ajouter une illustration"):
        notice["illustrations"].append({
            "id": len(notice["illustrations"]),
            "url": "",
            "storage": "",
            "copyright": "",
            "caption": ""
        })
        st.rerun()

    # =========================
    # TEXTES
    # =========================
    st.header("💬 Textes")

    description = st.text_area(
        "Description",
        notice.get("description", ""),
        key=f"description_{xml_id}"
    )

    notice["description"] = description

    commentaire = st.text_area(
        "Commentaire",
        notice.get("commentary", ""),
        key=f"commentaire_{xml_id}"
    )

    notice["commentary"] = commentaire

    # =========================
    # Statut de la notice
    # =========================    

    notice["status_entry"] = st.selectbox(
        "Statut de la notice",
        options=list(STATUS_ENTRY_OPTIONS.keys()),
        format_func=lambda x: STATUS_ENTRY_OPTIONS[x],
        index=list(STATUS_ENTRY_OPTIONS.keys()).index(
            int(notice["status_entry"]) if notice.get("status_entry") not in (None, "") else 0
        ),
    )


    # =========================
    # SAUVEGARDE
    # =========================
    st.divider()

    if st.button("💾 Créer la notice", type="primary"):

        if not notice["id"] or not notice["title"]:
            st.error("XML:ID et Titre sont obligatoires.")
            return

        notice["history"].append({
            "date": datetime.now().isoformat(),
            "type": "created",
            "author": entry_editor
        })

        with st.spinner("Enregistement de la notice et ajout sur github"):
            path = save_notice(notice)
            message = f"ajout notice {xml_id} par {entry_editor} {datetime.now().isoformat()}"
            git_commit_and_push(message)
            st.success(f"✅ Notice ajoutée avec succès sur github !\n\n📁 Fichier créé : `{path}`")
            st.balloons()
            st.session_state.pop("creating_notice")
        time.sleep(3)

        st.rerun()
    
    with st.expander("📄 Voir le JSON complet"):
        st.json(notice, expanded=False)
