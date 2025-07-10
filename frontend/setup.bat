@echo off
echo Setting up AI Purchase Order System Frontend...
echo.

echo Creating virtual environment...
python -m venv frontend_env

echo Activating virtual environment...
call frontend_env\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Setup complete! To run the frontend:
echo 1. Navigate to the frontend directory: cd frontend
echo 2. Activate environment: frontend_env\Scripts\activate.bat
echo 3. Run the app: streamlit run app.py
echo.
echo The dashboard will open in your browser at http://localhost:8501
pause
