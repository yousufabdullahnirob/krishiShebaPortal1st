@echo off
echo Starting Agroby Application...

cd /d "%~dp0\backend"
echo Starting Backend Server...
start "Agroby Backend" cmd /k "python manage.py runserver"

echo Waiting for backend to initialize...
timeout /t 5 /nobreak >nul

cd /d "%~dp0\frontend"
echo Starting Frontend Client...
start "Agroby Frontend" cmd /k "npm start"

echo Application launched successfully!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
pause
