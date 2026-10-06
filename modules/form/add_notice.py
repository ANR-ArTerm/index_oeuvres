"""Page Streamlit « Ajouter une notice ».

Crée une notice (œuvre, architecture ou ensemble) sous forme de JSON, l'enregistre
puis la pousse sur GitHub.

Organisation du fichier :
    1. Constantes
    2. Petits utilitaires (ids stables, nettoyage, sauvegarde dans les listes)
    3. Wikidata : cooldown 429, requête (mise en cache), préremplissage
    4. Formulaires élémentaires (créateur, lien entre œuvres, référence, illustration)
    5. Sections de la page (une fonction par section)
    6. Sauvegarde et point d'entrée `add_notice()`

Principes appliqués :
    - Chaque élément d'une liste (créateur, lien, référence, illustration) porte un
      identifiant stable `_uid`. Les clés de widgets l'utilisent à la place de l'index,
      ce qui évite les valeurs décalées après une suppression.
    - Toute clé commençant par « _ » est un état d'interface : elle n'est jamais
      enregistrée (voir `_public`).
    - Les clés de widgets sont préfixées par l'XML:ID (et le type de notice quand les
      options en dépendent) pour ne rien garder d'une notice à l'autre.
"""

import re
import time
import uuid
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.error import HTTPError

import requests
import streamlit as st

from modules.data.load import (
    exist_notice,
    get_all_objects_ids_flat_sorted,
    index_username,
    load_list_form,
    save_image,
    save_notice,
    save_person_wikidata,
    save_place_wikidata,
    save_to_list_form_git,
)
from modules.form.components import exemple_desc_image, wikidata_link_for_new_id
from modules.git_tools import git_commit_and_push
from modules.status_entry import STATUS_ENTRY_OPTIONS
from modules.wikidata.artwork_queries import get_artwork_data, match_existing_label
from modules.wikidata.matching_data import wikidata_to_xml_ids_or_qid
from modules.wikidata.queries import get_monument_data


# =============================================================================
# 1. CONSTANTES
# =============================================================================

XML_ID_KEY = "add_notice_xml_id"  # clé du champ XML:ID (réinitialisé après sauvegarde)
XML_ID_PATTERN = re.compile(r"[A-Za-z0-9]+")  # ni accent, ni espace, ni caractère spécial

ENTRY_TYPES = {
    "🖼️ Œuvre": "artwork",
    "🏛️ Architecture": "building",
    "🌿 Ensemble": "ensemble",
}

# type de notice -> (liste des typologies, titre de section, libellé du champ)
TYPOLOGIES = {
    "artwork": ("typologies_artwork", "🎲 Typologie d'œuvre", "Typologie d'œuvre"),
    "building": ("typologies_architecture", "Typologie de monument", "Typologie d'architecture"),
    "ensemble": ("typologies_ensemble", "Typologie d'ensemble", "Typologie d'ensemble"),
}

# type de notice -> listes de rôles proposées (la première reçoit les nouveaux rôles)
ROLE_LISTS = {
    "artwork": ("artists_roles",),
    "building": ("architects_roles",),
    "ensemble": ("artists_roles", "architects_roles"),
}

LOCATION_TYPES = {
    "🏛️ Institution de conservation (musée, église)": "holding_institution",
    "📍 Localisation (pour les bâtiments)": "place",
    "Non localisée": "unlocated",
    "Plusieurs localisations": "multiple_locations",
}
DEFAULT_LOCATION_TYPE = {
    "artwork": "holding_institution",
    "building": "place",
    "ensemble": "holding_institution",
}


# =============================================================================
# 2. UTILITAIRES
# =============================================================================

def _new_item(**fields) -> dict:
    """Crée un élément de liste avec un identifiant stable `_uid`."""
    return {"_uid": uuid.uuid4().hex[:8], **fields}


def _ensure_uid(item: dict) -> dict:
    """Ajoute un `_uid` aux éléments créés ailleurs (ex. préremplis par Wikidata)."""
    item.setdefault("_uid", uuid.uuid4().hex[:8])
    return item


def _public(item: dict, exclude=()) -> dict:
    """Retire les clés d'interface (préfixe « _ ») et celles de `exclude`."""
    return {k: v for k, v in item.items() if not k.startswith("_") and k not in exclude}


def _save_if_new(list_key, value, known=None, saving_msg="Sauvegarde de la nouvelle valeur"):
    """Ajoute `value` à la liste de formulaire `list_key` si elle n'y figure pas encore.

    `known` permet de réutiliser une liste déjà chargée (évite un second appel à
    `load_list_form`). Affiche le message de succès ou d'erreur de la sauvegarde git.
    """
    known = load_list_form(list_key) if known is None else known
    if not value or value in known:
        return
    with st.spinner(saving_msg):
        success, message = save_to_list_form_git(list_key, value)
    (st.success if success else st.error)(message)


