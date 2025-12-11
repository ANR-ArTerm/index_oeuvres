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