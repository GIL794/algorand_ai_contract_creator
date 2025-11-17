@echo off
echo ====================================
echo Algorand AI Contract Creator Setup
echo ====================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

echo Upgrading pip...
python -m pip install --upgrade pip
echo.

echo Installing package in editable mode...
pip install -e .
echo.

echo Installing dependencies...
pip install -r requirements.txt
echo.

echo ====================================
echo Installation complete!
echo ====================================
echo.
echo Next steps:
echo 1. Copy .env.example to .env
echo 2. Add your Perplexity API key to .env
echo 3. Run: scripts\run.bat
echo    OR: python main.py
echo.
pause
