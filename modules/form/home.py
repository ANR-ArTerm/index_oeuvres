import streamlit as st

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
    col1, col2, col3 = st.columns(3)
    col1.metric("📄 Notices totales", "")  # Tu peux remplacer par une fonction dynamique
    col2.metric("🖌️ Peintures", "")
    col3.metric("🏛️ Architectures", "")

    st.markdown("---")

    # Section conseils
    st.subheader("💡 Conseils d'utilisation")
    st.markdown(
        """
        - Naviguez dans le menu à gauche pour accéder aux différentes fonctionnalités.
        - Les données se sauvegardent sur Github automatiquement à chaque enregistrement. Assurez-vous de synchroniser vos données avec GitHub régulièrement.
        """
    )
