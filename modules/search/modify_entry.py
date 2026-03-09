import streamlit as st
import json
from datetime import datetime

from modules.data.load import load_notice, save_notice, index_list_form, load_list_form, index_username, get_all_objects_ids_flat_sorted, save_image, save_to_list_form
from modules.utils.functions import safe_int

def edit_creator(xml_id, creator, idx, type_entry):
    """Édite un artiste"""
    st.subheader(f"Artiste {idx + 1}")
    col1, col2 = st.columns(2)
    with col1:
        creator["xml_id"] = st.selectbox("Artiste :*",
                                     load_list_form("persons"),
                                     index=index_list_form(creator.get("xml_id", ""), "persons"),
                                     accept_new_options=True,
                                     key=f"{xml_id}_creator_xmlid_{idx}"
                                     )
    with col2:
        if type_entry == "peinture":
            creator["role"] = st.selectbox("Rôle :",
                                            load_list_form("artists_roles"),
                                            index=index_list_form(creator.get("role", ""), "artists_roles"),
                                            key=f"{xml_id}_creator_painting_xmlid_{idx}"
                                            )
        if type_entry == "architecture":
            creator["role"] = st.selectbox("Rôle :",
                                            load_list_form("architects_roles"),
                                            index=index_list_form(creator.get("role", ""), "architects_roles"),
                                            key=f"{xml_id}_creator_architect_xmlid_{idx}"
                                            )
            
        if type_entry == "ensemble":
            creator["role"] = st.selectbox("Rôle :",
                                            load_list_form("artists_roles", "architects_roles"),
                                            index=index_list_form(creator.get("role", ""), 
                                                                  ["artists_roles", "architects_roles"]),
                                            key=f"{xml_id}_creator_ensemble_xmlid_{idx}"
                                            )

    return creator

def edit_related_work(xml_id, work, idx, list_xml_id):
    """Édite une œuvre liée"""
    st.subheader(f"Œuvre liée {idx + 1}")

    work.setdefault("link_type", None)
    work.setdefault("xml_id_work", None)

    link_types = load_list_form("link_types")

    col1, col2 = st.columns(2)

    with col1:
        work["link_type"] = st.selectbox(
            "Type de lien",
            link_types,
            key=f"{xml_id}_work_type_{idx}",
            accept_new_options=True,
            index=index_list_form(work.get("link_type"), "link_types"),
        )

        if work["link_type"] and work["link_type"] not in link_types:
            save_to_list_form("link_types", work["link_type"])

    with col2:
        xml_id_value = work.get("xml_id_work")
        xml_index = (
            list_xml_id.index(xml_id_value)
            if xml_id_value in list_xml_id
            else None
        )

        work["xml_id_work"] = st.selectbox(
            f"XML:id de l'oeuvre liée {idx + 1}",
            list_xml_id,
            index=xml_index,
            placeholder="XML:ID de l'oeuvre liée",
            key=f"{xml_id}_work_xmlid_{idx}",
        )

    return work

def edit_contained_work(xml_id, work, idx, list_xml_id):
    """Édite une œuvre contenue dans un ensemble"""
    st.subheader(f"Œuvre contenue {idx + 1}")

    work.setdefault("link_types_contained", None)
    work.setdefault("xml_id_work", None)

    link_types_contained = load_list_form("link_types_contained")

    col1, col2 = st.columns(2)

    with col1:
        work["link_type"] = st.selectbox(
            "Type de lien",
            link_types_contained,
            key=f"{xml_id}_contained_work_type_{idx}",
            accept_new_options=True,
            index=index_list_form(
                work.get("link_type"),
                "link_types_contained",
            ),
        )

        if work["link_type"] and work["link_type"] not in link_types_contained:
            save_to_list_form(
                "link_types_contained",
                work["link_type"],
            )

    with col2:
        xml_id_value = work.get("xml_id_work")
        xml_index = (
            list_xml_id.index(xml_id_value)
            if xml_id_value in list_xml_id
            else None
        )

        work["xml_id_work"] = st.selectbox(
            "Œuvre contenue dans l'ensemble",
            list_xml_id,
            index=xml_index,
            placeholder="XML:ID de l'œuvre",
            key=f"{xml_id}_contained_work_xmlid_{idx}",
        )

    return work