def _edit_list(items, render, delete_label, key_prefix):
    """Affiche une liste éditable : un formulaire + un bouton « Supprimer » par élément.

    `render(item, idx)` modifie l'élément en place. Le bouton de suppression utilise
    le `_uid` de l'élément, pas son index, pour rester stable.
    """
    for idx, item in enumerate(items):
        _ensure_uid(item)
        render(item, idx)
        if st.button(f"{delete_label} {idx + 1}", key=f"{key_prefix}_del_{item['_uid']}"):
            items.pop(idx)
            st.rerun()


def init_empty_notice(xml_id, entry_type):
    return {
        "id": xml_id,
        "QID_wikidata": "",
        "entry_type": entry_type,
        "title": "",
        "creator": [],
        "dateCreated": {"startYear": None, "endYear": None, "text": ""},
        "location": "",
        "related_works": [],
        "bibliography": [],
        "illustrations": [],
        "description": "",
        "commentary": "",
        "history": [],
        "status_entry": 0,
    }


# =============================================================================
# 3. WIKIDATA
# =============================================================================

# --- 3.1 Cooldown après une erreur 429 --------------------------------------

@st.cache_resource
def _wikidata_cooldown_state():
    """État partagé par tous les utilisateurs de l'app (la limite 429 vaut pour l'IP)."""
    return {"retry_at": 0.0}


@st.fragment(run_every="1s")
def _render_wikidata_retry_timer():
    """Compte à rebours rafraîchi chaque seconde, sans relancer toute la page."""
    cooldown = _wikidata_cooldown_state()
    remaining = max(0, int(cooldown["retry_at"] - time.time() + 0.999))
    if remaining:
        st.warning(
            f"Attendre {remaining // 60:02d}:{remaining % 60:02d} "
            "avant de relancer la requête Wikidata."
        )
    else:
        cooldown["retry_at"] = 0.0
        st.success("Vous pouvez relancer la recherche Wikidata.")


def _http_status(error):
    """Renvoie (code, en-têtes) pour les deux familles d'exceptions HTTP.

    - `requests.HTTPError` (artwork_queries.py) : `.response.status_code`
    - `urllib.error.HTTPError` (SPARQLWrapper, donc queries.py) : `.code`
    """
    response = getattr(error, "response", None)
    if response is not None:
        return response.status_code, response.headers
    return getattr(error, "code", None), getattr(error, "headers", None)


def _retry_delay(headers) -> float:
    """Délai d'attente (s) demandé par l'en-tête Retry-After (secondes ou date HTTP)."""
    value = headers.get("Retry-After") if headers else None
    if value is None:
        return 60
    try:
        return float(value)
    except ValueError:
        pass
    try:
        return parsedate_to_datetime(value).timestamp() - time.time()
    except (TypeError, ValueError, OverflowError):
        return 60


def _start_wikidata_cooldown(headers) -> None:
    cooldown = _wikidata_cooldown_state()
    cooldown["retry_at"] = max(
        cooldown["retry_at"], time.time() + max(1, _retry_delay(headers))
    )


# --- 3.2 Requête (mise en cache) ---------------------------------------------

@st.cache_data(ttl=3600, show_spinner="Interrogation de Wikidata…")
def _fetch_wikidata(entry_type: str, qid: str) -> dict:
    """Interroge Wikidata. Les résultats sont gardés 1 h : relancer la même recherche
    ne coûte aucune requête (utile avec la limite 429). Les exceptions ne sont pas
    mises en cache."""
    fetch = get_artwork_data if entry_type == "artwork" else get_monument_data
    return fetch(qid)


# --- 3.3 Préremplissage : œuvre ---------------------------------------------

def _prefill_title_and_date(xml_id, notice, data):
    """Titre et date : on ne remplit que les champs encore vides."""
    if data["title"] and not (notice.get("title") or "").strip():
        notice["title"] = data["title"]
        st.session_state[f"{xml_id}_title"] = data["title"]

    year = data["year"]
    if year is None:
        return
    date = notice.setdefault("dateCreated", {})
    # (champ de la notice, suffixe de la clé du widget, valeur)
    for field, key_suffix, value in (
        ("startYear", "start_year", year),
        ("endYear", "end_year", year),
        ("text", "date_text", str(year)),
    ):
        if date.get(field) in (None, ""):
            date[field] = value
            st.session_state[f"{xml_id}_{key_suffix}"] = value


def _prefill_creators(xml_id, notice, data):
    """Ajoute les créateurs Wikidata déjà connus dans la liste des personnes."""
    persons = load_list_form("persons")
    creator_ids = wikidata_to_xml_ids_or_qid(data["creator_qids"], key="people")
    labels = data["creator_labels"]
    if len(creator_ids) != len(labels):  # garde-fou : zip() décalerait les noms
        labels = creator_ids

    entries = notice.setdefault("creator", [])
    already_selected = {c.get("xml_id") for c in entries if c.get("xml_id")}
    missing = []

    for creator_id, label in zip(creator_ids, labels):
        if creator_id not in persons:
            missing.append(label)
            continue
        if creator_id in already_selected:
            continue

        # On réutilise une ligne vide si elle existe, sinon on en crée une.
        entry = next((c for c in entries if not c.get("xml_id")), None)
        if entry is None:
            entry = _new_item(xml_id="", role="")
            entries.append(entry)
        _ensure_uid(entry)
        entry["xml_id"] = creator_id
        entry.setdefault("role", "")
        st.session_state[f"{xml_id}_creator_xmlid_{entry['_uid']}"] = creator_id
        already_selected.add(creator_id)

    if missing:
        names = ", ".join(dict.fromkeys(missing))
        st.warning(
            "Ces artistes Wikidata ne sont pas encore dans la liste des artistes : "
            f"{names}. Ajoutez-les à la liste pour pouvoir les associer à la notice."
        )


