import streamlit as st
import json
from datetime import datetime

from modules.data_loader import load_notice, save_notice, index_list_form, load_list_form, save_image


def edit_creator(creator, idx):
    """Édite un artiste"""
    st.subheader(f"Artiste {idx + 1}")
    col1, col2 = st.columns(2)
    str_creator = creator.get("xml_id", "")
    with col1:
        creator["xml_id"] = st.selectbox("Créateur de la notice :*",
                                     load_list_form("artists_names"),
                                     index=index_list_form(str_creator, "artists_names"),
                                     key=f"creator_xmlid_{idx}"
                                     )
    with col2:
        creator["role"] = st.text_input(f"Rôle", 
                                        creator.get("role", ""), 
                                        key=f"creator_role_{idx}")
    return creator

def edit_related_work(work, idx):
    """Édite une œuvre liée"""
    st.subheader(f"Œuvre liée {idx + 1}")
    col1, col2 = st.columns(2)
    with col1:
        work["link_type"] = st.text_input(f"Type de lien", 
                                          work.get("link_type", ""), 
                                          key=f"work_type_{idx}")
    with col2:
        work["xml_id_work"] = st.text_input(f"XML ID œuvre", 
                                            work.get("xml_id_work", ""), 
                                            key=f"work_xmlid_{idx}")
    return work

def edit_bibliography(biblio, idx):
    """Édite une référence bibliographique"""
    st.subheader(f"Référence {idx + 1}")
    col1, col2 = st.columns(2)
    with col1:
        biblio["zotero_key"] = st.text_input(f"Clé Zotero", biblio.get("zotero_key", ""), key=f"biblio_key_{idx}")
    with col2:
        biblio["location"] = st.text_input(f"Localisation", biblio.get("location", ""), key=f"biblio_loc_{idx}")
    return biblio

"""
def edit_illustration(illus, idx):
    
    st.subheader(f"Illustration {idx + 1}")
    illus["id"] = st.number_input(f"ID", value=illus.get("id", idx), key=f"illus_id_{idx}")
    illus["url"] = st.text_input(f"URL", illus.get("url", ""), key=f"illus_url_{idx}")
    illus["copyright"] = st.text_input(f"Copyright", illus.get("copyright", ""), key=f"illus_copyright_{idx}")
    illus["caption"] = st.text_area(f"Légende", illus.get("caption", ""), key=f"illus_caption_{idx}")
    illus["storage"] = st.text_input(f"Stockage", illus.get("storage", ""), key=f"illus_storage_{idx}")
    return illus
"""

def edit_illustration(illus, idx):
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
        if st.button("➕ URL", key=f"edit_url_btn_{idx}"):
            st.session_state.type_illustration_edit[idx] = "URL"
            st.session_state.show_image_edit[idx] = False

        if st.button("📁 Local", key=f"edit_local_btn_{idx}"):
            st.session_state.type_illustration_edit[idx] = "local"
            st.session_state.show_image_edit[idx] = False


    # --- Champs selon le mode ---
    with colB:
        illus_id = st.number_input("ID", value=illus.get("id", idx), key=f"edit_illus_id_{idx}")
        illus["id"] = illus_id

        mode = st.session_state.type_illustration_edit[idx]

        # ---- MODE URL ----
        if mode == "URL":
            col_url, col_btn = st.columns([5,1])
            with col_url:
                url = st.text_input("URL", illus.get("url", ""), key=f"edit_illus_url_{idx}")
            with col_btn:
                if st.button("Voir", key=f"edit_show_url_{idx}"):
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
                    key=f"edit_upload_{idx}"
                )
            with col_btn:
                if st.button("Voir/Sauvegarder", key=f"edit_show_local_{idx}"):
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
            key=f"edit_illus_copyright_{idx}"
        )

        illus["caption"] = st.text_input(
            "Légende",
            illus.get("caption", ""),
            key=f"edit_illus_caption_{idx}"
        )


    # --- Prévisualisation ---
    with colPreview:
        if st.session_state.show_image_edit[idx] and illus.get("url"):
            try:
                st.image(illus["url"], caption="Prévisualisation")
            except Exception:
                st.warning("Impossible d'afficher l'image.")


    return illus

