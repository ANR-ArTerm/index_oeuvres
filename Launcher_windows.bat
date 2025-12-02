@echo off
setlocal ENABLEDELAYEDEXPANSION

echo === Verification de Python ===

:: Teste la présence de python.exe en récupérant sa sortie ===
for /f "delims=" %%i in ('where python 2^>nul') do set PYTHON_FOUND=%%i

if not defined PYTHON_FOUND (
    echo.
    echo ! Python n'est pas installe ou pas dans le PATH.
    echo Télécharge-le ici : https://www.python.org/downloads/windows/
    echo.
    pause
    exit /b 1
)

echo Python detecte : %PYTHON_FOUND%
echo.

echo === Creation / Activation de l'environnement virtuel ===
echo.

if not exist ".venv" (
    echo --> Creation du venv...
    python -m venv .venv
    echo.
)

call .venv\Scripts\activate
echo --> Environnement virtuel active
echo.

echo === Installation de Streamlit si necessaire ===
python -c "import streamlit" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo --> Installation de Streamlit dans l'environnement virtuel...
    pip install --upgrade pip
    pip install -r requirements.txt
)
echo.

echo === Lancement de l'application ===
echo.
echo Pour quitter l'application, fermer cette fenetre du terminal ou appuyer sur controle + C simultanement puis O
streamlit run app.py

pause