def _prefill_institution(xml_id, notice, data):
    """Institution de conservation : première correspondance exacte avec la liste locale."""
    location = notice.get("location")
    if not isinstance(location, dict):
        location = {}
    institution = location.get("institution", {})
    location_type = location.get("type") or "holding_institution"
    if location_type != "holding_institution" or institution.get("name"):
        return

    known = load_list_form("institutions")
    name = next(
        (
            match
            for label in data["institutions"]
            if (match := match_existing_label(label, known))
        ),
        None,
    )
    if name:
        institution["name"] = name
        location["type"] = "holding_institution"
        location["institution"] = institution
        notice["location"] = location
        st.session_state[f"{xml_id}_institution"] = name


def _prefill_images(notice, data):
    """Ajoute les images Wikimedia Commons non déjà présentes (dédoublonnées par URL)."""
    illustrations = notice.setdefault("illustrations", [])
    known_urls = {item.get("url") for item in illustrations}
    for image in data["images"]:
        if image["url"] in known_urls:
            continue
        illustrations.append(_new_item(
            id=len(illustrations),
            url=image["url"],
            storage="online",
            copyright=image["copyright"],
            caption="",
        ))
        known_urls.add(image["url"])


def _apply_artwork_data(xml_id, notice, data):
    _prefill_title_and_date(xml_id, notice, data)
    _prefill_creators(xml_id, notice, data)
    _prefill_institution(xml_id, notice, data)
    _prefill_images(notice, data)


# --- 3.4 Préremplissage : bâtiment ------------------------------------------

def _apply_building_data(xml_id, notice, data):
    """Ville, pays (si connus dans la liste des lieux) et coordonnées."""
    location = notice.get("location")
    if not isinstance(location, dict):
        location = {"type": "place", "place": {}}
    elif not location.get("type"):
        location["type"] = "place"
    if location["type"] != "place":
        return  # l'utilisateur a choisi un autre type de localisation : on ne touche à rien

    place_ids = load_list_form("places")
    place = location.setdefault("place", {})
    unmatched = []

    # (champ Wikidata = champ de la notice, suffixe de la clé du widget)
    for field, key_suffix in (("city", "place_city"), ("country", "place_country")):
        label = data.get(field)
        if not label:
            continue
        known_place = match_existing_label(label, place_ids)
        if not known_place:
            unmatched.append(label)
        elif not place.get(field):
            place[field] = known_place
            st.session_state[f"{xml_id}_{key_suffix}"] = known_place

    coordinates = place.setdefault("coordinates", {})
    for field in ("latitude", "longitude"):
        if data.get(field) is not None and coordinates.get(field) in (None, ""):
            coordinates[field] = data[field]  # on garde un nombre, pas une chaîne
    notice["location"] = location

    if unmatched:
        names = ", ".join(dict.fromkeys(unmatched))
        st.warning(
            "Ces lieux Wikidata ne sont pas encore dans la liste des lieux : "
            f"{names}. Créez-les dans le sélecteur Ville/Pays."
        )


# --- 3.5 Bouton « Recherche Wikidata » --------------------------------------

def _run_wikidata_search(notice, entry_type, xml_id):
    qid = (notice.get("QID_wikidata") or "").strip()
    if not qid:
        st.warning("Veuillez entrer un QID.")
        return
    if entry_type == "ensemble":
        st.warning("La fonction n'existe pas encore")
        return

    try:
        data = _fetch_wikidata(entry_type, qid)
    except (HTTPError, requests.HTTPError) as error:
        status, headers = _http_status(error)
        if status == 429:
            _start_wikidata_cooldown(headers)
            st.error("Wikidata limite temporairement les requêtes.")
            _render_wikidata_retry_timer()
        else:
            st.error(f"Erreur lors de la recherche Wikidata : {error}")
        return
    except Exception as error:  # réseau, QID inexistant, réponse inattendue...
        st.error(f"Erreur lors de la recherche Wikidata : {error}")
        return

    if entry_type == "artwork":
        _apply_artwork_data(xml_id, notice, data)
    else:
        _apply_building_data(xml_id, notice, data)
    st.success("Informations Wikidata récupérées.")


# =============================================================================
# 4. FORMULAIRES ÉLÉMENTAIRES
# =============================================================================

