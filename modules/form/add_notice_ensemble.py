import streamlit as st
from datetime import datetime
import time
import uuid

from modules.data_loader import save_notice, exist_notice, save_image, load_list_form, index_username, save_to_list_form, get_all_objects_ids_flat_sorted
from modules.git_tools import git_commit_and_push

def init_empty_notice(xml_id, entry_type):
    return {
        "id": xml_id,
        "QID_wikidata": "",
        "entry_type": entry_type,
        "title": "",
        "creator": [],
        "dateCreated": {
            "startYear": "",
            "endYear": "",
            "text": ""
        },
        "location": "",
        "related_works": [],
        "bibliography": [],
        "illustrations": [],
        "description": "",
        "commentary": "",
        "history": []
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
    with col2:
        if type_entry == "peinture":
            creator["role"] = st.selectbox("Rôle :",
                                            load_list_form("artists_roles"),
                                            key=f"{xml_id}_creator_painting_xmlid_{idx}"
                                            )
        if type_entry == "architecture":
            creator["role"] = st.selectbox("Rôle :",
                                            load_list_form("architects_roles"),
                                            key=f"{xml_id}_creator_architect_xmlid_{idx}"
                                            )
        
        if type_entry == "ensemble":
            creator["role"] = st.selectbox("Rôle :",
                                            load_list_form("artists_roles", "architects_roles"),
                                            key=f"{xml_id}_creator_ensemble_xmlid_{idx}"
                                            )
    return creator

def add_related_work(xml_id, work, idx, list_xml_id):
    """Édite une œuvre liée"""
    st.subheader(f"Œuvre liée {idx + 1}")
    col1, col2 = st.columns(2)
    with col1:
        work["link_type"] = st.selectbox(
                    f"Type de lien",
                    load_list_form("link_types"),
                    key=f"{xml_id}_work_type_{idx}",
                    accept_new_options=True,
                    )
    with col2:
        work["xml_id_work"] = st.selectbox(
            f"XML:id de l'oeuvre liée {idx + 1}",
            list_xml_id,
            placeholder="XML:ID de l'oeuvre liée",
            accept_new_options=False,
            key=f"{xml_id}_work_xmlid_{idx}"
        )
    return work

def add_bibliography(xml_id, biblio, idx):
    """Édite une référence bibliographique"""
    st.subheader(f"Référence {idx + 1}")
    col1, col2 = st.columns(2)
    with col1:
        biblio["zotero_key"] = st.text_input(f"Clé Zotero", biblio.get("zotero_key", ""), key=f"{xml_id}_biblio_key_{idx}")
    with col2:
        biblio["location"] = st.text_input(f"Localisation", biblio.get("location", ""), key=f"{xml_id}_biblio_loc_{idx}")
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
        illus_id = st.number_input("ID", value=illus.get("id", idx), key=f"{xml_id}_edit_illus_id_{idx}")
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
                    st.image(url, caption="Prévisualisation")

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

        illus["caption"] = st.text_input(
            "Légende",
            illus.get("caption", ""),
            key=f"{xml_id}_edit_illus_caption_{idx}"
        )

def add_notice_ensemble():
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
        "🖼️ Œuvre": "peinture",
        "🏛️ Architecture": "architecture",
        "🌿 Ensemble": "ensemble"
    }[entry_type_display]


    # =========================
    # Choix ID + type
    # =========================
    xml_id = st.text_input(
        "XML:ID *",
        help="Identifiant unique de la notice"
    )

    if not xml_id:
        st.warning("Veuillez saisir un XML:ID")
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

    # =========================
    # INFOS GÉNÉRALES
    # =========================
    st.header("📋 Informations générales")

    notice["QID_wikidata"] = st.text_input(
        "QID Wikidata",
        notice.get("QID_wikidata", "")
    )

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

    if entry_type == "peinture":
        st.header("🎨 Matériaux & Techniques")

        notice["materialsAndTechniques"] = st.selectbox(
                    "Matériaux et techniques",
                    load_list_form("techniques")
                    )
    
    if entry_type == "architecture":
        st.header("Typologie de monument")

        notice["typology"] = st.selectbox(
                    "Typologie",
                    load_list_form("typologies_architecture")
                    )
    
    if entry_type == "ensemble":
        st.header("Typologie d'ensemble")

        notice["typology"] = st.selectbox(
                    "Typologie",
                    load_list_form("typologies_ensemble")
                    )

    # =========================
    # DATATION
    # =========================
    st.header("📅 Date de création")

    col1, col2, col3 = st.columns(3)
    with col1:
        notice["dateCreated"]["startYear"] = st.text_input(
            "Année début",
            notice["dateCreated"].get("startYear", "")
        )
    with col2:
        notice["dateCreated"]["endYear"] = st.text_input(
            "Année fin",
            notice["dateCreated"].get("endYear", "")
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
    if entry_type == "peinture":
        index_type_location = 0
    elif entry_type == "architecture":
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
            "Non localisée"
        ],
        horizontal=True,
        index=index_type_location
    )

    # mapping label → valeur interne
    location_type = {
        "🏛️ Institution de conservation (musée, église)": "holding_institution",
        "📍 Localisation (pour les bâtiments)": "place",
        "Non localisée": "unlocated"
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
    if location_type == "place":

        place = notice["location"].get("place", {})

        place["city"] = st.text_input(
            "Ville",
            value=place.get("city", "")
        )
        place["country"] = st.text_input(
            "Pays",
            value=place.get("country", "")
        )

        coordinates = place.get("coordinates", {})

        coordinates["latitude"] = st.text_input(
            "Latitude",
            value=coordinates.get("latitude", "")
        )
        coordinates["longitude"] = st.text_input(
            "Longitude",
            value=coordinates.get("longitude", "")
        )

        place["coordinates"] = coordinates
        notice["location"]["place"] = place

    # ----------------------------
    # CAS : INSTITUTION
    # ----------------------------
    elif location_type == "holding_institution":

        institution = notice["location"].get("institution", {})

        institution["name"] = st.text_input(
            "Nom de l'institution",
            value=institution.get("name", "")
        )
        institution["place"] = st.text_input(
            "Lieu",
            value=institution.get("place", "")
        )
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

    notice["description"] = st.text_area(
        "Description",
        notice.get("description", "")
    )

    notice["commentary"] = st.text_area(
        "Commentaire",
        notice.get("commentary", "")
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

        path = save_notice(notice)
        st.success(f"✅ Notice créée : {path}")

        st.session_state.pop("creating_notice")
        st.balloons()
        time.sleep(2)
        st.rerun()
