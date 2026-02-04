import streamlit as st
import pandas as pd
from pathlib import Path
from modules.data.load import load_list_form, get_all_objects_ids_flat_sorted
from modules.edit_dataframes.load_dataframes import load_notes, save_notes

DATA_PATH_NOTES = Path("data/dataframes/notes.csv")

def notes_editor():
    st.title("📝 Éditeur de tableur – notes.csv")

    if not DATA_PATH_NOTES.exists():
        st.error(f"Fichier introuvable : {DATA_PATH_NOTES}")
        return

    df = load_notes(DATA_PATH_NOTES)

    st.subheader("Tableur éditable")
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        width='stretch',
        column_config={
        "text_xml": st.column_config.SelectboxColumn(
            "Texte XML",
            help="Choix du texte XML associé à la note",
            width=60,
                options=load_list_form("text_xml"),
            required=True,
        ),
        "oeuvre_xml_ids": st.column_config.MultiselectColumn(
            "XML ID des oeuvres",
            options=get_all_objects_ids_flat_sorted(),
            width=60),
        "note":st.column_config.Column(
            "Note",
            width=600
        )
        },
        key="notes_editor",
        hide_index=False       
    )

    col1, col2 = st.columns(2)


    with col1:
        if st.button("💾 Sauvegarder"):
            save_notes(DATA_PATH_NOTES, edited_df)
            st.success("notes.csv sauvegardé avec succès")

    with col2:
        if st.button("🔄 Recharger"):
            st.rerun()