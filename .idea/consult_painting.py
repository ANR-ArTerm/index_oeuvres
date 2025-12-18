import streamlit as st
import json
from datetime import datetime

from modules.data_loader import load_notice, save_notice, index_list_form, load_list_form

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
        notice["entry_type"] = st.selectbox(
            "Type d'entrée", 
            ["architecture", "art", "document", "peinture", "autre"],
            index=["architecture", "art", "document", "peinture", "autre"].index(
                notice.get("entry_type", "architecture")
            )
        )
        
    notice["title"] = st.text_input("Titre", notice.get("title", ""))

    # ╔═══════════════════════════════════════════╗
    #            SECTIONS SPÉCIFIQUES TYPE
    # ╚═══════════════════════════════════════════╝

    # — PEINTURE —
    if notice["entry_type"] == "peinture":
        st.header("🎨 Matériaux & Techniques")
        notice["materialsAndTechniques"] = st.text_input(
            "Matériaux et techniques", 
            notice.get("materialsAndTechniques", "")
        )

        st.header("🏛️ Institution détentrice")
        if "holding_institution" not in notice:
            notice["holding_institution"] = {}

        col1, col2 = st.columns(2)
        with col1:
            notice["holding_institution"]["name"] = st.text_input(
                "Institution", 
                notice["holding_institution"].get("name", "")
            )
            notice["holding_institution"]["place"] = st.text_input(
                "Lieu", 
                notice["holding_institution"].get("place", "")
            )
        with col2:
            notice["holding_institution"]["inventory_number"] = st.text_input(
                "Numéro d'inventaire", 
                notice["holding_institution"].get("inventory_number", "")
            )
            notice["holding_institution"]["URL"] = st.text_input(
                "URL institution", 
                notice["holding_institution"].get("URL", "")
            )

    if notice["entry_type"] == "architecture": 
        notice["typology"] = st.text_input("Typologie", notice.get("typology", ""))


    # ╔═══════════════════════════════════════════╗
    #               PARTIE COMMUNE
    # ╚═══════════════════════════════════════════╝

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
        notice["illustrations"].append({
            "id": len(notice["illustrations"]),
            "url": "",
            "copyright": "",
            "caption": "",
            "storage": ""
        })
        st.rerun()

    # Section Commentaire
    st.header("💬 Commentaire")
    notice["commentary"] = st.text_area("Commentaire", notice.get("commentary", ""), height=150)

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
        notice["history"].append({
            "date": datetime.now().isoformat(),
            "type": "modified",
            "author": ""
        })
        st.rerun()

    # Boutons d'action
    st.divider()
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("💾 Sauvegarder", type="primary"):
            try:
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
