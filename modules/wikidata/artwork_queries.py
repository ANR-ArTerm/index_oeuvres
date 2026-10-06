"""Requêtes Wikidata destinées aux notices d'œuvres."""

import html
import re
import unicodedata
from urllib.parse import parse_qsl, quote, unquote, urlencode, urlparse, urlunparse

import requests

from modules.wikidata.data_treatment import extract_wikidata_id


def _extract_year(date_value: str) -> int | None:
    match = re.match(r"([+-]?\d+)-\d{2}-\d{2}", date_value)
    return int(match.group(1)) if match else None


def _commons_filename(image_url: str) -> str | None:
    parsed = urlparse(image_url)
    path = unquote(parsed.path)

    marker = "/wiki/Special:FilePath/"
    if parsed.netloc.endswith("commons.wikimedia.org") and marker in path:
        return path.split(marker, 1)[1]

    if parsed.netloc.endswith("commons.wikimedia.org") and "/wiki/File:" in path:
        return path.split("/wiki/File:", 1)[1]

    if parsed.netloc.endswith("upload.wikimedia.org") and "/wikipedia/commons/" in path:
        parts = path.split("/")
        if "thumb" in parts:
            return parts[-2]
        return parts[-1]

    return None


def _plain_text(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", value)).strip()


def _commons_image_metadata(image_urls: list[str]) -> list[dict[str, str]]:
    filenames = list(dict.fromkeys(
        filename
        for image_url in image_urls
        if (filename := _commons_filename(image_url))
    ))
    if not filenames:
        return []

    try:
        response = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            params={
                "action": "query",
                "format": "json",
                "prop": "imageinfo",
                "iiprop": "url|extmetadata|user",
                "titles": "|".join(f"File:{filename}" for filename in filenames[:50]),
            },
            headers={"User-Agent": "SIFON-artwork-catalog/1.0"},
            timeout=15,
        )
        response.raise_for_status()
        pages = response.json()["query"]["pages"].values()
    except (requests.RequestException, ValueError, KeyError):
        return []

    images = []
    for page in pages:
        image_infos = page.get("imageinfo", [])
        if not image_infos:
            continue

        info = image_infos[0]
        direct_url = info.get("url", "")
        if not direct_url.startswith("https://upload.wikimedia.org/wikipedia/commons/"):
            continue

        file_page_url = info.get("descriptionurl")
        if file_page_url:
            page_parts = urlparse(file_page_url)
            query = dict(parse_qsl(page_parts.query))
            query.setdefault("lang", "fr")
            file_page_url = urlunparse(page_parts._replace(query=urlencode(query)))
        else:
            title = page.get("title", "")
            file_page_url = f"https://commons.wikimedia.org/wiki/{quote(title.replace(' ', '_'))}?lang=fr"

        metadata = info.get("extmetadata", {})
        license_name = _plain_text(metadata.get("LicenseShortName", {}).get("value", ""))
        uploader = info.get("user", "").strip()
        rights_parts = ["Wikimedia Commons"]
        if license_name:
            rights_parts.append(license_name)
        if uploader:
            rights_parts.append(uploader)

        images.append({
            "url": direct_url,
            "copyright": f"{', '.join(rights_parts)} ({file_page_url})",
        })

    return images


def match_existing_label(label: str, values: list[str]) -> str | None:
    """Associe un libellé Wikidata à une valeur locale sans correspondance floue."""
    normalized_label = "".join(
        character
        for character in unicodedata.normalize("NFKD", label).casefold()
        if character.isalnum()
    )
    if not normalized_label:
        return None

    matches = [
        value
        for value in values
        if "".join(
            character
            for character in unicodedata.normalize("NFKD", value).casefold()
            if character.isalnum()
        ) == normalized_label
    ]
    return matches[0] if len(matches) == 1 else None


def _get_entity(qid: str) -> dict:
    response = requests.get(
        f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json",
        headers={"User-Agent": "SIFON-artwork-catalog/1.0"},
        timeout=20,
    )
    response.raise_for_status()
    entity = response.json().get("entities", {}).get(qid)
    if not entity or entity.get("missing"):
        raise ValueError(f"Aucune œuvre trouvée pour {qid}")
    return entity


def _entity_value(claim: dict):
    return claim.get("mainsnak", {}).get("datavalue", {}).get("value")


def _get_entity_labels(qids: list[str]) -> dict[str, str]:
    if not qids:
        return {}

    response = requests.get(
        "https://www.wikidata.org/w/api.php",
        params={
            "action": "wbgetentities",
            "format": "json",
            "ids": "|".join(qids),
            "props": "labels",
            "languages": "fr|it|en",
        },
        headers={"User-Agent": "SIFON-artwork-catalog/1.0"},
        timeout=20,
    )
    response.raise_for_status()
    entities = response.json().get("entities", {})

    labels = {}
    for qid, entity in entities.items():
        entity_labels = entity.get("labels", {})
        label = next(
            (entity_labels[language]["value"] for language in ("fr", "it", "en") if language in entity_labels),
            "",
        )
        if label:
            labels[qid] = label
    return labels


def get_artwork_data(url: str) -> dict:
    """Récupère les informations descriptives disponibles pour une œuvre."""
    qid = extract_wikidata_id(url)
    if not qid:
        raise ValueError("QID Wikidata invalide")

    entity = _get_entity(qid)
    claims = entity.get("claims", {})
    labels = entity.get("labels", {})
    titles = entity.get("descriptions", {})

    title_claims = [
        _entity_value(claim)
        for claim in claims.get("P1476", [])
        if isinstance(_entity_value(claim), dict)
    ]
    title = next(
        (
            claim.get("text", "").strip()
            for language in ("fr", "it", "en")
            for claim in title_claims
            if claim.get("language") == language and claim.get("text", "").strip()
        ),
        "",
    )
    if not title:
        title = next(
            (labels[language]["value"] for language in ("fr", "it", "en") if language in labels),
            "",
        )

    inception_claims = claims.get("P571", [])
    inception_value = _entity_value(inception_claims[0]) if inception_claims else ""
    year = _extract_year(inception_value.get("time", "")) if isinstance(inception_value, dict) else None

    creator_claims = [
        claim
        for claim in claims.get("P170", [])
        if claim.get("rank") != "deprecated"
    ]
    creator_claims.sort(key=lambda claim: claim.get("rank") != "preferred")
    creator_qids = list(dict.fromkeys(
        value["id"]
        for claim in creator_claims
        if isinstance((value := _entity_value(claim)), dict) and value.get("id")
    ))

    institution_qids = list(dict.fromkeys(
        value["id"]
        for claim in claims.get("P276", [])
        if isinstance((value := _entity_value(claim)), dict) and value.get("id")
    ))
    entity_labels = _get_entity_labels(list(dict.fromkeys(creator_qids + institution_qids)))

    image_urls = []
    for claim in claims.get("P18", []):
        filename = _entity_value(claim)
        if isinstance(filename, str) and filename:
            image_url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{quote(filename)}"
            if image_url not in image_urls:
                image_urls.append(image_url)

    images = _commons_image_metadata(image_urls)

    return {
        "title": title,
        "year": year,
        "creator_qids": creator_qids,
        "creator_labels": [entity_labels.get(creator_qid, creator_qid) for creator_qid in creator_qids],
        "institutions": list(dict.fromkeys(
            entity_labels[institution_qid]
            for institution_qid in institution_qids
            if institution_qid in entity_labels
        )),
        "images": images,
    }