def _creator_form(xml_id, creator, idx, entry_type):
    """Un créateur : identifiant de la personne + rôle (+ lien Wikidata si personne nouvelle)."""
    uid = creator["_uid"]
    st.subheader(f"Artiste {idx + 1}")
    col_person, col_role = st.columns(2)

    with col_person:
        person_ids = load_list_form("persons")
        selected = st.selectbox(
            "Artiste :*",
            person_ids,
            accept_new_options=True,
            index=None,
            key=f"{xml_id}_creator_xmlid_{uid}",
        )
        creator["xml_id"] = selected

        # Si la personne change, le lien Wikidata saisi pour la précédente n'a plus de sens.
        previous = creator.get("_wikidata_person_id")
        if previous and previous != selected:
            creator.pop("wikidata", None)
            creator.pop("_wikidata_person_id", None)

        # Personne absente de la liste : on l'ajoute et on propose un lien Wikidata.
        if selected and selected not in person_ids:
            creator["_wikidata_person_id"] = selected
            _save_if_new("persons", selected, person_ids, "Sauvegarde du nouvel identifiant")

        if selected and creator.get("_wikidata_person_id") == selected:
            creator["wikidata"] = st.text_input(
                "Lien Wikidata (facultatif)",
                value=creator.get("wikidata", ""),
                key=f"{xml_id}_creator_wikidata_{uid}",
                placeholder="https://www.wikidata.org/wiki/Q...",
            )

    with col_role:
        role_lists = ROLE_LISTS[entry_type]
        options = load_list_form(*role_lists)
        creator["role"] = st.selectbox(
            "Rôle :",
            options,
            index=None,
            accept_new_options=True,  # aussi pour les ensembles (le code de sauvegarde existait déjà)
            key=f"{xml_id}_creator_role_{uid}",
        )
        _save_if_new(role_lists[0], creator["role"], options, "Sauvegarde du nouveau rôle")


def _work_link_form(xml_id, work, idx, xml_ids, title, link_types_key, key_prefix):
    """Un lien vers une autre notice : type de lien + XML:ID de l'œuvre liée."""
    uid = work["_uid"]
    st.subheader(f"{title} {idx + 1}")
    col_type, col_work = st.columns(2)

    with col_type:
        link_types = load_list_form(link_types_key)
        work["link_type"] = st.selectbox(
            "Type de lien",
            link_types,
            key=f"{xml_id}_{key_prefix}_type_{uid}",
            index=None,
            accept_new_options=True,
        )
        _save_if_new(link_types_key, work["link_type"], link_types,
                     "Sauvegarde du nouveau type de lien")

    with col_work:
        work["xml_id_work"] = st.selectbox(
            f"XML:id de l'oeuvre liée {idx + 1}",
            xml_ids,
            index=None,
            key=f"{xml_id}_{key_prefix}_xmlid_{uid}",
        )


def _work_links_editor(xml_id, works, xml_ids, title, link_types_key, key_prefix, add_label):
    """Liste éditable de liens (œuvres liées ou œuvres contenues dans l'ensemble)."""
    _edit_list(
        works,
        lambda work, idx: _work_link_form(
            xml_id, work, idx, xml_ids, title, link_types_key, key_prefix
        ),
        "Supprimer œuvre",
        f"{xml_id}_{key_prefix}",
    )
    if st.button(add_label, key=f"{xml_id}_add_{key_prefix}"):
        works.append(_new_item(link_type="", xml_id_work=""))
        st.rerun()


def _bibliography_form(xml_id, ref, idx, zotero_list):
    """Une référence bibliographique : clé Zotero + localisation dans l'ouvrage."""
    uid = ref["_uid"]
    st.subheader(f"Référence {idx + 1}")
    col_key, col_location = st.columns(2)

    with col_key:
        current = ref.get("zotero_key")
        ref["zotero_key"] = st.selectbox(
            "Clé Zotero",
            zotero_list,
            key=f"{xml_id}_biblio_key_{uid}",
            index=zotero_list.index(current) if current in zotero_list else None,
            accept_new_options=True,
        )
        _save_if_new("zotero_keys", ref["zotero_key"], zotero_list,
                     "Sauvegarde de l'entrée bibliographique")

    with col_location:
        ref["location"] = st.text_input(
            "Localisation",
            ref.get("location", ""),
            key=f"{xml_id}_biblio_loc_{uid}",
        )


