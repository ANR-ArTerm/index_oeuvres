import streamlit as st
import pandas as pd
from pathlib import Path
from modules.data.load import load_list_form, get_all_objects_ids_flat_sorted

DATA_PATH = Path("data/notes_csv/notes.csv")

def load_notes():
    return pd.read_csv(DATA_PATH, sep=";", header=0)

def save_notes(df: pd.DataFrame):
    df.to_csv(DATA_PATH, sep=";", index=False)

def notes_editor():
    st.title("📝 Éditeur de tableur – notes.csv")

    if not DATA_PATH.exists():
        st.error(f"Fichier introuvable : {DATA_PATH}")
        return

    df = load_notes()

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
            save_notes(edited_df)
            st.success("notes.csv sauvegardé avec succès")

    with col2:
        if st.button("🔄 Recharger"):
            st.rerun()