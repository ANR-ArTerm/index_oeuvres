@echo off
setlocal ENABLEDELAYEDEXPANSION

echo === Verification du USERNAME ===
echo.

set "VALID_USERS=Pierre Julia Anna Emma Carla"
set "CURRENT_USER="

:: Lecture du USERNAME existant (première occurrence seulement)
if exist ".env" (
    for /f "tokens=1,* delims==" %%a in ('findstr /b /i "USERNAME=" .env') do (
        if not defined CURRENT_USER set "CURRENT_USER=%%b"
    )
)

:: Si USERNAME existe déjà → on ne demande rien
if defined CURRENT_USER (
    echo USERNAME deja defini : !CURRENT_USER!
    set "USERNAME=!CURRENT_USER!"
    goto END_USERNAME
)

:: Sinon → demander le nom
:ASK_USERNAME
color 0A
set /p USERNAME="Entrez votre nom d'utilisateur (Pierre, Julia, Anna, Emma, Carla) : "
color 07

set FOUND=0
for %%u in (%VALID_USERS%) do (
    if /I "%%u"=="!USERNAME!" set FOUND=1
)

if !FOUND!==0 (
    echo Utilisateur invalide.
    goto ASK_USERNAME
)

:: Ecriture dans le .env
echo USERNAME=!USERNAME!>>.env
echo USERNAME ajoute au fichier .env

:END_USERNAME
echo Utilisateur actif : !USERNAME!
echo.

echo.
echo.

echo === Verification de Python ===

:: Verifie si python est dans le PATH
for /f "delims=" %%i in ('where python 2^>nul') do (
    set "PYTHON_FOUND=%%i"
    goto PYTHON_OK
)

echo.
echo Python n'est pas installe ou n'est pas dans le PATH.
echo Telecharge-le ici : https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe
echo.
pause
exit /b 1

:PYTHON_OK
echo Python detecte : %PYTHON_FOUND%
echo.

echo === Creation / Activation de l'environnement virtuel ===
echo.

if not exist ".venv" (
    echo Creation du venv...
    python -m venv .venv
    echo.
)

if not exist ".venv\Scripts\activate.bat" (
    echo ERREUR : Le venv n'a pas ete cree correctement.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
echo Environnement virtuel active
echo.

echo === Installation des dependances ===
echo.

:: Test Streamlit

echo Installation des dependances et mise a jour...
pip install --upgrade pip
pip install --upgrade -r requirements.txt

echo.
echo.

echo === Lancement de l'application ===
echo.
echo L'application va s'ouvrir dans le navigateur par defaut
echo.
echo Pour quitter : Ctrl + C puis O ou fermer ce terminal
echo.

streamlit run app.py

echo.
pause