def _illustration_form(xml_id, illus, idx):
    """Une illustration, en ligne (URL) ou téléversée (local).

    État d'interface stocké dans l'illustration elle-même (jamais enregistré) :
        _mode : "URL", "local" ou None      _show : afficher l'aperçu ou non
    """
    uid = illus["_uid"]
    illus["id"] = idx  # l'id est la position ; il est de toute façon renumeroté à l'enregistrement

    if "_mode" not in illus:  # déduit du stockage pour les illustrations préremplies
        illus["_mode"] = {"online": "URL", "local": "local"}.get(illus.get("storage"))
    illus.setdefault("_show", False)

    st.markdown(f"### Illustration {idx + 1}")
    st.caption(f"ID : {idx}")
    col_mode, col_fields, col_preview = st.columns([1, 6, 4])

    # --- Choix du mode ---
    with col_mode:
        if st.button("➕ URL", key=f"{xml_id}_illus_url_btn_{uid}"):
            illus["_mode"], illus["_show"] = "URL", False
        if st.button("📁 Local", key=f"{xml_id}_illus_local_btn_{uid}"):
            illus["_mode"], illus["_show"] = "local", False

    # --- Champs selon le mode ---
    with col_fields:
        if illus["_mode"] == "URL":
            col_url, col_btn = st.columns([5, 1])
            illus["storage"] = "online"
            illus["url"] = col_url.text_input(
                "URL", illus.get("url", ""), key=f"{xml_id}_illus_url_{uid}"
            )
            if col_btn.button("Voir", key=f"{xml_id}_illus_show_url_{uid}"):
                illus["_show"] = True

        elif illus["_mode"] == "local":
            col_upload, col_btn = st.columns([5, 1])
            illus["storage"] = "local"
            uploaded = col_upload.file_uploader(
                "Fichier (jpg/png)",
                type=["jpg", "jpeg", "png"],
                key=f"{xml_id}_illus_upload_{uid}",
            )
            # Le fichier n'est enregistré qu'au clic (et non à chaque rerun).
            if col_btn.button("Voir/Sauvegarder", key=f"{xml_id}_illus_show_local_{uid}"):
                if uploaded is None:
                    st.warning("Chargez d'abord un fichier.")
                else:
                    illus["url"] = save_image(uploaded)
                    illus["_show"] = True
        else:
            st.info("Choisissez un mode : URL ou Local")

        illus["copyright"] = st.text_input(
            "Droits", illus.get("copyright", ""), key=f"{xml_id}_illus_copyright_{uid}"
        )
        exemple_desc_image()
        illus["caption"] = st.text_input(
            "Légende",
            illus.get("caption", ""),
            key=f"{xml_id}_illus_caption_{uid}",
            help=(
                "Pour préciser des informations sur l'image, en particulier si l'image "
                "ne correspond pas exactement à l'œuvre décrite dans la notice "
                "(une copie, un dessin préparatoire,...)"
            ),
        )

    # --- Aperçu ---
    with col_preview:
        if illus["_show"]:
            if illus.get("url"):
                st.image(illus["url"], caption="Prévisualisation")
            else:
                st.warning("Aucune image à afficher.")


# =============================================================================
# 5. SECTIONS DE LA PAGE
# =============================================================================

def _section_identity():
    """Auteur, type de notice et XML:ID. Arrête la page tant que l'ID n'est pas valide."""
    entry_editor = st.selectbox(
        "Créateur·rice de la notice : *",
        load_list_form("usernames"),
        index=index_username(),
    )
    entry_type = ENTRY_TYPES[st.radio("Type de notice *", list(ENTRY_TYPES), horizontal=True)]

    xml_id = st.text_input(
        "XML:ID *", key=XML_ID_KEY, help="Identifiant unique de la notice"
    )
    # Ordre voulu : vide -> format -> unicité (on n'interroge `exist_notice` qu'en dernier).
    if not xml_id:
        st.warning("Veuillez saisir un XML:ID")
        st.stop()
    if not XML_ID_PATTERN.fullmatch(xml_id):
        st.error("Vous ne pouvez pas utiliser de caractères spéciaux pour l'identifiant "
                 "de la notice (ni accent, ni espace)")
        st.stop()
    if exist_notice(xml_id):
        st.error(f"Une notice avec le XML:ID '{xml_id}' existe déjà. "
                 "Veuillez choisir un autre identifiant.")
        st.stop()
    return entry_editor, entry_type, xml_id


def _get_or_create_notice(xml_id, entry_type):
    """Récupère la notice en cours, ou en crée une vide si l'ID ou le type a changé."""
    current = st.session_state.get("creating_notice")
    if not current or current["id"] != xml_id or current["entry_type"] != entry_type:
        st.session_state.creating_notice = init_empty_notice(xml_id, entry_type)
    return st.session_state.creating_notice


def _section_general(notice, entry_type, xml_id):
    """QID Wikidata + bouton de recherche, puis titre.

    Le titre doit rester APRÈS le bouton : le préremplissage écrit dans
    `st.session_state[f"{xml_id}_title"]`, ce qui n'est permis qu'avant la création du widget.
    """
    st.header("📋 Informations générales")
    col_qid, col_btn = st.columns([4, 1])

    with col_qid:
        notice["QID_wikidata"] = st.text_input(
            "QID Wikidata", notice.get("QID_wikidata", ""), key=f"{xml_id}_qid"
        )

    with col_btn:
        on_cooldown = _wikidata_cooldown_state()["retry_at"] > time.time()
        if on_cooldown:
            _render_wikidata_retry_timer()
        if st.button("Recherche Wikidata") and not on_cooldown:
            _run_wikidata_search(notice, entry_type, xml_id)

    notice["title"] = st.text_input("Titre *", notice.get("title", ""), key=f"{xml_id}_title")


