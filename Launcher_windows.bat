@echo off
setlocal ENABLEDELAYEDEXPANSION

echo === Verification de Python ===

:: Vérifie si python est dans le PATH
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
python -c "import importlib.util; exit(0) if importlib.util.find_spec('streamlit') else exit(1)" >nul 2>&1

if %ERRORLEVEL% neq 0 (
    echo Installation des dependances...
    pip install --upgrade pip
    pip install -r requirements.txt
)
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