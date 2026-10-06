import streamlit as st


def wikidata_link_for_new_id(owner_id, field_name, identifier, known_ids):
    marker_key = f"{owner_id}_{field_name}_wikidata_id"
    source_key = f"{owner_id}_{field_name}_wikidata_source"
    previous_id = st.session_state.get(marker_key)

    if previous_id and previous_id != identifier:
        st.session_state.pop(marker_key, None)
        st.session_state.pop(source_key, None)

    if identifier and identifier not in known_ids:
        st.session_state[marker_key] = identifier

    if identifier and st.session_state.get(marker_key) == identifier:
        return st.text_input(
            "Lien Wikidata (facultatif)",
            key=source_key,
            placeholder="https://www.wikidata.org/wiki/Q...",
        )

    return None


def exemple_desc_image():
    with st.expander("Voir des exemples pour les droits"):
        st.markdown("##### Wikimedia")
        st.code("Wikimedia Commons, CC BY-SA 4.0, Akinator (https://commons.wikimedia.org/wiki/File:Akinator.svg?lang=fr)", language=None)
        st.markdown("##### Gallica")
        st.code("Source gallica.bnf.fr / Bibliothèque nationale de France", language=None)
        st.markdown("##### Metropolitan Museum")
        st.code("New York, Metropolitan Museum of Arts, inv. 31.31.24 (https://www.metmuseum.org/art/collection/search/342798)", language=None)