# index_oeuvres

Application streamlit pour ajouter et modifier les notices d'oeuvres du projet Arterm

## Organisation

- `app.py` : point d'entrée Streamlit et orchestration de l'interface.
- `modules/data/load.py` : lecture et écriture des notices, images et listes de formulaire.
- `modules/data/index_xml_oeuvres.py` : reconstruit `../corpus/IndexOeuvres.xml` depuis les notices JSON.
- `modules/data/index_xml_to_json.py` : synchronise les index TEI de personnes et de lieux vers les listes JSON.
- `modules/data/verify_data.py` : contrôle les notices et propose des corrections de données.
- `data/entry_*` : notices JSON classées par type (`artwork`, `building`, `ensemble`).
- `corbeille/` : archive locale des notices supprimées depuis l'application.

Les chemins de données sont calculés depuis le dossier de l'application afin que le lancement depuis un raccourci, un terminal ou un IDE donne le même résultat.

La reconstruction de l'index des œuvres est stricte : une notice JSON illisible, incomplète ou dupliquée bloque l'écriture et laisse l'index précédent intact.

## Installation et lancement

### Sur Windows

1. Double-cliquez sur le script `Launcher_windows.bat`.
2. Lorsque le programme le demande, entrez votre prénom.

### Sur Linux / macOS

1. Ouvrez un terminal à l'emplacement du dossier `index_oeuvres`.
2. Rendez le script exécutable avec la commande suivante :
   ```bash
   chmod +x Launcher_macOS.sh
   ````

3. Lancer le script bash
   ```bash
   ./Launcher_macOS.sh
    ````

4. Lorsque le programme le demande, entrez votre prénom.
