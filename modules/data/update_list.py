from modules.data.load import load_all_entries, save_list_to_list_form

def update_list_institutions():
    ENTRIES = load_all_entries("peinture")
    institutions = set()

    for data, _ in ENTRIES:
        name = (
            data.get("location", {})
                .get("institution", {})
                .get("name")
        )

        if name:
            institutions.add(name.strip())

    save_list_to_list_form("institutions", list(institutions))