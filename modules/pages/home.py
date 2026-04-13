import streamlit as st

from modules.data.load import load_all_entries

def render_home():
    # Section guide rapide
    st.subheader("📌 Sections principales")
    st.markdown(
        """
        - **Ajouter une notice** : Créez une nouvelle notice pour une œuvre, que ce soit une peinture ou une architecture.
        - **Rechercher dans les notices** : Trouvez rapidement une notice existante.
        - **Gestion Git** : Téléchargez les dernières données ou envoyez vos modifications sur GitHub.
        """
    )

    st.markdown("---")

    # Section visual
    col1, col2, col3, col4 = st.columns(4)
    total_notices = len(load_all_entries("artwork")) + len(load_all_entries("building")) + len(load_all_entries("ensemble"))
    col1.metric("📄 Notices totales", f"{total_notices} notices")  # Tu peux remplacer par une fonction dynamique
    col2.metric("🖌️ Peintures", f"{len(load_all_entries('artwork'))} notices")
    col3.metric("🏛️ Architectures", f"{len(load_all_entries("building"))} notices")
    col4.metric("🌿 Ensembles", f"{len(load_all_entries('ensemble'))} notices")


    st.markdown("---")

    # Section conseils
    st.subheader("💡 Conseils d'utilisation")
    st.markdown(
        """
        - Naviguez dans le menu à gauche pour accéder aux différentes fonctionnalités.
        - Les données se sauvegardent sur Github automatiquement à chaque enregistrement. Assurez-vous de synchroniser vos données avec GitHub régulièrement.
        """
    )
