import streamlit as st
import json
import os

from modules.data_loader import load_all_entries, delete_notice

def normalize_notice_architecture(o):
    """
    Remplace les champs vides par des chaînes 'AUCUN ...' pour que la recherche fonctionne.
    """
    # Champs principaux
    o['id'] = o.get('id') or "AUCUN ID"
    o['title'] = o.get('title') or "AUCUN TITRE"
    o['entry_type'] = o.get('entry_type') or "AUCUN TYPE"
    o['typology'] = o.get('typology') or "AUCUNE TYPOLOGIE"
    o['commentary'] = o.get('commentary') or "AUCUN COMMENTAIRE"
    
    # Date
    date = o.get('dateCreated', {})
    o['date_text'] = date.get('text') or "AUCUNE DATE"
    
    # Lieu
    location = o.get('location', {})
    o['city'] = location.get('city') or "AUCUNE VILLE"
    o['country'] = location.get('country') or "AUCUN PAYS"
    
    # Créateurs
    creators = o.get('creator', [])
    if not creators:
        o['creators_display'] = ["AUCUN CRÉATEUR"]
    else:
        display_list = []
        for c in creators:
            nom = c.get('xml_id', 'Créateur inconnu')
            role = c.get('role')
            display_list.append(f"{nom} ({role})" if role else nom)
        o['creators_display'] = display_list

    # Bibliographie
    biblio = o.get('bibliography', [])
    if not biblio:
        o['biblio_display'] = ["AUCUNE BIBLIOGRAPHIE"]
    else:
        o['biblio_display'] = [f"{b.get('zotero_key', '')} ({b.get('location', '')})" for b in biblio]

    # Illustrations
    illus = o.get('illustrations', [])
    if not illus:
        o['illustrations_display'] = ["AUCUNE ILLUSTRATION"]
    else:
        o['illustrations_display'] = [i.get('url', 'AUCUNE URL') for i in illus]

def render_search_entries_architecture():
    st.header("🔍 Recherche dans les notices d'architecture")
    
    # Charger toutes les œuvres
    oeuvres = load_all_entries("architecture")

    search_query = st.text_input("Rechercher dans toutes les œuvres", key="search_architecture")

    st.subheader("Résultats")
    filtered = []

    for idx, (o, json_path) in enumerate(oeuvres):
        normalize_notice_architecture(o)
        if search_query.lower() in json.dumps(o, ensure_ascii=False).lower():
            filtered.append((idx, o, json_path))

    if not filtered:
        st.info("Aucun résultat trouvé.")
        return

    cols = st.columns(3)

    for i, (idx, o, json_path) in enumerate(filtered):
        with cols[i % 3]:
            creators_str = " ; ".join(o.get('creators_display', []))
            biblio_str = " ; ".join(o.get('biblio_display', []))
            illustrations_list = o.get('illustrations_display', [])

            with st.container(border=True):
                # Image en haut si elle existe (première illustration)
                if illustrations_list and illustrations_list[0] != "AUCUNE ILLUSTRATION":
                    first_illustration = illustrations_list[0]
                    try:
                        st.image(first_illustration, use_container_width=True)
                    except Exception:
                        st.warning("⚠️ Image non disponible")
                
                # Type d'entrée
                st.caption(o['entry_type'])
                
                # ID
                st.markdown(f"xml:id : **{o['id']}**")

                col_mod, col_del = st.columns([1, 1])

                with col_del:
                    if st.button("Supprimer 🗑️", key=f"del_{idx}"):
                        delete_notice(json_path)
                        st.success(f"Notice déplacée dans la corbeille : {json_path}")
                        st.rerun()

                # Titre principal
                st.text(o['title'])
                
                # Créateurs en italique
                st.markdown(f"*{creators_str}*")
                
                # Informations secondaires
                st.text(f"{o['date_text']}, {o['typology']}")
                st.text(f"{o['city']} – {o['country']}")
                
                # Informations bibliographiques
                st.caption(f"📚 {biblio_str}")
                
                # Afficher toutes les illustrations
                if len(illustrations_list) > 1:
                    autres_illus = " ; ".join(illustrations_list[1:])
                    st.caption(f"🖼️ Autres illustrations : {autres_illus}")
                elif illustrations_list:
                    st.caption(f"🖼️ {illustrations_list[0]}")

                st.caption(f"📄 {os.path.basename(json_path)}")
