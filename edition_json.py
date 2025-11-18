import streamlit as st
from streamlit_smart_text_input import st_smart_text_input
import json
import os
import subprocess
from datetime import datetime

data_file = 'oeuvres.json'
st.set_page_config(layout="wide")

# Charger les données
if os.path.exists(data_file):
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        oeuvres = data.get('oeuvres', [])
else:
    oeuvres = []

# Chargement des données existantes
existing_type = list({o['type_oeuvre'] for o in oeuvres})
existing_artist = list({o['artiste'] for o in oeuvres})
existing_technique  = list({o['technique'] for o in oeuvres})
existing_city = list({o['ville'] for o in oeuvres})
existing_institution = list({o['institution'] for o in oeuvres})

# Initialiser session_state pour l'édition
if 'selected_idx' not in st.session_state:
    st.session_state.selected_idx = None
if 'form_version' not in st.session_state:
    st.session_state.form_version = 0

st.title('Gestion des Œuvres')

if st.button("Git Pull"):
    try:
        result = subprocess.run(["git", "pull"], check=True, capture_output=True, text=True)
        st.success("✅ Git pull effectué avec succès !")
        st.text(result.stdout)
    except subprocess.CalledProcessError as e:
        st.error(f"⚠️ Erreur lors du git pull : {e.stderr}")

# État pour afficher ou non la zone de commit
if "show_commit_box" not in st.session_state:
    st.session_state.show_commit_box = False

# Premier bouton pour afficher la zone de commit
if st.button("Git Commit & Push"):
    st.session_state.show_commit_box = True