def edit_bibliography(xml_id, biblio, idx):
    """Édite une référence bibliographique"""
    st.subheader(f"Référence {idx + 1}")
    col1, col2 = st.columns(2)
    with col1:
        biblio["zotero_key"] = st.text_input(f"Clé Zotero", biblio.get("zotero_key", ""), key=f"{xml_id}_biblio_key_{idx}")
    with col2:
        biblio["location"] = st.text_input(f"Localisation", biblio.get("location", ""), key=f"{xml_id}_biblio_loc_{idx}")
    return biblio


# ==== Illustrations ====

def edit_illustration(xml_id, illus, idx):
    """Édite une illustration existante (hors formulaire)."""

    st.markdown(f"### Illustration {idx + 1}")

    # --- Initialisations dans session_state ---
    if "type_illustration_edit" not in st.session_state:
        st.session_state.type_illustration_edit = {}
    if "show_image_edit" not in st.session_state:
        st.session_state.show_image_edit = {}

    # Déduction automatique du type si non défini
    if idx not in st.session_state.type_illustration_edit:
        existing_storage = illus.get("storage", "")
        st.session_state.type_illustration_edit[idx] = (
            "URL" if existing_storage == "online" else
            "local" if existing_storage == "local" else
            None
        )

    if idx not in st.session_state.show_image_edit:
        st.session_state.show_image_edit[idx] = False


    # --- Colonnes de structure ---
    colA, colB, colPreview = st.columns([1, 6, 4])

    # --- Choix du mode (boutons) ---
    with colA:
        if st.button("➕ URL", key=f"{xml_id}_edit_url_btn_{idx}"):
            st.session_state.type_illustration_edit[idx] = "URL"
            st.session_state.show_image_edit[idx] = False

        if st.button("📁 Local", key=f"{xml_id}_edit_local_btn_{idx}"):
            st.session_state.type_illustration_edit[idx] = "local"
            st.session_state.show_image_edit[idx] = False


    # --- Champs selon le mode ---
    with colB:
        illus_id = st.number_input("ID", value=illus.get("id", idx), key=f"{xml_id}_edit_illus_id_{idx}", disabled=True)
        illus["id"] = illus_id

        mode = st.session_state.type_illustration_edit[idx]

        # ---- MODE URL ----
        if mode == "URL":
            col_url, col_btn = st.columns([5,1])
            with col_url:
                url = st.text_input("URL", illus.get("url", ""), key=f"{xml_id}_edit_illus_url_{idx}")
            with col_btn:
                if st.button("Voir", key=f"{xml_id}_edit_show_url_{idx}"):
                    st.session_state.show_image_edit[idx] = True

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
                    st.session_state.show_image_edit[idx] = True

            illus["storage"] = "local"

            # Si on voit l'image + fichier chargé → sauvegarde
            if st.session_state.show_image_edit[idx] and uploaded is not None:
                local_path = save_image(uploaded)
                illus["url"] = local_path
            else:
                # garde l’existant
                illus["url"] = illus.get("url", None)

        else:
            st.info("Choisissez un mode : URL ou Local")


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


    # --- Prévisualisation ---
    with colPreview:
        if st.session_state.show_image_edit[idx] and illus.get("url"):
            try:
                st.image(illus["url"], caption="Prévisualisation")
            except Exception:
                st.warning("Impossible d'afficher l'image.")
    
    return illus

    # ╔═══════════════════════════════════════════╗
    #            Fonction principale
    # ╚═══════════════════════════════════════════╝


