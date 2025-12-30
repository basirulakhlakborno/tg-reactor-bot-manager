@echo off
echo ========================================
echo Telegram Bot Manager - Admin Panel
echo ========================================
echo.
echo Checking Flask installation...
python -c "import flask" 2>nul
if errorlevel 1 (
    echo Flask not found. Installing Flask first...
    python -m pip install flask==3.0.0
    if errorlevel 1 (
        echo Error installing Flask. Please install manually: pip install flask
        pause
        exit /b 1
    )
    echo Flask installed successfully!
    echo.
)
echo.
echo Starting server...
echo.
echo If this is your first run, you will be redirected to the setup page.
echo Admin Panel will be available at:
echo http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.
python app.py
pause