# Affiche la zone de commit si le bouton a été cliqué
if st.session_state.show_commit_box:
    commit_message = st.text_input(
        "Message de commit", 
        f"Update {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    if st.button("Valider Commit & Push"):
        try:
            # git add .
            subprocess.run(["git", "add", "."], check=True)
            
            # git commit -m "message"
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            
            # git push
            subprocess.run(["git", "push"], check=True)
            
            st.success("✅ Repository mis à jour et push effectué !")
            
            # Réinitialiser l'affichage de la zone de commit
            st.session_state.show_commit_box = False
            
        except subprocess.CalledProcessError as e:
            st.error(f"⚠️ Erreur lors du git operation : {e}")


col1, col2 = st.columns([1, 2])

# --- Colonne droite : cartes, modifier et supprimer ---
with col2:
    search_query = st.text_input('Rechercher dans toutes les œuvres')
    st.subheader('Œuvres enregistrées')
    filtered = []
    for idx, o in enumerate(oeuvres):
        if search_query.lower() in json.dumps(o).lower():
            filtered.append((idx, o))

    for idx, o in filtered:
        st.markdown(f"""
        <div style='border:1px solid #ddd; border-radius:10px; padding:10px; margin-bottom:10px; background:#f9f9f9'>
        <strong>{o['type_oeuvre']}</strong><br>
        <strong>{o['titre']}</strong><br>
        <em>{o['artiste']}</em><br>
        <small>{o['date']}, {o['technique']}</small><br>
        <small>{o['ville']} – {o['institution']}</small><br>
        <small>Inventaire: {o['inventaire']}</small>
        </div>
        """, unsafe_allow_html=True)
        col_btn_mod, col_btn_del = st.columns([1,1])
        with col_btn_mod:
            if st.button(f'Modifier', key=f'mod_{idx}'):
                st.session_state.selected_idx = idx
                st.session_state.form_version += 1  # Forcer la réinitialisation du formulaire
                st.rerun()
        with col_btn_del:
            if st.button(f'Supprimer', key=f'del_{idx}'):
                oeuvres.pop(idx)
                with open(data_file, 'w', encoding='utf-8') as f:
                    json.dump({'oeuvres': oeuvres}, f, ensure_ascii=False, indent=2)
                st.rerun()

# --- Colonne gauche : formulaire ---
with col1:
    if st.session_state.selected_idx is not None:
        current = oeuvres[st.session_state.selected_idx]
        st.info(f"✏️ Modification : {current['titre']}")
    else:
        current = {'id': '', 'type_oeuvre': '', 'artiste': '', 'titre': '', 'date': '', 'technique': '', 'ville': '', 'institution': '', 'inventaire': ''}

    with st.form('oeuvre_form'):
        # ID obligatoire
        id_input = st.text_input("XML:ID de l'oeuvre *", current['id'], help="Champ obligatoire")

        # Type avec autocomplétion
        if current['type_oeuvre'] and current['type_oeuvre'] not in existing_type:
            existing_type.append(current['type_oeuvre'])
        
        # Initialiser la valeur dans session_state si en mode édition
        type_key = f"type_oeuvre_smart_{st.session_state.form_version}"
        if current['type_oeuvre'] and type_key not in st.session_state:
            st.session_state[type_key] = current['type_oeuvre']
        
        type_input = st_smart_text_input(
            "Type de l'oeuvre",
            options=existing_type,
            placeholder=current['type_oeuvre'] if current['type_oeuvre'] else "Sélectionner ou saisir un type...",
            key=type_key
        )
        # Si rien n'est saisi, utiliser la valeur actuelle
        if not type_input:
            type_input = current['type_oeuvre']

        # Artiste avec autocomplétion
        if current['artiste'] and current['artiste'] not in existing_artist:
            existing_artist.append(current['artiste'])
        
        artiste_key = f"artiste_smart_{st.session_state.form_version}"
        if current['artiste'] and artiste_key not in st.session_state:
            st.session_state[artiste_key] = current['artiste']
            
        artiste_input = st_smart_text_input(
            "XML:ID de l'artiste (appuyer sur entrée!) *",
            options=existing_artist,
            placeholder=current['artiste'] if current['artiste'] else "Sélectionner ou saisir un artiste...",
            key=artiste_key
        )
        if not artiste_input:
            artiste_input = current['artiste']

        # Titre obligatoire
        titre_input = st.text_input('Titre *', current['titre'], help="Champ obligatoire")

        # Date libre
        date_input = st.text_input('Date', current['date'])

        # Technique avec autocomplétion
        if current['technique'] and current['technique'] not in existing_technique:
            existing_technique.append(current['technique'])
        
        technique_key = f"technique_smart_{st.session_state.form_version}"
        if current['technique'] and technique_key not in st.session_state:
            st.session_state[technique_key] = current['technique']
            
        technique_input = st_smart_text_input(
            "Technique",
            options=existing_technique,
            placeholder=current['technique'] if current['technique'] else "Sélectionner ou saisir une technique...",
            key=technique_key
        )
        if not technique_input:
            technique_input = current['technique']

        # Ville avec autocomplétion
        if current['ville'] and current['ville'] not in existing_city:
            existing_city.append(current['ville'])
        
        ville_key = f"ville_smart_{st.session_state.form_version}"
        if current['ville'] and ville_key not in st.session_state:
            st.session_state[ville_key] = current['ville']
            
        ville_input = st_smart_text_input(
            "Ville",
            options=existing_city,
            placeholder=current['ville'] if current['ville'] else "Sélectionner ou saisir une ville...",
            key=ville_key
        )
        if not ville_input:
            ville_input = current['ville']

        # Institution avec autocomplétion
        if current['institution'] and current['institution'] not in existing_institution:
            existing_institution.append(current['institution'])
        
        institution_key = f"institution_smart_{st.session_state.form_version}"
        if current['institution'] and institution_key not in st.session_state:
            st.session_state[institution_key] = current['institution']
            
        institution_input = st_smart_text_input(
            "Institution",
            options=existing_institution,
            placeholder=current['institution'] if current['institution'] else "Sélectionner ou saisir une institution...",
            key=institution_key
        )
        if not institution_input:
            institution_input = current['institution']

        # Inventaire reste libre
        inventaire_input = st.text_input('Inventaire', current['inventaire'])

        col_submit, col_cancel = st.columns([1, 1])
        with col_submit:
            submitted = st.form_submit_button('💾 Enregistrer')
        with col_cancel:
            cancel = st.form_submit_button('❌ Annuler')

    if cancel:
        st.session_state.selected_idx = None
        st.session_state.form_version += 1
        st.rerun()

    if submitted:
        # Validation des champs obligatoires
        errors = []
        if not id_input or id_input.strip() == '':
            errors.append("XML:ID de l'oeuvre")
        if not titre_input or titre_input.strip() == '':
            errors.append("Titre")
        if not artiste_input or artiste_input.strip() == '':
            errors.append("Artiste")
        
        if errors:
            st.error(f"❌ Champs obligatoires manquants : {', '.join(errors)}")
        else:
            new_entry = {
                'id': id_input.strip(),
                'type_oeuvre': type_input,
                'artiste': artiste_input,
                'titre': titre_input.strip(),
                'date': date_input,
                'technique': technique_input,
                'ville': ville_input,
                'institution': institution_input,
                'inventaire': inventaire_input
            }
            if st.session_state.selected_idx is None:
                oeuvres.append(new_entry)
            else:
                oeuvres[st.session_state.selected_idx] = new_entry
                st.session_state.selected_idx = None

            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump({'oeuvres': oeuvres}, f, ensure_ascii=False, indent=2)

            st.session_state.form_version += 1
            st.success('✅ Œuvre enregistrée !')
            st.rerun()

