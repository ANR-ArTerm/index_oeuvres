import csv

from modules.data_loader import get_wikidata_csv_path, 

def wikidata_to_xml_ids_or_qid(qid_list, key):
    """
    Mapping wikidata_qid -> xml_id
    Si le QID n'est pas trouvé, il est conservé tel quel.
    """
    if isinstance(qid_list, str):
        qid_list = [qid_list]

    csv_path = get_wikidata_csv_path(key)

    mapping = {}

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            mapping[row.get("wikidata_qid")] = row.get("xml_id")

    return [mapping.get(qid, qid) for qid in qid_list]


def wikidata_to_xml_ids_or_none(qid_list, key):
    """
    À utiliser pour typologies / techniques.
    - évite les doublons
    - ignore les labels vides
    - retourne un seul label (stable) ou None
    """
    if isinstance(qid_list, str):
        qid_list = [qid_list]

    csv_path = get_wikidata_csv_path(key)

    labels_set = set()

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            qid = row.get("wikidata_qid")
            label = row.get("label_fr")

            if qid in qid_list and label:
                labels_set.add(label.strip())

    if not labels_set:
        return None

    return sorted(labels_set)[0]


""" usage :

wikidata_to_xml_ids_or_qid(
    ["Q42", "Q123"],
    key="people"
)

wikidata_to_xml_ids_or_none(
    ["Q987"],
    key="techniques"
)

"""