import streamlit as st
import json

from modules.data.load import load_all_notices, delete_notice

def display_value(val, label_if_empty=None):
    """
    Retourne la valeur si elle existe, sinon un texte indiquant ce qui manque.
    label_if_empty : chaîne affichée si val est vide (ex: "AUCUN LIEU")
    """
    if val:
        return val
    elif label_if_empty:
        return f"<span style='color:red;'>{label_if_empty}</span>"
    else:
        return "—"

def normalize_notice(o):
    """
    Remplace les champs vides par des chaînes 'AUCUN ...' pour que la recherche fonctionne.
    """
    # Champs simples
    o['type_oeuvre'] = o.get('type_oeuvre') or "AUCUN TYPE"
    o['titre'] = o.get('titre') or "AUCUN TITRE"
    o['date'] = o.get('date') or "AUCUNE DATE"
    o['technique'] = o.get('technique') or "AUCUNE TECHNIQUE"
    o['ville'] = o.get('ville') or "AUCUN LIEU DE CONSERVATION"
    o['institution'] = o.get('institution') or "AUCUNE INSTITUTION DE CONSERVATION"
    o['inventaire'] = o.get('inventaire') or "AUCUN NUMÉRO D’INVENTAIRE"

    # Artistes
    artistes = o.get("artistes", [])
    if not artistes:
        o['artistes_display'] = ["AUCUN ARTISTE"]
    else:
        display_list = []
        for a in artistes:
            if isinstance(a, dict):
                nom = a.get("xml:id", "Artiste inconnu")
                role = a.get("role")
                display_list.append(f"{nom} ({role})" if role else nom)
            elif isinstance(a, str):
                display_list.append(a)
        o['artistes_display'] = display_list

def render_search_notices():
    st.header("🔍 Recherche dans les notices")
    
    # Charger toutes les œuvres
    oeuvres, filenames, *rest = load_all_notices()

    search_query = st.text_input("Rechercher dans toutes les œuvres")

    st.subheader("Résultats")
    filtered = []

    # Préparer les résultats filtrés
    for idx, o in enumerate(oeuvres):
        normalize_notice(o)
        if search_query.lower() in json.dumps(o, ensure_ascii=False).lower():
            filtered.append((idx, o, filenames[idx]))

    # Affichage des cartes
    cols = st.columns(3)

    for i, (idx, o, path) in enumerate(filtered):

        with cols[i % 3]:

            artistes_display = []
            artistes = o.get("artistes", [])

            for a in artistes:
                if isinstance(a, dict):
                    nom = a.get("xml:id", "Artiste inconnu")
                    role = a.get("role")
                    if role:
                        artistes_display.append(f"{nom} ({role})")
                    else:
                        artistes_display.append(nom)
                elif isinstance(a, str):
                    artistes_display.append(a)

            # Séparer les artistes par un point-virgule
            artistes_display_str = " ; ".join(artistes_display) if artistes_display else "<span style='color:red;'>AUCUN</span>"

            st.markdown(
                f"""
                <div style='border:1px solid #ddd; border-radius:10px; padding:10px;
                    margin-bottom:10px; background:#fafafa; min-height:220px'>
                    <strong>{o['type_oeuvre'].replace('AUCUN', '<span style="color:red;">AUCUN</span>')}</strong><br>
                    <strong>{o['titre'].replace('AUCUN', '<span style="color:red;">AUCUN</span>')}</strong><br>
                    <em>{artistes_display_str}</em><br>
                    <small>{o['date'].replace('AUCUN', '<span style="color:red;">AUCUN</span>')}, {o['technique'].replace('AUCUN', '<span style="color:red;">AUCUN</span>')}</small><br>
                    <small>{o['ville'].replace('AUCUN', '<span style="color:red;">AUCUN</span>')} – {o['institution'].replace('AUCUN', '<span style="color:red;">AUCUN</span>')}</small><br>
                    <small>Inventaire : {o['inventaire'].replace('AUCUN', '<span style="color:red;">AUCUN</span>')}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )



            # Modifier / Supprimer
            col_mod, col_del = st.columns([1, 1])

            with col_mod:
                if st.button("✏️ Modifier", key=f"mod_{idx}"):
                    st.session_state.selected_idx = idx
                    st.session_state.selected_path = path
                    st.session_state.form_version += 1
                    st.rerun()

            with col_del:
                if st.button("Supprimer 🗑️", key=f"del_{idx}"):
                    delete_notice(path)
                    st.success(f"Notice supprimée : {path}")
                    st.rerun()