def _section_creators(notice, entry_type, xml_id):
    st.header("👥 Créateur·rice·s")
    creators = notice.setdefault("creator", [])
    _edit_list(
        creators,
        lambda creator, idx: _creator_form(xml_id, creator, idx, entry_type),
        "Supprimer créateur·rice",
        f"{xml_id}_creator",
    )
    if st.button("➕ Ajouter un·e créateur·rice", key=f"{xml_id}_add_creator"):
        creators.append(_new_item(xml_id="", role=""))
        st.rerun()


def _typology_select(notice, entry_type, xml_id):
    list_key, header, label = TYPOLOGIES[entry_type]
    st.header(header)
    options = load_list_form(list_key)
    notice["typology"] = st.selectbox(
        label,
        options,
        index=None,
        accept_new_options=True,
        key=f"{xml_id}_{entry_type}_typology",
    )
    _save_if_new(list_key, notice["typology"], options, "Sauvegarde de la nouvelle typologie")


def _materials_select(notice, xml_id):
    """Matériaux et techniques (œuvres uniquement)."""
    st.header("🎨 Matériaux & Techniques")
    techniques = load_list_form("techniques")
    current = notice.get("materialsAndTechniques")
    # Une valeur déjà choisie mais pas encore dans la liste reste sélectionnable.
    options = [current, *techniques] if current and current not in techniques else techniques
    notice["materialsAndTechniques"] = st.selectbox(
        "Matériaux et techniques",
        options,
        index=options.index(current) if current in options else None,
        accept_new_options=True,
        key=f"{xml_id}_materials_techniques",
    )
    _save_if_new("techniques", notice["materialsAndTechniques"], techniques,
                 "Sauvegarde de la technique")


def _section_typology(notice, entry_type, xml_id):
    if entry_type == "artwork":
        col_typology, col_materials = st.columns(2)
        with col_typology:
            _typology_select(notice, entry_type, xml_id)
        with col_materials:
            _materials_select(notice, xml_id)
    else:
        _typology_select(notice, entry_type, xml_id)


def _year_input(label, date, field, key):
    value = date.get(field)
    date[field] = st.number_input(
        label,
        min_value=-10000,
        max_value=3000,
        value=int(value) if value not in ("", None) else None,
        step=1,
        format="%d",
        key=key,
    )


def _section_dates(notice, xml_id):
    st.header("📅 Date de création")
    date = notice["dateCreated"]
    col_start, col_end, col_text = st.columns([1, 1, 3])
    with col_start:
        _year_input("Année début", date, "startYear", f"{xml_id}_start_year")
    with col_end:
        _year_input("Année fin", date, "endYear", f"{xml_id}_end_year")
    with col_text:
        date["text"] = st.text_input("Texte", date.get("text", ""), key=f"{xml_id}_date_text")


def _place_select(xml_id, label, state_key, link_key, place_ids, saving_msg):
    """Sélecteur de lieu : ajoute un lieu nouveau à la liste et propose son lien Wikidata.

    `state_key` est la clé du widget (préfixée par l'XML:ID) ; `link_key` est le nom court
    passé à `wikidata_link_for_new_id`.
    """
    st.selectbox(label, place_ids, index=None, accept_new_options=True, key=state_key)
    value = st.session_state[state_key]
    _save_if_new("places", value, place_ids, saving_msg)

    source = wikidata_link_for_new_id(xml_id, link_key, value, place_ids)
    if source is not None:
        save_place_wikidata(value, source)
    return value


def _location_place(notice, xml_id):
    """Localisation géographique (bâtiments) : ville, pays, coordonnées."""
    place = notice["location"].setdefault("place", {})
    place_ids = load_list_form("places")
    city_key, country_key = f"{xml_id}_place_city", f"{xml_id}_place_country"
    # Valeur initiale reprise de la notice (première fois seulement).
    st.session_state.setdefault(city_key, place.get("city"))
    st.session_state.setdefault(country_key, place.get("country"))

    col_city, col_country = st.columns(2)
    with col_city:
        place["city"] = _place_select(
            xml_id, "Ville", city_key, "place_city", place_ids, "Sauvegarde de la nouvelle ville")
    with col_country:
        place["country"] = _place_select(
            xml_id, "Pays", country_key, "place_country", place_ids, "Sauvegarde du nouveau pays")

    # Coordonnées en lecture seule : on affiche la valeur sans la réécrire dans la notice,
    # sinon un nombre Wikidata deviendrait une chaîne.
    coordinates = place.setdefault("coordinates", {})
    col_lat, col_lon = st.columns(2)
    for column, field, label in ((col_lat, "latitude", "Latitude"), (col_lon, "longitude", "Longitude")):
        coordinates.setdefault(field, "")
        with column:
            st.text_input(label, value=str(coordinates[field]), disabled=True)


