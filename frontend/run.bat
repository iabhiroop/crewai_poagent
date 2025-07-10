@echo off
echo Starting AI Purchase Order System Dashboard...
echo.

if not exist "frontend_env" (
    echo Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

echo Activating virtual environment...
call frontend_env\Scripts\activate.bat

echo Starting Streamlit dashboard...
streamlit run app.py

pause
