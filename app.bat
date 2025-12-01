@echo off
setlocal

REM --- 1. Vérifier si Python est installé ---
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python n'est pas installe. Installer Python et relancer.
    pause
    exit /b
)

REM --- 2. Créer un venv s'il n'existe pas ---
if not exist ".venv" (
    echo Creation de l'environnement virtuel...
    python -m venv .venv
)

REM --- 3. Activer le venv ---
call .venv\Scripts\activate

REM --- 4. Installer Streamlit s'il manque ---
python -c "import streamlit" 2>nul
if %ERRORLEVEL% neq 0 (
    echo Installation de Streamlit...
    pip install --upgrade pip
    pip install streamlit
)

REM --- 5. Lancer l'application ---
streamlit run app.py

pause