def _location_institution(notice, xml_id):
    """Institution de conservation (musée, église...) d'une œuvre."""
    institution = notice["location"].setdefault("institution", {})

    institutions = load_list_form("institutions")
    institution["name"] = st.selectbox(
        "Nom de l'institution",
        institutions,
        index=None,
        accept_new_options=True,
        key=f"{xml_id}_institution",
    )
    _save_if_new("institutions", institution["name"], institutions,
                 "Sauvegarde de la nouvelle institution")

    institution["place"] = _place_select(
        xml_id, "Ville de l'institution", f"{xml_id}_institution_city", "institution_city",
        load_list_form("places"), "Sauvegarde de la nouvelle ville")

    institution["inventory_number"] = st.text_input(
        "Numéro d'inventaire",
        value=institution.get("inventory_number", ""),
        key=f"{xml_id}_inventory_number",
    )
    institution["url"] = st.text_input(
        "URL de l'oeuvre sur le site de l'institution",
        value=institution.get("url", ""),
        key=f"{xml_id}_institution_url",
    )


def _section_location(notice, entry_type, xml_id):
    st.header("🏛️ Institution de conservation / 📍 Localisation")

    default_index = list(LOCATION_TYPES.values()).index(DEFAULT_LOCATION_TYPE[entry_type])
    label = st.radio(
        "Type de localisation",
        list(LOCATION_TYPES),
        horizontal=True,
        index=default_index,
        key=f"{xml_id}_{entry_type}_location_type",  # le défaut dépend du type de notice
    )
    location_type = LOCATION_TYPES[label]

    if not isinstance(notice.get("location"), dict):
        notice["location"] = {}
    notice["location"]["type"] = location_type

    if location_type == "place":
        _location_place(notice, xml_id)
    elif location_type == "holding_institution":
        _location_institution(notice, xml_id)
    else:  # « Non localisée » ou « Plusieurs localisations » : on ne garde que le type
        notice["location"] = {"type": location_type}


def _section_parent_ensemble(notice, xml_id):
    """Ensemble qui contient l'œuvre ou le bâtiment (optionnel)."""
    st.header("🌿 Ensemble contenant l'œuvre")
    belongs = st.radio(
        "Cette œuvre appartient-elle à un ensemble ?",
        ["Non", "Oui"],
        horizontal=True,
        key=f"{xml_id}_has_ensemble",
    )
    if belongs == "Non":
        notice["contained_by_ensemble"] = {}
        return

    link = notice.setdefault("contained_by_ensemble", {})
    col_type, col_ensemble = st.columns(2)
    with col_type:
        link_types = load_list_form("link_types_contained")
        link["link_type"] = st.selectbox(
            "Type de lien",
            link_types,
            key=f"{xml_id}_contained_by_ensemble_type",
            index=None,
            accept_new_options=True,
        )
        _save_if_new("link_types_contained", link["link_type"], link_types,
                     "Sauvegarde du nouveau type de lien")
    with col_ensemble:
        link["xml_id_work"] = st.selectbox(
            "Ensemble contenant l'œuvre",
            get_all_objects_ids_flat_sorted(["ensemble"]),
            placeholder="XML:ID de l'oeuvre liée",
            index=None,
            key=f"{xml_id}_contained_by_ensemble_xmlid",
        )


def _section_links(notice, entry_type, xml_id):
    """Œuvres liées, et selon le type : œuvres de l'ensemble ou ensemble parent."""
    st.header("🔗 Œuvres liées")
    _work_links_editor(
        xml_id,
        notice.setdefault("related_works", []),
        get_all_objects_ids_flat_sorted(),
        "Œuvre liée", "link_types", "related_work",
        "➕ Ajouter une œuvre liée",
    )

    if entry_type == "ensemble":
        st.header("🌿 Œuvres constituantes de l'ensemble")
        _work_links_editor(
            xml_id,
            notice.setdefault("contains_works", []),
            get_all_objects_ids_flat_sorted(["artwork", "building"]),
            "Œuvre contenue dans l'ensemble", "link_types_contained", "contained_work",
            "➕ Ajouter une œuvre contenue",
        )
    else:
        _section_parent_ensemble(notice, xml_id)


def _section_bibliography(notice, xml_id):
    st.header("Bibliographie")
    references = notice.setdefault("bibliography", [])
    col_count, col_refs = st.columns([1, 4])

    with col_count:
        count = st.radio(
            "Nombre d'ouvrages",
            [0, 1, 2, 3],
            index=min(len(references), 3),
            key=f"{xml_id}_nbr_biblio",
        )

    with col_refs:
        # La liste est ajustée au nombre choisi (ajout ou retrait en fin de liste).
        while len(references) < count:
            references.append(_new_item(zotero_key="", location=""))
        del references[count:]

        zotero_list = load_list_form("zotero_keys")
        for idx, ref in enumerate(references):
            _bibliography_form(xml_id, _ensure_uid(ref), idx, zotero_list)


