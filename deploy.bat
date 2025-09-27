@echo off
REM MoneyManager Deployment Script for Windows
REM This script automates the deployment process on Windows

setlocal EnableDelayedExpansion

echo 🚀 Starting MoneyManager deployment...
echo.

REM Configuration
set PYTHON_VERSION=3.9
set PROJECT_NAME=moneymanager
set VENV_NAME=venv
set REQUIREMENTS_FILE=requirements.txt

REM Check if Python is installed
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Python is not installed or not in PATH. Please install Python %PYTHON_VERSION% or higher.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set python_version=%%i
echo [INFO] Found Python %python_version%

REM Setup virtual environment
echo [INFO] Setting up virtual environment...

if exist %VENV_NAME% (
    echo [WARNING] Virtual environment already exists. Removing...
    rmdir /s /q %VENV_NAME%
)

python -m venv %VENV_NAME%
call %VENV_NAME%\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip

echo [SUCCESS] Virtual environment created and activated
echo.

REM Install dependencies
echo [INFO] Installing Python dependencies...

if not exist %REQUIREMENTS_FILE% (
    echo [ERROR] Requirements file not found: %REQUIREMENTS_FILE%
    pause
    exit /b 1
)

pip install -r %REQUIREMENTS_FILE%
if !errorlevel! neq 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo [SUCCESS] Dependencies installed successfully
echo.

REM Setup environment file
echo [INFO] Setting up environment configuration...

if not exist .env (
    if exist .env.example (
        copy .env.example .env
        echo [WARNING] Created .env from .env.example. Please update with your settings.

        REM Generate a random secret key
        for /f "delims=" %%i in ('python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"') do set SECRET_KEY=%%i

        REM Update .env file with generated secret key
        powershell -Command "(gc .env) -replace 'SECRET_KEY=your-secret-key-here', 'SECRET_KEY=%SECRET_KEY%' | Out-File -encoding ASCII .env"

        echo [SUCCESS] Generated new SECRET_KEY in .env file
    ) else (
        echo [ERROR] .env.example file not found. Please create .env manually.
        pause
        exit /b 1
    )
) else (
    echo [SUCCESS] Environment file already exists
)
echo.

REM Setup database
echo [INFO] Setting up database...

REM Create logs directory if it doesn't exist
if not exist logs mkdir logs

REM Make migrations
python manage.py makemigrations
if !errorlevel! neq 0 (
    echo [ERROR] Failed to create migrations
    pause
    exit /b 1
)

REM Apply migrations
python manage.py migrate
if !errorlevel! neq 0 (
    echo [ERROR] Failed to apply migrations
    pause
    exit /b 1
)

REM Setup initial data
python manage.py setup_initial_data
if !errorlevel! neq 0 (
    echo [ERROR] Failed to setup initial data
    pause
    exit /b 1
)

echo [SUCCESS] Database setup completed
echo.

REM Collect static files
echo [INFO] Collecting static files...

REM Create static directories
if not exist static mkdir static
if not exist staticfiles mkdir staticfiles
if not exist media mkdir media

REM Collect static files
python manage.py collectstatic --noinput
if !errorlevel! neq 0 (
    echo [ERROR] Failed to collect static files
    pause
    exit /b 1
)

echo [SUCCESS] Static files collected
echo.

REM Create superuser
set /p create_superuser="Create a superuser account? (Y/n): "
if /i "!create_superuser!" neq "n" (
    echo [INFO] Creating superuser account...
    echo Please create an admin account:
    python manage.py createsuperuser
    echo [SUCCESS] Superuser created
    echo.
)

REM Run tests
set /p run_tests="Run tests? (Y/n): "
if /i "!run_tests!" neq "n" (
    echo [INFO] Running tests...
    python manage.py test --verbosity=2
    if !errorlevel! equ 0 (
        echo [SUCCESS] All tests passed
    ) else (
        echo [WARNING] Some tests failed. Check the output above.
    )
    echo.
)

REM Deployment completed
echo.
echo [SUCCESS] 🎉 Deployment completed successfully!
echo.
echo Next steps:
echo 1. Update .env file with your specific settings
echo 2. Review the admin panel at: http://127.0.0.1:8000/admin/
echo 3. Access the application at: http://127.0.0.1:8000/
echo.
echo To start the server manually later, run:
echo   %VENV_NAME%\Scripts\activate.bat
echo   python manage.py runserver
echo.

set /p start_server="Start the development server now? (y/N): "
if /i "!start_server!" equ "y" (
    echo [INFO] Starting development server...
    python manage.py runserver
) else (
    echo.
    echo [INFO] You can start the server later with: python manage.py runserver
    echo [INFO] Don't forget to activate the virtual environment first: %VENV_NAME%\Scripts\activate.bat
)

echo.
echo [SUCCESS] Deployment script completed!
pause