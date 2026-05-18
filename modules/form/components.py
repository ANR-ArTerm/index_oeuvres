import streamlit as st

def exemple_desc_image():
    with st.expander("Voir des exemples pour les droits"):
        st.markdown("##### Wikimedia")
        st.code("Wikimedia Commons, CC BY-SA 4.0, Akinator (https://commons.wikimedia.org/wiki/File:Akinator.svg?lang=fr)", language=None)
        st.markdown("##### Gallica")
        st.code("Source gallica.bnf.fr / Bibliothèque nationale de France", language=None)
        st.markdown("##### Metropolitan Museum")
        st.code("New York, Metropolitan Museum of Arts, inv. 31.31.24 (https://www.metmuseum.org/art/collection/search/342798)", language=None)