def edit_history_entry(entry, idx):
    """Édite une entrée d'historique"""
    st.subheader(f"Historique {idx + 1}")
    col1, col2, col3 = st.columns(3)
    with col1:
        entry["date"] = st.text_input(f"Date", entry.get("date", ""), key=f"hist_date_{idx}")
    with col2:
        entry["type"] = st.selectbox(f"Type", ["created", "modified", "deleted"], 
                                     index=["created", "modified", "deleted"].index(entry.get("type", "modified")) 
                                     if entry.get("type") in ["created", "modified", "deleted"] else 1,
                                     key=f"hist_type_{idx}")
    with col3:
        entry["author"] = st.text_input(f"Auteur", entry.get("author", ""), key=f"hist_author_{idx}")
    return entry

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
    
    # Section Informations générales
    st.header("📋 Informations générales")
    col1, col2 = st.columns(2)
    with col1:
        notice["id"] = st.text_input("ID", notice.get("id", ""))
        notice["QID_wikidata"] = st.text_input("QID Wikidata", notice.get("QID_wikidata", ""))
    with col2:
        notice["entry_type"] = st.selectbox("Type d'entrée", 
                                            ["architecture", "art", "document", "autre"],
                                            index=["architecture", "art", "document", "autre"].index(notice.get("entry_type", "architecture"))
                                            if notice.get("entry_type") in ["architecture", "art", "document", "autre"] else 0)
        notice["typology"] = st.text_input("Typologie", notice.get("typology", ""))
    
    notice["title"] = st.text_input("Titre", notice.get("title", ""))
    
    # Section Créateurs
    st.header("👥 Créateurs")
    if "creator" not in notice or not isinstance(notice["creator"], list):
        notice["creator"] = []
    
    for idx, creator in enumerate(notice["creator"]):
        notice["creator"][idx] = edit_creator(creator, idx)
        if st.button(f"Supprimer créateur {idx + 1}", key=f"del_creator_{idx}"):
            notice["creator"].pop(idx)
            st.rerun()
    
    if st.button("➕ Ajouter un créateur"):
        notice["creator"].append({"xml_id": "", "role": ""})
        st.rerun()
    
    # Section Date de création
    st.header("📅 Date de création")
    if "dateCreated" not in notice:
        notice["dateCreated"] = {}
    
    col1, col2, col3 = st.columns(3)
    with col1:
        notice["dateCreated"]["startYear"] = st.text_input("Année de début", 
                                                            notice["dateCreated"].get("startYear", ""))
    with col2:
        notice["dateCreated"]["endYear"] = st.text_input("Année de fin", 
                                                          notice["dateCreated"].get("endYear", ""))
    with col3:
        notice["dateCreated"]["text"] = st.text_input("Texte date", 
                                                       notice["dateCreated"].get("text", ""))
    
    # Section Localisation
    st.header("📍 Localisation")
    if "location" not in notice:
        notice["location"] = {"coordinates": {}}
    
    col1, col2 = st.columns(2)
    with col1:
        notice["location"]["city"] = st.text_input("Ville", notice["location"].get("city", ""))
        notice["location"]["country"] = st.text_input("Pays", notice["location"].get("country", ""))
    with col2:
        if "coordinates" not in notice["location"]:
            notice["location"]["coordinates"] = {}
        notice["location"]["coordinates"]["latitude"] = st.text_input("Latitude", 
                                                                       notice["location"]["coordinates"].get("latitude", ""))
        notice["location"]["coordinates"]["longitude"] = st.text_input("Longitude", 
                                                                        notice["location"]["coordinates"].get("longitude", ""))
    
    # Section Œuvres liées
    st.header("🔗 Œuvres liées")
    if "related_works" not in notice or not isinstance(notice["related_works"], list):
        notice["related_works"] = []
    
    for idx, work in enumerate(notice["related_works"]):
        notice["related_works"][idx] = edit_related_work(work, idx)
        if st.button(f"Supprimer œuvre {idx + 1}", key=f"del_work_{idx}"):
            notice["related_works"].pop(idx)
            st.rerun()
    
    if st.button("➕ Ajouter une œuvre liée"):
        notice["related_works"].append({"link_type": "", "xml_id_work": ""})
        st.rerun()
    
    # Section Bibliographie
    st.header("📚 Bibliographie")
    if "bibliography" not in notice or not isinstance(notice["bibliography"], list):
        notice["bibliography"] = []
    
    for idx, biblio in enumerate(notice["bibliography"]):
        notice["bibliography"][idx] = edit_bibliography(biblio, idx)
        if st.button(f"Supprimer référence {idx + 1}", key=f"del_biblio_{idx}"):
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
        notice["illustrations"][idx] = edit_illustration(illus, idx)
        if st.button(f"Supprimer illustration {idx + 1}", key=f"del_illus_{idx}"):
            notice["illustrations"].pop(idx)
            st.rerun()
    
    if st.button("➕ Ajouter une illustration"):
        notice["illustrations"].append({"id": len(notice["illustrations"]), "url": "", 
                                        "copyright": "", "caption": "", "storage": ""})
        st.rerun()
    
    # Section Commentaire
    st.header("💬 Commentaire")
    notice["commentary"] = st.text_area("Commentaire", notice.get("commentary", ""), height=150)
    
    """
    # Section Historique
    st.header("📜 Historique")
    if "history" not in notice or not isinstance(notice["history"], list):
        notice["history"] = []
    
    for idx, entry in enumerate(notice["history"]):
        notice["history"][idx] = edit_history_entry(entry, idx)
        if st.button(f"Supprimer entrée {idx + 1}", key=f"del_hist_{idx}"):
            notice["history"].pop(idx)
            st.rerun()
    
    if st.button("➕ Ajouter une entrée historique"):
        notice["history"].append({"date": datetime.now().isoformat(), "type": "modified", "author": ""})
        st.rerun()
    """
    
    # Boutons d'action
    st.divider()
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("💾 Sauvegarder", type="primary"):
            try:
                # Utilise votre fonction save_notice qui gère automatiquement le chemin
                saved_path = save_notice(notice, path=json_path)
                st.success(f"✅ Modifications sauvegardées dans : {saved_path}")
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
