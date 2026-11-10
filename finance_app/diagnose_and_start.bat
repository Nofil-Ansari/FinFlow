@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo        FinanceFlow Environment & Startup Check
echo ========================================================
echo.

cd /d D:\Projects\Project\finance_app
echo [1/4] Current Directory: %CD%
echo.

echo [2/4] Checking Python installation...
where python
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python was not found in PATH!
    echo Please install Python 3.10+ or add it to your Windows Environment Variables.
    goto :end
)
python --version
echo.

echo [3/4] Checking virtual environments...
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Found venv in finance_app\venv. Activating...
    call venv\Scripts\activate.bat
) else if exist "..\venv\Scripts\activate.bat" (
    echo [INFO] Found venv in Project\venv. Activating...
    call ..\venv\Scripts\activate.bat
) else (
    echo [INFO] No local venv folder found; using system Python.
)
echo.

echo [4/4] Testing application imports and startup...
python -c "import flask, flask_sqlalchemy, flask_socketio; print('Core dependencies OK!')"
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Missing required Python packages.
    echo Trying: pip install -r requirements.txt
    pip install -r requirements.txt
)

echo.
echo ========================================================
echo Launching FinanceFlow (run.py)...
echo ========================================================
python run.py

:end
echo.
echo Application stopped or failed to launch.
pause