def edit_json_notice(json_path=None, data=None):

    st.title("Éditeur de Notice JSON")
    
    # 1. Charger les données depuis le fichier
    if data is None and json_path:
        data = load_notice(json_path)
    elif data is None:
        st.error("Aucune donnée fournie")
        return None
    

    # 2. Réinitialiser notice_data quand on change de fichier
    if (
        'editing_path' not in st.session_state 
        or st.session_state.editing_path != json_path
    ):
        st.session_state.editing_path = json_path
        st.session_state.notice_data = data.copy()

    # 3. Récupération de la notice active
    notice = st.session_state.notice_data

    id_entry = notice["id"]
    entry_type = notice["entry_type"]

    
    # Section Informations générales
    st.header("📋 Informations générales")
    notice["id"] = st.text_input("ID", notice.get("id", ""))
    notice["QID_wikidata"] = st.text_input("QID Wikidata", notice.get("QID_wikidata", ""))
        
    notice["title"] = st.text_input("Titre", notice.get("title", ""))

    
    if entry_type == "architecture": 
        notice["typology"] = st.selectbox(
                    "Typologie de monument",
                    load_list_form("typologies_architecture"),
                    accept_new_options=True,
                    index=index_list_form(notice.get("typology", ""), "typologies_architecture")
                    )
        
        if notice["typology"] not in load_list_form("typologies_architecture"):
            save_to_list_form("typologies_architecture", notice["typology"])
    
    if entry_type == "ensemble": 
        notice["typology"] = st.selectbox(
                    "Typologie d'ensemble (ex : ensemble décoratif, retable,...)",
                    load_list_form("typologies_ensemble"),
                    accept_new_options=True,
                    index=index_list_form(notice.get("typology", ""), "typologies_ensemble")
                    )
        
        if notice["typology"] not in load_list_form("typologies_ensemble"):
            save_to_list_form("typologies_ensemble", notice["typology"])


    # Section Créateurs
    st.header("👥 Créateurs")
    if "creator" not in notice or not isinstance(notice["creator"], list):
        notice["creator"] = []
    
    for idx, creator in enumerate(notice["creator"]):
        notice["creator"][idx] = edit_creator(id_entry, creator, idx, entry_type)
        if st.button(f"Supprimer créateur {idx + 1}", key=f"{id_entry}_del_creator_{idx}"):
            notice["creator"].pop(idx)
            st.rerun()
    
    if st.button("➕ Ajouter un créateur"):
        notice["creator"].append({"xml_id": "", "role": ""})
        st.rerun()

    # — PEINTURE —
    if entry_type == "peinture":
        st.header("🎨 Matériaux & Techniques")

        notice["materialsAndTechniques"] = st.selectbox(
                    "Matériaux et techniques",
                    load_list_form("techniques"),
                    index=index_list_form(notice.get("materialsAndTechniques", ""), "techniques"),
                    accept_new_options=True
                    )
        
        if not notice["materialsAndTechniques"] in load_list_form("techniques"):
            save_to_list_form("techniques", notice["materialsAndTechniques"])
        
    # — Localisation globale —
    
    st.header("🏛️ Localisation de l'oeuvre")

    # Initialisation robuste
    notice.setdefault("location", {})
    notice["location"].setdefault("type", "")

    location_type = notice["location"]["type"]

    # Liste des options
    LOCATION_OPTIONS = {
        "Non localisé": "unlocated",
        "Institution de conservation (musée, église)": "holding_institution",
        "Lieu (bâtiments)": "place",
        "Plusieurs localisations": "many_locations"
    }

    location_options_list = list(LOCATION_OPTIONS.keys())

    # retrouver la clé correspondant à la valeur stockée
    reverse_options = {v: k for k, v in LOCATION_OPTIONS.items()}

    try:
        location_selected_label = reverse_options[location_type]
        location_selected_index = location_options_list.index(location_selected_label)
    except KeyError:
        location_selected_index = 0

    location_choice = st.radio(
        "Type de localisation",
        location_options_list,
        index=location_selected_index,
        key=f"{id_entry}_location_type",
        horizontal=True
    )

    # récupérer la valeur associée
    location_type = LOCATION_OPTIONS[location_choice]

    notice["location"]["type"] = location_type

        # --- CAS : INSTITUTION DE CONSERVATION ---
    if location_type == "holding_institution":

        notice["location"].setdefault("institution", {})

        institution = notice["location"]["institution"]
        institution.setdefault("name", "")
        institution.setdefault("place", "")
        institution.setdefault("inventory_number", "")
        institution.setdefault("url", "")

        col1, col2 = st.columns(2)

        with col1:
            institution["name"] = st.selectbox(
                "Institution de conservation",
                load_list_form("institutions"),
                index=index_list_form(
                    institution["name"],
                    "institutions"
                    ),
                    accept_new_options=True
                )

            institution["place"] = st.text_input(
                    "Lieu (ville)",
                    institution["place"]
                )

        with col2:
            institution["inventory_number"] = st.text_input(
                    "Numéro d'inventaire",
                    institution["inventory_number"]
                )

            institution["url"] = st.text_input(
                    "URL de l'institution",
                    institution["url"]
                )

        # --- CAS : LIEU GÉOGRAPHIQUE ---
    elif location_type == "place":
        notice["location"].setdefault("place", {})

        place = notice["location"]["place"]
        place.setdefault("city", "")
        place.setdefault("country", "")
        place.setdefault("coordinates", {})
        place["coordinates"].setdefault("latitude", "")
        place["coordinates"].setdefault("longitude", "")

        col1, col2 = st.columns(2)

        with col1:
            place["city"] = st.text_input(
                    "Ville",
                    place["city"]
                )

            place["coordinates"]["latitude"] = st.text_input(
                    "Latitude",
                    place["coordinates"]["latitude"],
                    disabled=True
                )

        with col2:
            place["country"] = st.text_input(
                    "Pays",
                    place["country"]
                )

            place["coordinates"]["longitude"] = st.text_input(
                    "Longitude",
                    place["coordinates"]["longitude"],
                    disabled=True
                )

        
    # Section Date de création
    st.header("📅 Date de création")
    if "dateCreated" not in notice:
        notice["dateCreated"] = {}

    col1, col2, col3 = st.columns([1,1,4])
    with col1:
        notice["dateCreated"]["startYear"] = st.number_input(
            "Année de début",
            min_value=-10000,
            max_value=3000,
            value=safe_int(notice["dateCreated"].get("startYear")),
            step=1,
            format="%d",
            help="Valeurs négatives pour avant J.-C."
        )

    with col2:
        notice["dateCreated"]["endYear"] = st.number_input(
            "Année de fin",
            min_value=-10000,
            max_value=3000,
            value=safe_int(notice["dateCreated"].get("endYear")),
            step=1,
            format="%d",
            help="Valeurs négatives pour avant J.-C."
        )
    with col3:
        notice["dateCreated"]["text"] = st.text_input("Texte date", 
                                                       notice["dateCreated"].get("text", ""))
                    
    # Section Œuvres liées
    st.header("🔗 Œuvres liées")
    if "related_works" not in notice or not isinstance(notice["related_works"], list):
        notice["related_works"] = []

    list_xml_id = get_all_objects_ids_flat_sorted()
    
    for idx, work in enumerate(notice["related_works"]):
        notice["related_works"][idx] = edit_related_work(id_entry, work, idx, list_xml_id)
        if st.button(f"Supprimer œuvre {idx + 1}", key=f"{id_entry}_del_work_{idx}"):
            notice["related_works"].pop(idx)
            st.rerun()
    
    if st.button("➕ Ajouter une œuvre liée"):
        notice["related_works"].append({"link_type": "", "xml_id_work": ""})
        st.rerun()

    if entry_type == "ensemble":
        st.header("📦 Œuvres contenues dans l'ensemble")

        if "contains_works" not in notice or not isinstance(
            notice["contains_works"], list
        ):
            notice["contains_works"] = []

        list_xml_id_contained = get_all_objects_ids_flat_sorted(["peinture", "architecture"])

        for idx, work in enumerate(notice["contains_works"]):
            notice["contains_works"][idx] = edit_contained_work(
                id_entry,
                work,
                idx,
                list_xml_id_contained,
            )

            if st.button(
                f"Supprimer œuvre {idx + 1}",
                key=f"{id_entry}_del_contained_work_{idx}",
            ):
                notice["contains_works"].pop(idx)
                st.rerun()

        if st.button("➕ Ajouter une œuvre à l'ensemble"):
            notice["contains_works"].append(
                {"link_type": "", "xml_id_work": ""}
            )
            st.rerun()

    if entry_type in {"architecture", "peinture"}:
        st.header("🌿 Ensemble contenant l'œuvre")
        if "contained_by_ensemble" not in notice:
            notice["contained_by_ensemble"] = {}
        
        
        list_xml_id_ensemble = get_all_objects_ids_flat_sorted(["ensemble"])

        col1, col2 = st.columns(2)
        with col1:
            notice["contained_by_ensemble"]["link_type"] = st.selectbox(
                        f"Type de lien",
                        load_list_form("link_types_contained"),
                        key=f"{id_entry}_contained_by_ensemble_type",
                        index=index_list_form(notice["contained_by_ensemble"].get("link_type", ""), "link_types_contained"),
                        accept_new_options=True,
                        )
            if not notice["contained_by_ensemble"]["link_type"] in load_list_form("link_types_contained"):
                save_to_list_form("link_types_contained", notice["contained_by_ensemble"]["link_type"])
    
        with col2:
            xml_id_value = notice["contained_by_ensemble"].get("xml_id_work", "")
            xml_index = (
                list_xml_id_ensemble.index(xml_id_value)
                if xml_id_value in list_xml_id_ensemble
                else None
            )
            notice["contained_by_ensemble"]["xml_id_work"] = st.selectbox(
                f"Ensemble contenant l'œuvre",
                list_xml_id_ensemble,
                index=xml_index,
                placeholder="XML:ID de l'oeuvre liée",
                accept_new_options=False,
                key=f"{id_entry}_contained_by_ensemble_xmlid"
            )
    
    # Section Bibliographie
    st.header("📚 Bibliographie")
    if "bibliography" not in notice or not isinstance(notice["bibliography"], list):
        notice["bibliography"] = []
    
    for idx, biblio in enumerate(notice["bibliography"]):
        notice["bibliography"][idx] = edit_bibliography(id_entry, biblio, idx)
        if st.button(f"Supprimer référence {idx + 1}", key=f"{id_entry}_del_biblio_{idx}"):
            notice["bibliography"].pop(idx)
            st.rerun()
    
    if st.button("➕ Ajouter une référence"):
        notice["bibliography"].append({"zotero_key": "", "location": ""})
        st.rerun()
    
    # Section Illustrations
    st.header("🖼️ Illustrations")
    if "illustrations" not in notice or not isinstance(notice["illustrations"], list):
        notice["illustrations"] = []
    
    for idx, illus in enumerate(notice["illustrations"]):
        notice["illustrations"][idx] = edit_illustration(id_entry, illus, idx)
        if st.button(f"Supprimer illustration {idx + 1}", key=f"{id_entry}_del_illus_{idx}"):
            notice["illustrations"].pop(idx)
            st.rerun()
    
    if st.button("➕ Ajouter une illustration"):
        notice["illustrations"].append({
            "id": len(notice["illustrations"]),
            "url": "",
            "copyright": "",
            "caption": "",
            "storage": ""
        })
        st.rerun()

    # Section Commentaire

    st.header("💬 Description et commentaire")
    notice["description"] = st.text_area("Description", notice.get("description", ""))
    notice["commentary"] = st.text_area("Commentaire", notice.get("commentary", ""))

    # Boutons d'action
    st.divider()
    entry_editor = st.selectbox("Auteur des modifications :",
                                load_list_form("usernames"),
                                index=index_username()
                                )
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("💾 Sauvegarder", type="primary"):
            try:
                notice["history"].append({
                    "date": datetime.now().isoformat(),
                    "type": "modified",
                    "author": entry_editor
                })
                # Nettoyage des données :
                location_type = notice["location"]["type"]
                if location_type == "unlocated" or location_type == "many_locations":
                    notice["location"].pop("institution", None)
                    notice["location"].pop("place", None)
                
                if location_type == "place":
                    notice["location"].pop("institution", None)

                if location_type == "holding_institution":
                    notice["location"].pop("place", None)

                saved_path = save_notice(notice, path=json_path, old_id=st.session_state.original_id)
                st.success(f"✅ Modifications sauvegardées dans : {saved_path}")
                st.session_state.pop("original_id", None)

            except Exception as e:
                st.error(f"❌ Erreur lors de la sauvegarde : {str(e)}")
    
    with col2:
        if st.button("🔄 Réinitialiser"):
            st.session_state.notice_data = data.copy()
            st.rerun()

    # Affichage JSON
    with st.expander("📄 Voir le JSON complet"):
        st.json(notice, expanded=False)
    
    return notice