def _section_illustrations(notice, xml_id):
    st.header("🖼️ Illustrations")
    illustrations = notice.setdefault("illustrations", [])
    _edit_list(
        illustrations,
        lambda illus, idx: _illustration_form(xml_id, illus, idx),
        "Supprimer illustration",
        f"{xml_id}_illus",
    )
    if st.button("➕ Ajouter une illustration", key=f"{xml_id}_add_illus"):
        illustrations.append(
            _new_item(id=len(illustrations), url="", storage="", copyright="", caption="")
        )
        st.rerun()


def _section_texts_and_status(notice, xml_id):
    st.header("💬 Textes")
    notice["description"] = st.text_area(
        "Description", notice.get("description", ""), key=f"description_{xml_id}"
    )
    notice["commentary"] = st.text_area(
        "Commentaire", notice.get("commentary", ""), key=f"commentaire_{xml_id}"
    )

    status_keys = list(STATUS_ENTRY_OPTIONS)
    current = notice.get("status_entry")
    current = int(current) if current not in (None, "") else 0
    notice["status_entry"] = st.selectbox(
        "Statut de la notice",
        options=status_keys,
        format_func=STATUS_ENTRY_OPTIONS.get,
        index=status_keys.index(current) if current in status_keys else 0,
        key=f"{xml_id}_status",
    )


# =============================================================================
# 6. SAUVEGARDE ET POINT D'ENTRÉE
# =============================================================================

def _build_notice_to_save(notice, history_entry=None):
    """Copie de la notice prête à être enregistrée (sans état d'interface).

    - retire `_uid`, `_mode`, `_show`... et le lien Wikidata des créateurs
      (enregistré à part par `_save_new_persons_wikidata`) ;
    - renumérote les illustrations selon leur position ;
    - ajoute `history_entry` à l'historique sans modifier la notice en cours.
    """
    to_save = {**notice}
    to_save["creator"] = [_public(c, exclude={"wikidata"}) for c in notice.get("creator", [])]
    for key in ("related_works", "contains_works", "bibliography"):
        if key in notice:
            to_save[key] = [_public(item) for item in notice[key]]
    to_save["illustrations"] = [
        {**_public(illus), "id": position}
        for position, illus in enumerate(notice.get("illustrations", []))
    ]
    if history_entry:
        to_save["history"] = [*notice.get("history", []), history_entry]
    return to_save


def _save_new_persons_wikidata(creators):
    """Enregistre le lien Wikidata des personnes créées dans cette notice."""
    for creator in creators:
        source = (creator.get("wikidata") or "").strip()
        if source and creator.get("_wikidata_person_id") == creator.get("xml_id"):
            save_person_wikidata(creator["xml_id"], source)


def _save_button(notice, xml_id, entry_editor):
    if not st.button("💾 Créer la notice", type="primary", key=f"{xml_id}_save"):
        return

    if not notice["id"] or not notice["title"] or not notice.get("typology"):
        st.error("XML:ID, Titre et la typologie sont obligatoires.")
        return

    history_entry = {
        "date": datetime.now().isoformat(),
        "type": "created",
        "author": entry_editor,
    }
    to_save = _build_notice_to_save(notice, history_entry)
    _save_new_persons_wikidata(notice["creator"])

    with st.spinner("Enregistrement de la notice et ajout sur github"):
        path = save_notice(to_save)
        git_commit_and_push(f"ajout notice {xml_id} par {entry_editor} {history_entry['date']}")

    # Le rerun efface l'écran : le message de succès et la réinitialisation du champ
    # XML:ID sont donc traités au début de la page suivante (voir `_handle_post_save`).
    st.session_state.pop("creating_notice", None)
    st.session_state["_saved_path"] = path
    st.rerun()


def _handle_post_save():
    """Après une sauvegarde : message de succès et champ XML:ID vidé.

    Sans cela, l'ID resterait saisi et la page afficherait aussitôt « notice déjà existante ».
    Un widget ne peut être modifié qu'avant sa création, d'où l'appel en tout début de page.
    """
    path = st.session_state.pop("_saved_path", None)
    if path:
        st.session_state[XML_ID_KEY] = ""
        st.success(f"✅ Notice ajoutée avec succès sur github !\n\n📁 Fichier créé : `{path}`")
        st.balloons()


def add_notice():
    st.title("➕ Ajouter une notice")
    _handle_post_save()

    entry_editor, entry_type, xml_id = _section_identity()
    notice = _get_or_create_notice(xml_id, entry_type)

    _section_general(notice, entry_type, xml_id)
    _section_creators(notice, entry_type, xml_id)
    _section_typology(notice, entry_type, xml_id)
    _section_dates(notice, xml_id)
    _section_location(notice, entry_type, xml_id)
    _section_links(notice, entry_type, xml_id)
    _section_bibliography(notice, xml_id)
    _section_illustrations(notice, xml_id)
    _section_texts_and_status(notice, xml_id)

    st.divider()
    _save_button(notice, xml_id, entry_editor)

    with st.expander("📄 Voir le JSON complet"):
        st.json(_build_notice_to_save(notice), expanded=False)  # exactement ce qui sera enregistré