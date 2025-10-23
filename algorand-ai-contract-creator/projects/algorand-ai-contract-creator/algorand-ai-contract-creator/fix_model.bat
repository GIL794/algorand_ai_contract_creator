@echo off
echo Fixing Perplexity model names to 'sonar'...

REM Update .env
powershell -Command "(Get-Content .env) -replace 'AI_MODEL=.*', 'AI_MODEL=sonar' | Set-Content .env"

echo.
echo Fixed! Your .env now uses: AI_MODEL=sonar
echo.
echo Restart the app with: streamlit run tools\web_interface.py
pause
